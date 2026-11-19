"""Finiteness guard of the reference kernel (decisions 5 and 6, 19 November 2026).

Every comparison with NaN is false, so a kernel that only tests `S < floor`
admits NaN. A measure that is not a finite number is insufficient evidence:
never PASS, never FLAG, and named in `unmeasured_axes`.
"""
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kernel.policy_engine import PolicyEngine  # noqa: E402

ENGINE = PolicyEngine(ROOT / "kernel" / "tenir_policies.yaml")
BAD = [float("nan"), float("inf"), float("-inf"), None, "0.9"[:0], "0.2", True, 10**400, object()]


@pytest.mark.parametrize("axis", [0, 1, 2])
@pytest.mark.parametrize("bad", BAD, ids=repr)
def test_a_non_finite_axis_is_held_never_admitted(axis, bad):
    args = [0.2, 0.2, 0.9]
    args[axis] = bad
    r = ENGINE.evaluate(*args)
    assert r["decision"] == "HOLD"
    assert r["reason"] == "INSUFFICIENT_EVIDENCE"
    assert r["unmeasured_axes"] == [("P", "V", "K")[axis]]
    assert r["s_score"] is None


@pytest.mark.parametrize("axis", [0, 1], ids=["P", "V"])
@pytest.mark.parametrize("bad", [None, float("nan"), float("inf"), "0.2"], ids=repr)
def test_a_conclusive_veto_is_not_masked_by_an_unmeasured_axis(axis, bad):
    # K = 0 vetoes whatever P and V (RFC-0 §4: the most restrictive applicable
    # disposition governs). The unmeasured axis is still reported.
    args = [0.9, 0.9, 0.0]
    args[axis] = bad
    r = ENGINE.evaluate(*args)
    assert r["decision"] == "HARD_VETO"
    assert r["unmeasured_axes"] == [("P", "V")[axis]]
    assert r["s_score"] is None
    json.dumps(r, allow_nan=False)


def test_an_unmeasured_capacity_is_held_not_vetoed():
    r = ENGINE.evaluate(0.9, 0.9, None)
    assert (r["decision"], r["reason"], r["unmeasured_axes"]) == ("HOLD", "INSUFFICIENT_EVIDENCE", ["K"])


def test_a_zero_denominator_does_not_raise():
    eps = ENGINE.epsilon
    held = ENGINE.evaluate(-eps, 1.0, 0.5)            # P × V + ε = 0
    assert (held["decision"], held["reason"]) == ("HOLD", "INSUFFICIENT_EVIDENCE")
    assert ENGINE.evaluate(-eps, 1.0, 0.0)["decision"] == "HARD_VETO"


def test_finite_inputs_are_unchanged():
    assert ENGINE.evaluate(0.2, 0.2, 0.9)["decision"] == "PASS"
    assert ENGINE.evaluate(0.9, 0.9, 0.1)["decision"] == "HARD_VETO"


def test_the_result_is_strict_json():
    r = ENGINE.evaluate(float("nan"), 0.2, 0.9)
    json.dumps(r, allow_nan=False)
    r = ENGINE.evaluate(0.2, 0.2, 0.9)
    assert math.isfinite(r["s_score"])
    json.dumps(r, allow_nan=False)


@pytest.mark.parametrize("bad", [True, False, "0.2", "abc"], ids=repr)
def test_the_shim_refuses_a_measurement_that_is_not_a_number(bad):
    pydantic = pytest.importorskip("pydantic")
    pytest.importorskip("fastapi")
    import shim
    with pytest.raises(pydantic.ValidationError):
        shim.Measurements(pressure=bad)


@pytest.mark.parametrize("pressure, volatility",
                         [(10**400, 1), (10**400, 0.5), (-0.04, 1.0), (None, 0.5), (0.04, None)],
                         ids=repr)
def test_a_velocity_that_cannot_be_derived_is_unmeasured(pressure, volatility):
    pytest.importorskip("fastapi")
    import shim
    v = shim._derived_velocity(pressure, volatility)
    assert v is None
    assert ENGINE.evaluate(pressure, v, 0.9)["decision"] == "HOLD"


def test_a_derived_velocity_is_kept():
    pytest.importorskip("fastapi")
    import shim
    assert shim._derived_velocity(0.04, 1.0) == pytest.approx(0.2)


def test_the_shim_keeps_numbers_and_null():
    pytest.importorskip("fastapi")
    import shim
    m = shim.Measurements(pressure=0.2, capacity=1)
    assert (m.pressure, m.volatility, m.velocity, m.capacity) == (0.2, None, None, 1)
    assert math.isnan(shim.Measurements(pressure=float("nan")).pressure)  # held by the kernel
