"""
tenir-kernel / core / policy_engine.py
========================================
Minimal governance kernel — the deployable core of the admissibility formula.

Architectural note
------------------
This module is the *kernel tier* of the TENIR-Gov two-tier architecture.
It implements the admissibility formula independently of the full middleware stack.

    S = K / (P × V + ε)

Verdicts map to the full middleware decision surface as follows:

    Kernel verdict   Full middleware equivalent   Condition
    ─────────────    ─────────────────────────    ───────────────────────────
    PASS             allow                        S ≥ flag_below
    FLAG             allow_with_alert             hard_veto_below ≤ S < flag_below
    HARD_VETO        block (intended)             S < hard_veto_below

Default thresholds are intentionally conservative (demonstrator profile).
Institutional deployments should define domain-specific YAML policies.

Epsilon (1e-6) is identical to the full middleware canonical value.
"""
from __future__ import annotations

import yaml
from pathlib import Path


class KernelPolicyViolation(ValueError):
    """Raised when the policy configuration is internally inconsistent."""


class PolicyEngine:
    """
    The Ontological Circuit-Breaker (Le Disjoncteur Ontologique).

    Evaluates whether an action is admissible given the current
    Pressure (P), Velocity (V), and Capacity (K) of the governed system.
    Configuration is loaded from a YAML policy file, preserving the
    separation between the formula (code) and the calibration (YAML).
    """

    def __init__(self, config_path: str | Path = "tenir_policies.yaml") -> None:
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Policy file not found: {config_path}")
        with config_path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        self.version: str = cfg.get("version", "unversioned")
        self.institution: str = cfg.get("institution", "unknown")
        params = cfg.get("parameters", {})
        thresholds = cfg.get("thresholds", {})

        self.epsilon: float = float(params.get("epsilon", 1e-6))
        self.hard_veto_below: float = float(thresholds.get("hard_veto_below", 0.5))
        self.flag_below: float = float(thresholds.get("flag_below", 1.2))

        self._validate()

    def _validate(self) -> None:
        if self.epsilon <= 0:
            raise KernelPolicyViolation("epsilon must be > 0")
        if self.hard_veto_below <= 0:
            raise KernelPolicyViolation("hard_veto_below must be > 0")
        if self.flag_below <= self.hard_veto_below:
            raise KernelPolicyViolation(
                "flag_below must be strictly greater than hard_veto_below"
            )

    def evaluate(self, p: float, v: float, k: float) -> dict:
        """
        Compute the stability score and return an admissibility verdict.

        Parameters
        ----------
        p : float  Pressure    (urgency, volatility, deadline compression)
        v : float  Velocity    (rate of change, context drift, commit rate)
        k : float  Capacity    (bottleneck-adjusted institutional throughput)

        Returns
        -------
        dict with keys: s_score, decision, rationale
        """
        denominator = (p * v) + self.epsilon
        s_score = k / denominator

        if s_score < self.hard_veto_below:
            decision = "HARD_VETO"
            rationale = (
                f"S={s_score:.6f} is below the hard-veto floor "
                f"({self.hard_veto_below}). Action is inadmissible — "
                "continuity of the governed system is threatened."
            )
        elif s_score < self.flag_below:
            decision = "FLAG"
            rationale = (
                f"S={s_score:.6f} is marginal (floor={self.hard_veto_below}, "
                f"flag={self.flag_below}). HOLDING-FIRST posture required. "
                "Human review before proceeding."
            )
        else:
            decision = "PASS"
            rationale = (
                f"S={s_score:.6f} is above the flag threshold ({self.flag_below}). "
                "Action is admissible under the current policy."
            )

        return {
            "s_score": round(s_score, 6),
            "decision": decision,
            "rationale": rationale,
            "policy_version": self.version,
            "institution": self.institution,
        }

    # Backward-compatible alias used by V6 documentation
    evaluate_admissibility = evaluate
