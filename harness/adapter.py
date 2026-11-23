"""PortAdapter: runs the neutral scenarios against any RuntimePort and
produces the runner's existing result and report types."""
from __future__ import annotations

import math

import importlib

import runner as R
from .port import (ALL_BOUNDS, ALL_CAPABILITIES, ALL_EPISTEMIC, ALL_INTENTS, CLOCK,
                   CONFIDENCE, RuntimePort)
from . import properties
from .scenarios import CHECKS, PROBES, SCENARIOS

FLAG_RESERVE = ("obtained under a declared mapping interpretation, pending ratification; "
                "the FLAG on this path states no condition.")
HARNESS_GAP = ("HARNESS_GAP: no runtime-neutral scenario exists for this vector yet; "
               "the subject was not evaluated.")

# Rule of 23 November 2026 (standard author's decision, 15:07 UTC, option A),
# for the registered rows no port can adapt. A row the frozen RFCs do not
# specify (RESERVED in VECTORS.md) and a row superseded by a ratified revision
# have no normative property to test on any subject: they are reported
# NOT_SPECIFIED, listed with their reason, and stay out of conformance_status
# and of the exit code. A row whose property a harness check exercises is
# reported by that check (EXERCISED_BY_CHECK) when the check ran and passed.
# A row the implementer declares outside the runtime's perimeter, with a signed
# reason, is NOT_IN_PERIMETER, as a property check already could be. The rule
# is dated: it reinterprets no report produced before it. What it removes from
# the exit code is listed in every report, under `exit_code_rule`.
EXIT_CODE_RULE_DATE = "2026-11-23"
OUT_OF_EXIT_CODE = ("NOT_SPECIFIED", "EXERCISED_BY_CHECK", "NOT_IN_PERIMETER", "NOT_APPLICABLE")
# Registered under RN-001 §3, withdrawn readings: superseded by the RFC-4 v0.3
# revision of 19 November 2026 (§4), ratified and kept outside the frozen
# baseline. Kept with their text and ids; nothing left to test on them.
SUPERSEDED = {"CT-R4-014": "CT-R4-004a", "CT-R4-015": "CT-R4-004a", "CT-R4-016": "CT-R4-004b"}
_RESERVED_ROWS = None


def reserved_rows() -> dict:
    """id -> VECTORS.md row, for every row whose status is RESERVED."""
    global _RESERVED_ROWS
    if _RESERVED_ROWS is None:
        _RESERVED_ROWS = {vid: row for vid, row in properties.index_rows().items()
                          if row.get("status") == "RESERVED"}
    return _RESERVED_ROWS


class PortAdapter(R.BaseAdapter):
    def __init__(self, port: RuntimePort):
        unknown = set(port.capabilities) - ALL_CAPABILITIES
        if unknown:
            raise ValueError(f"port declares unknown capabilities: {sorted(unknown)}")
        unknown = set(port.intents) - ALL_INTENTS
        if unknown:
            raise ValueError(f"port declares unknown intents: {sorted(unknown)}")
        for combo in port.combinations:
            if len(combo) < 2 or not set(combo) <= set(port.intents):
                raise ValueError("a combination must list two or more intents the port "
                                 f"declares: {sorted(combo)}")
        unknown = set(port.bounds) - ALL_BOUNDS
        if unknown:
            raise ValueError(f"port declares unknown bounds: {sorted(unknown)}")
        for name, seconds in dict(port.bounds, effect_window=port.effect_window).items():
            if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) \
                    or not 0 <= seconds < float("inf"):
                raise ValueError(f"{name} must be a finite number of seconds, zero or more")
        if CLOCK in port.capabilities and port.clock_mode not in ("real", "simulated"):
            raise ValueError("a port that declares clock says how time passes: real or simulated")
        if port.effect_window and CLOCK not in port.capabilities:
            raise ValueError("a port that declares an effect window must be able to let it pass")
        if port.exhaustion_policy not in (None, "fail-closed", "fail-degraded"):
            raise ValueError("exhaustion_policy is fail-closed, fail-degraded or None")
        unknown = set(port.degradations) - ALL_EPISTEMIC
        if unknown:
            raise ValueError(f"port declares unknown epistemic states: {sorted(unknown)}")
        for state, names in port.degradations.items():
            if not names or not all(isinstance(n, str) and n for n in names):
                raise ValueError(f"{state}: name at least one measurement the port can degrade")
        if CONFIDENCE in port.capabilities and port.confidence_steps < 2:
            raise ValueError("a port that declares confidence submits at two levels or more")
        for name, domain in dict(port.domains).items():
            if not isinstance(name, str) or not name:
                raise ValueError("a declared domain names its measurement")
            try:
                low, high = domain
            except (TypeError, ValueError):
                raise ValueError(f"{name}: a domain is a (low, high) pair of finite numbers") from None
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                   for v in (low, high)) or not low < high:
                raise ValueError(f"{name}: a domain is a (low, high) pair of finite numbers, low < high")
        self.port = port
        self.interface_mode = port.interface_mode
        # A port is a translation layer: it can never report native conformance.
        self.evidence_level = R.EvidenceLevel(min(int(port.evidence_level),
                                                  int(R.EvidenceLevel.ADAPTER_TESTED)))
        # check id -> facts a scenario recorded beside its result (for example
        # that it went forward on a FLAG). Kept apart from the result type.
        self.facts = {}

    def _run_scenario(self, vid, scenario):
        self.facts.pop(vid, None)
        # Everything that keeps the scenario from running, in one note: a
        # missing capability, an intent the runtime has no notion of, a bound
        # the subject does not declare.
        lacking = [(label, sorted(wanted - set(have))) for label, wanted, have in (
            ("port does not declare: ", scenario.requires, self.port.capabilities),
            ("port cannot produce intent: ", scenario.intents, self.port.intents),
            ("no bound declared for: ", scenario.bounds, self.port.bounds),
            ("port cannot make evidence: ", scenario.degradations, self.port.degradations),
            # A check on declared domains runs only when the port declares one.
            ("port declares no admissible domain for its ", scenario.domains,
             {"measurements"} if self.port.domains else set()))]
        lacking = [label + ", ".join(names) for label, names in lacking if names]
        if lacking:
            return self._ar(vid, "; ".join(lacking))
        try:
            self.port.reset()
            outcome = scenario.run(self.port)
            state, details = outcome[0], outcome[1]
            if len(outcome) > 2 and outcome[2]:
                self.facts[vid] = outcome[2]
        except NotImplementedError as e:
            # Declared but not implemented: the port's claim is wrong, not the subject.
            return self._inconclusive(vid, f"declared capability not implemented: {e}")
        except Exception as e:
            status = self._inconclusive if vid == "C3" else self._fail
            return status(vid, f"exception prevents a determinate result: {e}")
        fact = self.facts.get(vid)
        if fact and fact.get("admitted_on") == "FLAG" and not fact.get("flag_conditions"):
            # Author's decision 3 (19 November 2026), CLAIMS.md, RN-001 §1: the FLAG
            # without a condition is recorded apart as an implementation gap, whatever
            # the result. The check keeps its result under the declared admission
            # mapping; a pass carries the reserve below.
            fact["implementation_gap"] = "FLAG without an explicit condition (RFC-0 §4)"
            if state == R.ReportingState.PASS.value:
                return self._r(vid, R.ReportingState.PASS, details, gap_note=FLAG_RESERVE)
        return self._r(vid, R.ReportingState(state), details)

    @staticmethod
    def _perimeter_declaration(row, decl):
        if not (isinstance(decl, dict) and all(
                isinstance(decl.get(f), str) and decl[f].strip() for f in ("declared_by", "reason"))):
            raise ValueError(f"{row}: a not_in_perimeter declaration needs a "
                             "non-empty 'declared_by' and 'reason'")
        return f"not_in_perimeter on {row}, declared by {decl['declared_by']}: {decl['reason']}"

    def run_vector(self, vid):
        if vid in self.port.not_applicable:
            if vid in SCENARIOS:
                # Same rule as for run_custom: a port does not set aside a neutral scenario.
                # A scenario that cannot run says so itself (ADAPTER_REQUIRED, INCONCLUSIVE).
                raise ValueError(f"{vid}: a port may not declare a neutral scenario not applicable")
            return self._na(vid, self.port.not_applicable[vid])
        if vid in self.port.not_in_perimeter:
            if vid in SCENARIOS:
                raise ValueError(f"{vid}: a port may not declare a neutral scenario outside the perimeter")
            # Rule of 23 November 2026: the implementer's signed declaration on a
            # registered row, as on a property check. Neither PASS nor FAIL.
            return self._r(vid, R.ReportingState.NOT_IN_PERIMETER,
                           gap_note=self._perimeter_declaration(vid, self.port.not_in_perimeter[vid]))
        custom = self.port.run_custom(vid)
        if custom is not None:
            if vid in SCENARIOS:
                raise ValueError(f"{vid}: a port may not override a neutral scenario")
            return custom
        if vid in SCENARIOS:
            result = self._run_scenario(vid, SCENARIOS[vid])
            if (result.status == R.ReportingState.ADAPTER_REQUIRED
                    and vid in self.port.declared_gaps
                    and str(result.gap_note or result.details or "").startswith("port does not declare: ")):
                # The scenario cannot run for want of a capability and the port
                # declares the gap on that row: the declaration is the more
                # precise record. Same exit code; the note travels.
                return self._gap(vid, self.port.declared_gaps[vid])
            return result
        if vid in self.port.declared_gaps:
            return self._gap(vid, self.port.declared_gaps[vid])
        if vid in SUPERSEDED:
            return self._r(vid, R.ReportingState.NOT_SPECIFIED, gap_note=(
                f"superseded by {SUPERSEDED[vid]} (RFC-4 v0.3 revision of 19 November 2026, §4); "
                f"withdrawn reading, kept with its id and text; nothing to test "
                f"(rule of {EXIT_CODE_RULE_DATE})"))
        row = reserved_rows().get(vid)
        if row is not None:
            return self._r(vid, R.ReportingState.NOT_SPECIFIED, gap_note=(
                f"RESERVED in VECTORS.md ({row.get('rfc', '?')}): the frozen RFCs do not specify "
                f"this row; a proposal, nothing to test (rule of {EXIT_CODE_RULE_DATE})"))
        return self._ar(vid, HARNESS_GAP)

    @staticmethod
    def fold_checks(results, checks):
        """Rule of 23 November 2026: a registered row with no neutral scenario
        (HARNESS_GAP) whose property a check exercised in this run is reported
        by that check. The check passed: the row says so and points to it,
        out of the exit code. The check failed: the row fails, the property is
        one the RFC states. Anything else: the row keeps its gap, with the
        check's status noted. Returns a new list; the check results are untouched."""
        by_row = {}
        for c in checks:
            row = CHECKS[c.vector_id].exercises
            by_row.setdefault(row, []).append(c)
        out = []
        for r in results:
            folded = by_row.get(r.vector_id)
            if not folded or r.status != R.ReportingState.ADAPTER_REQUIRED or r.gap_note != HARNESS_GAP:
                out.append(r)
                continue
            names = ", ".join(f"{c.vector_id} {c.status.value}" for c in folded)
            statuses = {c.status for c in folded}
            if statuses == {R.ReportingState.PASS}:
                r = R.ConformanceResult(r.vector_id, R.ReportingState.EXERCISED_BY_CHECK,
                                        r.interface_mode, r.evidence_level,
                                        details=f"exercised by {names}: "
                                                + "; ".join(c.details for c in folded),
                                        gap_note=f"reported by its property check (rule of {EXIT_CODE_RULE_DATE})")
            elif R.ReportingState.FAIL in statuses:
                r = R.ConformanceResult(r.vector_id, R.ReportingState.FAIL, r.interface_mode,
                                        r.evidence_level,
                                        details=f"its property check failed: {names}: "
                                                + "; ".join(c.details for c in folded
                                                            if c.status == R.ReportingState.FAIL))
            else:
                r = R.ConformanceResult(r.vector_id, r.status, r.interface_mode, r.evidence_level,
                                        r.details, gap_note=f"{r.gap_note} Its property check: {names}.")
            out.append(r)
        return out

    def run_probes(self):
        """Harness probes, reported apart from the REG vector set."""
        return [self._run_scenario(vid, s) for vid, s in PROBES.items()]

    def run_checks(self):
        """Property checks, reported apart from the REG vector set. When the
        implementer has declared a gap on the row a check exercises, the note
        travels with any result that is not a pass."""
        out = []
        for vid, s in CHECKS.items():
            decl = self.port.not_in_perimeter.get(s.exercises)
            if decl is not None:
                out.append(self._r(vid, R.ReportingState.NOT_IN_PERIMETER,
                                   gap_note=self._perimeter_declaration(s.exercises, decl)))
                continue
            r = self._run_scenario(vid, s)
            gap = self.port.declared_gaps.get(s.exercises)
            if gap and r.status != R.ReportingState.PASS:
                note = f"gap declared by the implementer on {s.exercises}: {gap}"
                r.gap_note = f"{r.gap_note} | {note}" if r.gap_note else note
            out.append(r)
        return out


def load_port(spec: str) -> RuntimePort:
    """'package.module:ClassName' -> instance."""
    module, _, cls = spec.partition(":")
    if not cls:
        raise ValueError("port must be given as 'package.module:ClassName'")
    return getattr(importlib.import_module(module), cls)()
