"""Contract gates for T6-T8; laboratory PASS is not native certification."""
import pytest

from lifecycle.t7_membrane_probe import run_t6_probe, run_t7_probe, run_t8_probe
from runner import _run_lifecycle_membrane_vector, CORE_VECTORS


@pytest.mark.parametrize("vector_id,probe", [
    ("CT-R4-011", run_t6_probe),
    ("CT-R4-012", run_t7_probe),
    ("CT-R4-013", run_t8_probe),
])
def test_scoped_lab_lifecycle_probe(vector_id, probe):
    assert vector_id in CORE_VECTORS
    status, detail = probe()
    assert status == "PASS", (vector_id, status, detail)
    assert "LAB_ONLY" in detail


@pytest.mark.parametrize("vector_id", ["CT-R4-011", "CT-R4-012", "CT-R4-013"])
def test_lab_success_does_not_become_native_conformance(vector_id):
    class FakeAdapter:
        def _gap(self, vid, reason):
            return ("IMPLEMENTATION_GAP", vid, reason)

        def _fail(self, vid, reason):
            return ("FAIL", vid, reason)

    status, vid, reason = _run_lifecycle_membrane_vector(FakeAdapter(), vector_id)
    assert status == "IMPLEMENTATION_GAP"
    assert vid == vector_id
    assert "LAB_PROBE_PASS_ONLY" in reason
    assert "native TENIR-Gov" in reason
