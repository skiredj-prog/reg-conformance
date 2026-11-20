"""Independent RC-01/I8 consistency oracle for one explicit ordered projection.

No producer, receipt-verifier or semantic-replay imports. This model proves only
arithmetic/state consistency of supplied records, never authenticity/completeness.
"""
import argparse
import json
import os
from pathlib import Path
import re
import stat

PROFILE = "w4-rc01-i8-projection/0.1"
FIELDS = {"profile", "operation_id", "resource_id", "amount_minor", "baseline",
          "initial_view", "initial_settlement", "records"}
LEGAL = {
    "INIT": {"RESERVED"},
    "RESERVED": {"DISPATCHING"},
    "DISPATCHING": {"UNKNOWN", "REPAIR", "CONFIRMED", "FAILED"},
    "UNKNOWN": {"REPAIR", "REVIEW_REQUIRED", "RECONCILED_CONFIRMED", "RECONCILED_NOT_EXECUTED"},
    "REVIEW_REQUIRED": {"UNKNOWN"},
    "REPAIR": {"RECONCILED_CONFIRMED", "RECONCILED_NOT_EXECUTED"},
    "CONFIRMED": set(), "FAILED": set(),
    "RECONCILED_CONFIRMED": set(), "RECONCILED_NOT_EXECUTED": set(),
}
POSITIVE = {"CONFIRMED", "RECONCILED_CONFIRMED"}
NEGATIVE = {"FAILED", "RECONCILED_NOT_EXECUTED"}


class Issue(ValueError):
    def __init__(self, outcome, code):
        self.outcome, self.code = outcome, code
        super().__init__(code)


def reject(code):
    raise Issue("REFUTED", code)


def incomplete(code):
    raise Issue("INDETERMINATE", code)


def need(value, fields):
    if not isinstance(value, dict) or not set(fields) <= value.keys():
        incomplete("OBSERVATION_FIELDS_MISSING")


def _result(outcome, code, **extra):
    return {"outcome": outcome, "code": code, "assurance_scope": PROFILE,
            "input_authenticity": "NOT_EVALUATED", "capture_completeness": "NOT_ESTABLISHED",
            "grant_and_witness": "NOT_EVALUATED",
            "integration_lock": "HOLD", "production": "HOLD", **extra}


def replay_projection(projection):
    try:
        return _replay(projection)
    except Issue as exc:
        return _result(exc.outcome, exc.code)


def _replay(p):
    if not isinstance(p, dict) or p.get("profile") != PROFILE or set(p) != FIELDS:
        incomplete("PROJECTION_PROFILE_OR_FIELDS_UNAVAILABLE")
    if p["initial_view"] != "INIT" or p["initial_settlement"] != "NONE":
        incomplete("INITIAL_BOUNDARY_UNSUPPORTED")
    if any(not isinstance(p[k], str) or not p[k].strip() for k in ("operation_id", "resource_id")):
        reject("SUBJECT_INVALID")
    amount = p["amount_minor"]
    if type(amount) is not int or amount <= 0:
        reject("AMOUNT_INVALID")
    base = p["baseline"]
    if not isinstance(base, dict) or set(base) != {"capacity", "reserved", "committed"}:
        incomplete("BASELINE_UNAVAILABLE")
    if any(type(v) is not int or v < 0 for v in base.values()):
        reject("BASELINE_INVALID")
    capacity, reserved, committed = base["capacity"], base["reserved"], base["committed"]
    if reserved + committed > capacity:
        reject("BASELINE_OVER_CAPACITY")
    records = p["records"]
    if not isinstance(records, list) or len(records) > 10000:
        incomplete("RECORD_SCOPE_UNSUPPORTED")
    view, settlement, fact, fact_ref = "INIT", "NONE", None, None
    released = 0
    counts = {"reserve_applied": 0, "commit_applied": 0, "release_applied": 0,
              "failed_settlement_observed": 0, "replays": 0}
    seen = set()
    for expected_sequence, row in enumerate(records, 1):
        need(row, ("sequence", "kind", "operation_id"))
        sequence = row["sequence"]
        if type(sequence) is not int or sequence < 1:
            reject("SEQUENCE_INVALID")
        if sequence in seen:
            reject("SEQUENCE_REUSED")
        seen.add(sequence)
        if sequence != expected_sequence:
            incomplete("SEQUENCE_INCOMPLETE_OR_UNORDERED")
        if row["operation_id"] != p["operation_id"]:
            reject("OPERATION_BINDING_MISMATCH")
        kind = row["kind"]
        common = {"sequence", "kind", "operation_id"}
        if kind == "STATE":
            allowed = common | {"from", "to"}
        elif kind == "I8":
            allowed = common | {"resource_id", "amount_minor", "action"}
        elif kind == "PROVIDER":
            allowed = common | {"resource_id", "amount_minor", "effect_status",
                                "receipt_sha256", "finality"}
        else:
            incomplete("OBSERVATION_KIND_UNSUPPORTED")
        if not set(row) <= allowed:
            incomplete("OBSERVATION_EXTENSION_UNSUPPORTED")
        if kind in ("I8", "PROVIDER"):
            need(row, ("resource_id", "amount_minor"))
            if row["resource_id"] != p["resource_id"] or type(row["amount_minor"]) is not int or row["amount_minor"] != amount:
                reject("RESOURCE_OR_AMOUNT_BINDING_MISMATCH")
        if kind == "PROVIDER":
            need(row, ("effect_status",))
            status = row["effect_status"]
            if status == "UNKNOWN":
                # A later absent reply cannot erase already observed final evidence.
                continue
            if status not in ("EXECUTED", "NOT_EXECUTED_FINAL"):
                incomplete("PROVIDER_OUTCOME_UNSUPPORTED")
            need(row, ("receipt_sha256", "finality"))
            if not isinstance(row["receipt_sha256"], str) or not re.fullmatch("[0-9a-f]{64}", row["receipt_sha256"]):
                incomplete("PROVIDER_EVIDENCE_REFERENCE_UNAVAILABLE")
            if row["finality"] != "PROVIDER_LEDGER_TERMINAL":
                incomplete("PROVIDER_FINALITY_NOT_ESTABLISHED")
            if fact is not None and status != fact:
                reject("PROVIDER_OUTCOME_CONTRADICTION")
            if fact_ref is not None and row["receipt_sha256"] != fact_ref:
                incomplete("MULTIPLE_RECEIPTS_REQUIRE_ANALYSIS")
            fact, fact_ref = status, row["receipt_sha256"]
        elif kind == "I8":
            need(row, ("action",))
            action = row["action"]
            if action == "RESERVE_APPLIED":
                if settlement != "NONE":
                    reject("DUPLICATE_RESERVATION")
                reserved += amount
                settlement = "HELD"; counts["reserve_applied"] += 1
            elif action == "SETTLE_FAILED":
                if settlement != "HELD":
                    reject("FAILED_SETTLEMENT_WITHOUT_HELD_RESERVATION")
                counts["failed_settlement_observed"] += 1
            elif action == "COMMIT_APPLIED":
                if settlement == "COMMITTED":
                    reject("DOUBLE_SETTLEMENT")
                if settlement != "HELD":
                    reject("COMMIT_WITHOUT_HELD_RESERVATION")
                if fact != "EXECUTED":
                    reject("COMMIT_WITHOUT_POSITIVE_PROVIDER_FACT")
                reserved -= amount; committed += amount
                settlement = "COMMITTED"; counts["commit_applied"] += 1
            elif action == "RELEASE_APPLIED":
                if settlement != "HELD":
                    reject("RELEASE_WITHOUT_HELD_RESERVATION")
                if fact != "NOT_EXECUTED_FINAL":
                    reject("RELEASE_WITHOUT_NEGATIVE_FINAL")
                reserved -= amount; released += amount
                settlement = "RELEASED"; counts["release_applied"] += 1
            elif action in ("COMMIT_REPLAY", "RELEASE_REPLAY", "RESERVE_REPLAY"):
                required = {"COMMIT_REPLAY": "COMMITTED", "RELEASE_REPLAY": "RELEASED", "RESERVE_REPLAY": "HELD"}[action]
                if settlement != required:
                    reject("REPLAY_STATE_MISMATCH")
                counts["replays"] += 1
            else:
                incomplete("LEDGER_ACTION_UNSUPPORTED")
            if min(reserved, committed) < 0 or reserved + committed > capacity:
                reject("I8_CAPACITY_OR_CONSERVATION_VIOLATION")
        elif kind == "STATE":
            need(row, ("from", "to"))
            before, after = row["from"], row["to"]
            if not isinstance(before, str) or not isinstance(after, str):
                reject("STATE_FIELDS_INVALID")
            if before != view:
                reject("STATE_PREDECESSOR_MISMATCH")
            if after not in LEGAL:
                incomplete("STATE_UNSUPPORTED")
            if before != after and after not in LEGAL[before]:
                reject("STATE_TRANSITION_INVALID")
            if after in {"RESERVED", "DISPATCHING", "UNKNOWN", "REVIEW_REQUIRED"} and settlement != "HELD":
                reject("UNRESOLVED_VIEW_WITHOUT_HELD_BUDGET")
            if after == "REPAIR":
                if fact is None:
                    reject("REPAIR_WITHOUT_PROVIDER_FACT")
                if settlement not in {"HELD", "COMMITTED", "RELEASED"}:
                    reject("REPAIR_WITHOUT_ACCOUNTING_RECORD")
                # COMMITTED/RELEASED may still await a witness acknowledgement;
                # this oracle deliberately does not verify that witness.
            if after in POSITIVE and (fact != "EXECUTED" or settlement != "COMMITTED"):
                reject("POSITIVE_TERMINAL_WITHOUT_MATCHING_SETTLEMENT")
            if after in NEGATIVE and (fact != "NOT_EXECUTED_FINAL" or settlement != "RELEASED"):
                reject("NEGATIVE_TERMINAL_WITHOUT_MATCHING_RELEASE")
            view = after
        else:
            incomplete("OBSERVATION_KIND_UNSUPPORTED")
    return _result("VERIFIED", "PROJECTED_RC01_I8_CONSISTENT",
                   final_view=view, settlement=settlement, observed_provider_outcome=fact,
                   review_required=view == "REVIEW_REQUIRED",
                   terminal=view in POSITIVE | NEGATIVE,
                   balances={"capacity": capacity, "reserved": reserved, "committed": committed,
                             "released_minor": released, "available": capacity-reserved-committed},
                   counters=counts,
                   limits="Only the supplied ordered single-operation projection; not native execution, cryptographic evidence or external-effect completeness")


def _identical(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_identical(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(_identical(x, y) for x, y in zip(a, b))
    return a == b


def compare_projection(verifier_report, projection):
    oracle = replay_projection(projection)
    if oracle["outcome"] != "VERIFIED":
        return oracle
    if (not isinstance(verifier_report, dict) or verifier_report.get("outcome") != "VERIFIED"
            or verifier_report.get("assurance_scope") != PROFILE):
        return _result("INDETERMINATE", "VERIFIER_PROJECTION_NOT_PROVIDED")
    for field in ("final_view", "settlement", "observed_provider_outcome", "review_required",
                  "terminal", "balances", "counters"):
        if field not in verifier_report:
            return _result("INDETERMINATE", "VERIFIER_PROJECTION_FIELD_MISSING", field=field)
        if not _identical(verifier_report[field], oracle[field]):
            return _result("REFUTED", "DIFFERENTIAL_PROJECTION_MISMATCH", field=field)
    return _result("VERIFIED", "PROJECTED_DIFFERENTIAL_AGREEMENT",
                   limits="Agreement of supplied projection reports only; independence and input authenticity not established")


def read_projection(path):
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    with os.fdopen(os.open(path, flags), "rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise ValueError("Regular projection file required")
        raw = source.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Projection size bound")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def constant(value):
        raise ValueError("Non-JSON numeric constant")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except RecursionError as exc:
        raise ValueError("JSON nesting limit") from exc


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("projection", type=Path)
    p.add_argument("--verifier-report", type=Path)
    args = p.parse_args()
    try:
        projection = read_projection(args.projection)
        report = compare_projection(read_projection(args.verifier_report), projection) if args.verifier_report else replay_projection(projection)
    except (OSError, ValueError) as exc:
        report = _result("INDETERMINATE", "PROJECTION_INPUT_INVALID", detail=str(exc))
    print(json.dumps(report, indent=2))
    return {"VERIFIED": 0, "REFUTED": 1}.get(report["outcome"], 2)


if __name__ == "__main__":
    raise SystemExit(main())
