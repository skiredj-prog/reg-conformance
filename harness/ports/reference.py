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
                              P.NONCE, P.RECEIPTS, P.MANIFEST, P.TENIR_SCORE})
    intents = frozenset({P.ADMISSIBLE, P.INADMISSIBLE, P.NO_STANDING, P.DENIED})
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
        # evidence and the T6-T8 laboratory probes.
        if vector_id in ("CT-R4-009", "CT-R4-010", "CT-R4-011", "CT-R4-012", "CT-R4-013"):
            result = self._k.run_vector(vector_id)
            result.interface_mode = self.interface_mode
            result.evidence_level = int(self.evidence_level)
            return result
        return None
