"""Register CT-R4-011..013 into runner.CORE_VECTORS / VECTORS when imported."""


def register(runner_module) -> None:
    TestVector = runner_module.TestVector
    extra = {
        "CT-R4-011": TestVector(
            "CT-R4-011", "RFC-4 lifecycle T6", "UNKNOWN → RESOLVED (qualified)",
            "Qualified evidence within τ_K or explicit resolve transitions UNKNOWN/AWAITING to RESOLVED.",
        ),
        "CT-R4-012": TestVector(
            "CT-R4-012", "RFC-4 lifecycle T7", "UNKNOWN → FAILED (evidence guard)",
            "FAILED requires evidence_qualified=true; timeout alone must not auto-FAILED.",
        ),
        "CT-R4-013": TestVector(
            "CT-R4-013", "RFC-4 lifecycle T8", "FAILED + retry_eligible → new attempt",
            "retry_eligible=true allows a new attempt_id on same LEI; false keeps LEI locked.",
        ),
    }
    runner_module.CORE_VECTORS.update(extra)
    runner_module.VECTORS.update(extra)
