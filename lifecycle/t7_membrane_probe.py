"""Scoped RFC-4 T6/T7/T8 probes against the separate laboratory membrane.

A PASS means the imported laboratory membrane satisfied this behavioral probe.
It is not native TENIR-Gov conformance or independently proven external custody.
The signer uses a PUBLIC RFC 8032 Ed25519 test vector, never a production key.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Callable, Tuple

PAYLOAD = {"P": 0.5, "V": 0.5, "K": 1.0, "option_space": 1.0}
# RFC 8032 test vector 1; publicly disclosed test material.
_TEST_ONLY_SEED = bytes.fromhex(
    "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
)


def _load_lab():
    try:
        from tenir_conformance.membrane.membrane import (
            AttemptState, FakeClock, Membrane, Receipt,
        )
        from tenir_conformance.membrane.kernel_bridge import KernelBridge
        from tenir_conformance.membrane.attestation import NonExecutionAttestation
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as exc:
        return None, f"LAB_NOT_INSTALLED: {exc}"
    return (AttemptState, FakeClock, Membrane, Receipt, KernelBridge,
            NonExecutionAttestation, Ed25519PrivateKey), ""


def _signed_non_execution(modules, *, attempt_id: str, lei: str, nonce: str):
    _, _, _, _, _, Attestation, PrivateKey = modules
    draft = Attestation(
        attestation_id=f"LAB-{attempt_id}", attempt_id=attempt_id,
        lei=lei, nonce=nonce, non_execution_confirmed=True,
        key_id="K1", key_epoch=1, signature=None, algorithm="Ed25519",
    )
    signature = PrivateKey.from_private_bytes(_TEST_ONLY_SEED).sign(
        draft.signing_bytes()
    )
    return replace(draft, signature=signature.hex())


def _outcome(test: Callable[[], None]) -> Tuple[str, str]:
    try:
        test()
    except AssertionError as exc:
        return "FAIL", f"BEHAVIOR_MISMATCH: {exc or 'assertion failed'}"
    except Exception as exc:
        return "FAIL", f"PROBE_EXCEPTION: {type(exc).__name__}: {exc}"
    return "PASS", "LAB_ONLY: checked against imported membrane (not native conformance)"


def run_t6_probe() -> Tuple[str, str]:
    """T6: a bound, in-window receipt resolves an awaiting attempt."""
    modules, missing = _load_lab()
    if modules is None:
        return "GAP", missing
    State, Clock, Membrane, Receipt, Bridge, _, _ = modules

    def check():
        clock = Clock(now_ms=1_000_000)
        m = Membrane(Bridge(), clock=clock, tau_k_ms=5_000)
        m.admit_and_await_qualification(
            lei="L-T6", attempt_id="A-T6", payload=PAYLOAD,
            apply_effect=True, nonce="n-t6",
        )
        clock.tick(100)
        receipt = m.deliver_qualifying_receipt(
            Receipt(attempt_id="A-T6", lei="L-T6", nonce="n-t6")
        )
        assert receipt.client_state == "RESOLVED", receipt.client_state
        assert m.attempts["A-T6"].state == State.RESOLVED
        assert m.retry_eligible_for("L-T6") is False

    return _outcome(check)


def run_t7_probe() -> Tuple[str, str]:
    """T7: timeout/boolean alone cannot FAILED; verified attestation can."""
    modules, missing = _load_lab()
    if modules is None:
        return "GAP", missing
    State, Clock, Membrane, _, Bridge, _, _ = modules

    def check():
        m = Membrane(Bridge(), clock=Clock(now_ms=1_000_000), tau_k_ms=5_000)
        m.process_transaction(
            lei="L-T7", attempt_id="A-T7", nonce="n-t7",
            payload=PAYLOAD, request_lost=True,
        )
        assert m.attempts["A-T7"].state == State.UNKNOWN
        m.declare_failed(
            attempt_id="A-T7", evidence_qualified=False, retry_eligible=True,
        )
        assert m.attempts["A-T7"].state == State.UNKNOWN
        m.declare_failed(
            attempt_id="A-T7", evidence_qualified=True,
            retry_eligible=True, reason="PROOF_NON_EXECUTION",
            attestation=_signed_non_execution(
                modules, attempt_id="A-T7", lei="L-T7", nonce="n-t7",
            ),
        )
        assert m.attempts["A-T7"].state == State.FAILED
        assert m.attempts["A-T7"].non_execution_confirmed is True
        assert m.attempts["A-T7"].retry_eligible is True

        clock = Clock(now_ms=1_000_000)
        timeout = Membrane(Bridge(), clock=clock, tau_k_ms=5_000)
        timeout.admit_and_await_qualification(
            lei="L-TO", attempt_id="A-TO", payload=PAYLOAD,
            apply_effect=True, nonce="n-timeout",
        )
        clock.advance_to(1_005_000)
        timeout.check_qualification_timeouts()
        assert timeout.attempts["A-TO"].state == State.UNKNOWN

    return _outcome(check)


def run_t8_probe() -> Tuple[str, str]:
    """T8: verified non-execution AND explicit retry eligibility required."""
    modules, missing = _load_lab()
    if modules is None:
        return "GAP", missing
    State, Clock, Membrane, _, Bridge, _, _ = modules

    def check():
        for eligible in (False, True):
            lei = f"L-T8-{eligible}"
            old_id = f"A-T8-{eligible}"
            nonce = f"n-t8-{eligible}"
            m = Membrane(Bridge(), clock=Clock(now_ms=1_000_000), tau_k_ms=5_000)
            m.process_transaction(
                lei=lei, attempt_id=old_id, nonce=nonce,
                payload=PAYLOAD, request_lost=True,
            )
            m.declare_failed(
                attempt_id=old_id, evidence_qualified=True,
                retry_eligible=eligible,
                attestation=_signed_non_execution(
                    modules, attempt_id=old_id, lei=lei, nonce=nonce,
                ),
            )
            assert m.attempts[old_id].state == State.FAILED
            assert m.retry_eligible_for(lei) is eligible, (
                f"retry_eligible_for({lei}) disagrees with T8={eligible}"
            )
            result = m.retry(
                lei=lei, attempt_id=f"A2-{eligible}",
                nonce=f"n-retry-{eligible}", payload=PAYLOAD,
            )
            if eligible:
                assert result.kernel_decision != "NOT_EVALUATED"
                assert f"A2-{eligible}" in m.attempts
            else:
                assert result.kernel_decision == "NOT_EVALUATED"
                assert f"A2-{eligible}" not in m.attempts

    return _outcome(check)


if __name__ == "__main__":
    for name, probe in (("T6", run_t6_probe), ("T7", run_t7_probe),
                        ("T8", run_t8_probe)):
        status, detail = probe()
        print(name, status, detail)
        if status != "PASS":
            raise SystemExit(1)
