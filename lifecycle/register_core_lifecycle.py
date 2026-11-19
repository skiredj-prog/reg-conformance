"""Register CT-R4-011..013 into runner.CORE_VECTORS / VECTORS when imported."""


def register(runner_module) -> None:
    TestVector = runner_module.TestVector
    extra = {
        "CT-R4-011": TestVector(
            "CT-R4-011", "Lifecycle T6 (tenir-conformance-s1-g1@8bc0e5e; not named in manuscript v7.2 nor in the frozen RFC-4 text)", "UNKNOWN → RESOLVED (qualified)",
            "Qualified evidence within τ_R (receipt qualification window) or explicit resolve transitions UNKNOWN/AWAITING to RESOLVED.",
        ),
        "CT-R4-012": TestVector(
            "CT-R4-012", "Lifecycle T7 (manuscript v7.2 §4.4; not in the frozen RFC-4 text)", "UNKNOWN → FAILED (evidence guard)",
            "FAILED requires verified, exactly bound non-execution attestation; timeout alone never fails.",
        ),
        "CT-R4-013": TestVector(
            "CT-R4-013", "Lifecycle T8 (tenir-conformance-s1-g1@8bc0e5e; not named in manuscript v7.2 nor in the frozen RFC-4 text)", "FAILED + retry_eligible → new attempt",
            "retry_eligible=true allows a new attempt_id on same LEI; false keeps LEI locked.",
        ),
    }
    runner_module.CORE_VECTORS.update(extra)
    runner_module.VECTORS.update(extra)
