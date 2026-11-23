"""PortAdapter: runs the neutral scenarios against any RuntimePort and
produces the runner's existing result and report types."""
from __future__ import annotations

import importlib

import runner as R
from .port import (ALL_BOUNDS, ALL_CAPABILITIES, ALL_EPISTEMIC, ALL_INTENTS, CLOCK,
                   CONFIDENCE, PRIMITIVES, RuntimePort)
from .scenarios import CHECKS, PROBES, SCENARIOS

FLAG_RESERVE = ("obtained under a declared mapping interpretation, pending ratification; "
                "the FLAG on this path states no condition.")
HARNESS_GAP = ("HARNESS_GAP: no runtime-neutral scenario exists for this vector yet; "
               "the subject was not evaluated.")


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
            ("port cannot make evidence: ", scenario.degradations, self.port.degradations))]
        lacking = [label + ", ".join(names) for label, names in lacking if names]
        if lacking:
            return self._ar(vid, "; ".join(lacking))
        # Raised past the scenario (sys.exit included: a port does not end the run):
        # the scenario decides PASS and FAIL, and it decided nothing here. A crash of
        # the port or of the harness, or a refusal the scenario did not expect, is
        # HARNESS_ERROR (C3 included), never a FAIL of the subject (review of #80).
        try:
            self.port.reset()                 # not a capability: any failure is a crash
        except (Exception, SystemExit) as e:
            return self._harness_error(vid, e)
        try:
            outcome = scenario.run(self.port)
            state, details = outcome[0], outcome[1]
            if len(outcome) > 2 and outcome[2]:
                self.facts[vid] = outcome[2]
        except NotImplementedError as e:
            primitive = _entry_primitive(self.port, e)
            if primitive is None:
                # Raised by the scenario or the harness, or by a port method that
                # is no capability's primitive, or by a primitive of a capability
                # the port does not declare: not the port's claim, a crash.
                return self._harness_error(vid, e)
            # Declared but not implemented: the port's claim is wrong, not the subject.
            return self._inconclusive(
                vid, f"declared capability not implemented: {PRIMITIVES[primitive]} ({primitive}): {e}")
        except (Exception, SystemExit) as e:
            return self._harness_error(vid, e)
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

    def run_vector(self, vid):
        if vid in self.port.not_applicable:
            if vid in SCENARIOS:
                # Same rule as for run_custom: a port does not set aside a neutral scenario.
                # A scenario that cannot run says so itself (ADAPTER_REQUIRED, INCONCLUSIVE).
                raise ValueError(f"{vid}: a port may not declare a neutral scenario not applicable")
            return self._na(vid, self.port.not_applicable[vid])
        custom = self.port.run_custom(vid)
        if custom is not None:
            if vid in SCENARIOS:
                raise ValueError(f"{vid}: a port may not override a neutral scenario")
            return custom
        if vid in SCENARIOS:
            return self._run_scenario(vid, SCENARIOS[vid])
        if vid in self.port.declared_gaps:
            return self._gap(vid, self.port.declared_gaps[vid])
        return self._ar(vid, HARNESS_GAP)

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
                if not (isinstance(decl, dict) and all(
                        isinstance(decl.get(f), str) and decl[f].strip() for f in ("declared_by", "reason"))):
                    raise ValueError(f"{s.exercises}: a not_in_perimeter declaration needs a "
                                     "non-empty 'declared_by' and 'reason'")
                out.append(self._r(vid, R.ReportingState.NOT_IN_PERIMETER, gap_note=(
                    f"not_in_perimeter on {s.exercises}, declared by {decl['declared_by']}: "
                    f"{decl['reason']}")))
                continue
            r = self._run_scenario(vid, s)
            gap = self.port.declared_gaps.get(s.exercises)
            if gap and r.status != R.ReportingState.PASS:
                note = f"gap declared by the implementer on {s.exercises}: {gap}"
                r.gap_note = f"{r.gap_note} | {note}" if r.gap_note else note
            out.append(r)
        return out


def _primitive_codes(port) -> dict:
    """Code object -> primitive name, for the functions the port's class binds
    to each primitive name, through any decorator (`__wrapped__`) and whatever
    the function is called: a wrapper or an alias still is that primitive."""
    codes = {}
    for name in PRIMITIVES:
        fn = getattr(type(port), name, None)
        while fn is not None:
            code = getattr(fn, "__code__", None)
            if code is not None:
                codes.setdefault(code, name)
            fn = getattr(fn, "__wrapped__", None)
    return codes


def _entry_primitive(port, exc):
    """The primitive through which the exception left the port, if its
    capability is declared; None otherwise. The first frame of the port on the
    way down is where scenario code entered it; what the primitive calls below
    is the primitive's own concern."""
    codes = _primitive_codes(port)
    tb = exc.__traceback__
    while tb is not None:
        frame = tb.tb_frame
        bound = frame.f_locals.get("self", port)
        name = codes.get(frame.f_code) if bound is port else None
        if name is not None:
            return name if PRIMITIVES[name] in port.capabilities else None
        if frame.f_locals.get("self") is port:
            return None            # entered through a port method that is no primitive
        tb = tb.tb_next
    return None


def load_port(spec: str) -> RuntimePort:
    """'package.module:ClassName' -> instance."""
    module, _, cls = spec.partition(":")
    if not cls:
        raise ValueError("port must be given as 'package.module:ClassName'")
    return getattr(importlib.import_module(module), cls)()
