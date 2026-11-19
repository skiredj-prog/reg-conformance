"""Port over the bundled reference kernel.

Reuses the kernel operations of runner.NativeKernelAdapter unchanged, so the
neutral scenarios exercise exactly the code the legacy native mode exercises.
Evidence level stays 1 (semantic mapping): this is not the TENIR-Gov runtime.
"""
from __future__ import annotations

import copy
import uuid
from pathlib import Path

import runner as R
from .. import port as P

_ROOT = Path(__file__).resolve().parents[2]
_INPUTS = {                       # intent -> (credential, P, V, K)
    P.ADMISSIBLE:   ("valid", 0.2, 0.2, 0.90),
    P.INADMISSIBLE: ("valid", 0.95, 0.90, 0.10),
    P.NO_STANDING:  ("none", 0.3, 0.3, 0.85),
    P.DENIED:       ("none", 0.3, 0.3, 0.85),
    # A blank token: not a credential in any format, and one step past the
    # kernel's test for an empty one. Structure as ADMISSIBLE.
    P.MALFORMED_CREDENTIAL: ("   ", 0.2, 0.2, 0.90),
}
_CODES = [("STANDING_REVOKED", P.R_STANDING_REVOKED), ("STATE_DRIFT", P.R_STATE_DRIFT),
          ("EXPIRED", P.R_EXPIRED), ("BINDING_VIOLATION", P.R_BINDING),
          ("INVALID_DISPOSITION", P.R_INVALID_DISPOSITION), ("NONCE_REPLAY", P.R_REPLAY)]


def _refused(exc, grant=None):
    text = str(exc)
    for needle, code in _CODES:
        if needle in text:
            return P.Refused(code, (grant or {}).get("commit_disposition"), text)
    return exc


class ReferencePort(P.RuntimePort):
    name = "bundled-reference-kernel"
    interface_mode = "native"            # invocation style, not a certification claim
    evidence_level = 1
    capabilities = frozenset({P.EVALUATE, P.COMMIT, P.REVOKE, P.STATE_DRIFT, P.STALE_GRANT,
                              P.NONCE, P.RECEIPTS, P.MANIFEST, P.TENIR_SCORE, P.DEGRADE})
    # The three measurements the kernel reads. UNKNOWN is a value that is not
    # a number (NaN): it arrives and says nothing of the state. MISSING is no
    # value at all (None). The kernel takes no age, no second measurement and
    # no confidence: STALE, CONTRADICTORY and CONFIDENCE are not declared.
    _MEASUREMENTS = ("pressure", "velocity", "capacity")
    degradations = {P.E_UNKNOWN: _MEASUREMENTS, P.E_MISSING: _MEASUREMENTS}
    # Not declared: OUT_OF_SCOPE and INVARIANT_VIOLATED. The kernel has no way
    # to give a principal a scope or to declare a hard invariant. COMBINE is
    # not declared either: its two refusals are both HARD_VETO, so no pair of
    # conditions conflicts.
    # No bound and no clock. The kernel revokes at once, and its own register
    # says the latency is "not declared or measured": the port does not
    # declare one in its place. It has no time-limited credential, no request
    # timestamp and no signing key for credentials. Its only HOLD is the one
    # for insufficient evidence (an unmeasured axis, decision 5, or a score
    # that cannot be computed); neither path has a declared bound.
    intents = frozenset({P.ADMISSIBLE, P.INADMISSIBLE, P.NO_STANDING, P.DENIED,
                         P.MALFORMED_CREDENTIAL})
    not_applicable = {"C4": "No transport layer in in-process kernel."}
    declared_gaps = dict(R.EXTENDED_GAP_NOTES)

    def __init__(self, policy_file=None):
        self._policy = str(policy_file or _ROOT / "kernel" / "tenir_policies.yaml")
        self.reset()

    def reset(self):
        self._k = R.NativeKernelAdapter(self._policy)

    def evaluate(self, intent, *, principal, action_type, nonce=None):
        cred, Pv, V, K = _INPUTS[intent]
        try:
            g = self._k._evaluate(principal, cred, action_type, Pv, V, K, nonce or uuid.uuid4().hex)
        except ValueError as e:
            raise _refused(e) from e
        return P.Decision(g["evaluation_id"], g["final_disposition"], action_type, principal, g)

    def evaluate_degraded(self, state, measurement, *, principal, action_type):
        cred, Pv, V, K = _INPUTS[P.ADMISSIBLE]
        values = {"pressure": Pv, "velocity": V, "capacity": K}
        values[measurement] = float("nan") if state == P.E_UNKNOWN else None
        try:
            g = self._k._evaluate(principal, cred, action_type, values["pressure"],
                                  values["velocity"], values["capacity"], uuid.uuid4().hex)
        except ValueError as e:
            raise _refused(e) from e
        except TypeError as e:
            # The kernel stops on a value it cannot compute with. No grant
            # exists: for the caller this is a refusal, though not a recorded one.
            raise P.Refused("INPUT_REJECTED", None, str(e)) from e
        return P.Decision(g["evaluation_id"], g["final_disposition"], action_type, principal, g)

    def commit(self, decision, *, action_type=None):
        g = decision.raw
        try:
            r = self._k._commit(g["evaluation_id"], action_type,
                                action_id=g["action_id"], nonce=g["nonce"])
        except ValueError as e:
            raise _refused(e, g) from e
        return P.Committed(decision.decision_id, r)

    def revoke(self, principal):
        self._k._revoke(principal)

    def drift_state(self):
        before = self._k._epoch
        self._k._reload_policy()
        return f"policy epoch {before}->{self._k._epoch}"

    def stale_grant(self, *, action_type):
        g = self._k._inject_stale(action_type)
        return P.Decision(g["evaluation_id"], g["final_disposition"], action_type, g["principal_id"], g)

    def receipt_verifies(self, decision):
        receipt = decision.raw.get("receipt", {})
        if not receipt.get("signed") or not receipt.get("signature"):
            return False
        try:
            self._k._verify(self._k._pub, receipt)
            return True
        except Exception:
            return False

    def tampered_receipt_verifies(self, decision):
        tampered = dict(decision.raw["receipt"])
        tampered["final_disposition"] = "TAMPERED"
        try:
            self._k._verify(self._k._pub, tampered)
            return True
        except Exception:
            return False

    def manifest_intact(self):
        return bool(self._k._manifest.verify()["integrity_ok"])

    def tampered_manifest_intact(self):
        probe = copy.deepcopy(self._k._manifest)
        probe.entries[0]["entry"]["final_disposition"] = "TAMPERED"
        return bool(probe.verify()["integrity_ok"])

    def tenir_score(self, Pv, V, K):
        return self._k._engine.evaluate(Pv, V, K)

    def run_custom(self, vector_id):
        # Runtime-specific results the legacy adapter reports for vectors that
        # have no neutral scenario: decision reproduction, external-effect
        # evidence, the T6-T8 laboratory probes, and the RN-001 §3 vectors
        # (CT-R4-014 to CT-R4-016), registered with no probe yet.
        if vector_id in ("CT-R4-009", "CT-R4-010", "CT-R4-011", "CT-R4-012", "CT-R4-013",
                         "CT-R4-014", "CT-R4-015", "CT-R4-016"):
            result = self._k.run_vector(vector_id)
            result.interface_mode = self.interface_mode
            result.evidence_level = int(self.evidence_level)
            return result
        return None
