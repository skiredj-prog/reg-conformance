"""PortAdapter: runs the neutral scenarios against any RuntimePort and
produces the runner's existing result and report types."""
from __future__ import annotations

import importlib

import runner as R
from .port import ALL_CAPABILITIES, ALL_INTENTS, RuntimePort
from .scenarios import PROBES, SCENARIOS

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
        missing = sorted(scenario.requires - set(self.port.capabilities))
        if missing:
            return self._ar(vid, "port does not declare: " + ", ".join(missing))
        missing = sorted(scenario.intents - set(self.port.intents))
        if missing:
            return self._ar(vid, "port cannot produce intent: " + ", ".join(missing))
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
        return self._r(vid, R.ReportingState(state), details)

    def run_vector(self, vid):
        if vid in self.port.not_applicable:
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


def load_port(spec: str) -> RuntimePort:
    """'package.module:ClassName' -> instance."""
    module, _, cls = spec.partition(":")
    if not cls:
        raise ValueError("port must be given as 'package.module:ClassName'")
    return getattr(importlib.import_module(module), cls)()
