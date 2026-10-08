"""CT-R4-012 / T7 probe — evidence guard against the lab membrane.

Returns (status, detail) where status is "PASS" | "FAIL" | "GAP".
Does not claim native kernel conformance; validates the membrane implementation
referenced by T6_T8_GAP_NOTE when the package is importable.
"""

from __future__ import annotations

from typing import Tuple


def run_t7_probe() -> Tuple[str, str]:
    try:
        from tenir_conformance.membrane.membrane import (
            AttemptState,
            FakeClock,
            Membrane,
        )
        from tenir_conformance.membrane.kernel_bridge import KernelBridge
    except ImportError as e:
        return (
            "GAP",
            "Membrane package not importable "
            f"({e}). Install: pip install "
            '"git+https://github.com/skiredj-prog/tenir-conformance-s1-g1.git"',
        )

    payload = {"P": 0.5, "V": 0.5, "K": 1.0, "option_space": 1.0}
    clock = FakeClock(now_ms=1_000_000)
    m = Membrane(KernelBridge(), clock=clock, tau_k_ms=5_000)

    m.process_transaction(
        lei="L-T7", attempt_id="A1", payload=payload, receipt_lost=True
    )
    if m.attempts["A1"].state != AttemptState.UNKNOWN:
        return "FAIL", f"setup: expected UNKNOWN, got {m.attempts['A1'].state}"

    m.declare_failed(
        attempt_id="A1", evidence_qualified=False, retry_eligible=True
    )
    if m.attempts["A1"].state != AttemptState.UNKNOWN:
        return "FAIL", "unqualified declare_failed mutated state away from UNKNOWN"

    events = [e["event"] for e in m.events]
    if "T7_REJECTED_UNQUALIFIED_EVIDENCE" not in events:
        return "FAIL", "missing T7_REJECTED_UNQUALIFIED_EVIDENCE event"

    m.declare_failed(
        attempt_id="A1",
        evidence_qualified=True,
        retry_eligible=True,
        reason="PROOF_NON_EXECUTION",
    )
    if m.attempts["A1"].state != AttemptState.FAILED:
        return "FAIL", f"qualified declare_failed expected FAILED, got {m.attempts['A1'].state}"
    if not m.attempts["A1"].retry_eligible:
        return "FAIL", "retry_eligible not set after qualified T7"

    clock2 = FakeClock(now_ms=1_000_000)
    m2 = Membrane(KernelBridge(), clock=clock2, tau_k_ms=5_000)
    m2.admit_and_await_qualification(
        lei="L-TO", attempt_id="B1", payload=payload, apply_effect=True
    )
    clock2.advance_to(1_000_000 + 5_000)
    m2.check_qualification_timeouts()
    if m2.attempts["B1"].state != AttemptState.UNKNOWN:
        return "FAIL", f"timeout alone expected UNKNOWN, got {m2.attempts['B1'].state}"

    return (
        "PASS",
        "T7 evidence guard: unqualified rejected; qualified → FAILED; "
        "timeout alone remains UNKNOWN (membrane lab)",
    )


if __name__ == "__main__":
    status, detail = run_t7_probe()
    print(status, detail)
    raise SystemExit(0 if status == "PASS" else 1)
