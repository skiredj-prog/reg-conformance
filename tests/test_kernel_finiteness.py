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


def test_finite_inputs_are_unchanged():
    assert ENGINE.evaluate(0.2, 0.2, 0.9)["decision"] == "PASS"
    assert ENGINE.evaluate(0.9, 0.9, 0.1)["decision"] == "HARD_VETO"


def test_the_result_is_strict_json():
    r = ENGINE.evaluate(float("nan"), 0.2, 0.9)
    json.dumps(r, allow_nan=False)
    r = ENGINE.evaluate(0.2, 0.2, 0.9)
    assert math.isfinite(r["s_score"])
    json.dumps(r, allow_nan=False)


def test_the_shim_refuses_a_boolean_measurement():
    pydantic = pytest.importorskip("pydantic")
    pytest.importorskip("fastapi")
    import shim
    with pytest.raises(pydantic.ValidationError):
        shim.Measurements(pressure=True)
    assert shim.Measurements(pressure=0.2).pressure == 0.2
    assert shim.Measurements().pressure is None
