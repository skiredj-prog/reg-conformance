"""Readable reference simulator for RFC-3 §6 multi-TAU composition.

This is a local scenario simulator, not a production enforcement component.
The composition liveness window is supplied as an input; derivation and
attestation of tau_K are outside this module.
"""
from enum import Enum
from typing import Dict, List, Optional


class ConflictType(Enum):
    NONE = "Aucun"
    C1_VERTICAL = "C1_Vertical (Invariant de composition viole)"
    C2_HORIZONTAL = "C2_Horizontal (Ressource partagee epuisee)"
    C3_TEMPOREL = "C3_Temporel (Violation progressive au terme de la sequence)"
    C4_NO_PRIORITY = "C4_Priorite absente (Tension sans preseance declaree)"


class Strategy(Enum):
    PRIORITY_ENFORCE = "Priority-Enforce"
    SERIALIZE = "Serialize"
    PARETO_RESTORE = "Pareto-Restore"
    ESCALATE = "Escalate"
    FAIL_CLOSED_COLLECTIF = "Fail-Closed-Collectif"


class TAU:
    """Minimal TAU model. Lower numeric priority means higher priority."""

    def __init__(self, agent_id: str, priority: int,
                 notional_requested: float, lcr_local: float):
        self.agent_id = agent_id
        self.priority = priority
        self.notional_requested = notional_requested
        self.lcr_local = lcr_local
        self.status = "NOMINAL"

    def __repr__(self):
        return f"TAU({self.agent_id}, p={self.priority}, status={self.status})"


class CompositionEngine:
    """Scenario-level dispatcher for the RFC-3 §6 composition strategies."""

    def __init__(self, composition_id: str, lcr_group_threshold: float,
                 shared_notional_limit: float, tau_k_seconds: float,
                 max_hold_minutes: float = 30.0):
        self.composition_id = composition_id
        self.lcr_group_threshold = lcr_group_threshold
        self.shared_notional_limit = shared_notional_limit
        # Supplied input, not derived by this simulator.
        self.tau_k_seconds = tau_k_seconds
        self.max_hold_minutes = max_hold_minutes

    def evaluate_scenario(self, taus: List[TAU], conflict_type: ConflictType,
                          elapsed_tau_k: float,
                          custom_strategy: Optional[Strategy] = None) -> Dict:
        if not taus:
            raise ValueError("Composition vide : aucune TAU à évaluer")

        for tau in taus:
            tau.status = "NOMINAL"

        print()
        print("=" * 60)
        print(f" EVALUATION : {conflict_type.value}")
        print(f" Temps écoulé τ_K : {elapsed_tau_k}s / {self.tau_k_seconds}s")
        print("=" * 60)

        # Absolute precedence 1: expired composition liveness window.
        if elapsed_tau_k >= self.tau_k_seconds:
            print("!! EXPIRATION τ_K : fenêtre de décision dépassée")
            self._apply_fail_closed_collectif(taus)
            return {
                "decision": "FAIL_CLOSED_COLLECTIF",
                "reason": "Expiration de τ_K de composition",
                "affected_taus": [tau.agent_id for tau in taus],
            }

        # Absolute precedence 2: duplicate priority makes precedence ambiguous.
        if len({tau.priority for tau in taus}) < len(taus):
            print(f"!! ÉGALITÉ DE PRIORITÉS dans contexte [{conflict_type.name}]"
                  " → préséance indécidable (C4 implicite)")
            self._apply_fail_closed_collectif(taus)
            return {
                "decision": "FAIL_CLOSED_COLLECTIF",
                "reason": f"Égalité de priorités — C4 implicite [{conflict_type.name}]",
                "affected_taus": [tau.agent_id for tau in taus],
            }

        total_notional = sum(tau.notional_requested for tau in taus)
        # Simplification: unweighted mean, not an exposure-weighted LCR.
        avg_lcr = sum(tau.lcr_local for tau in taus) / len(taus)

        if conflict_type == ConflictType.NONE:
            return self._nominal_path(taus)

        if conflict_type == ConflictType.C1_VERTICAL:
            print(f">> LCR moyen groupe : {avg_lcr:.1f}% "
                  f"(seuil composition : {self.lcr_group_threshold}%)")
            if avg_lcr >= self.lcr_group_threshold:
                print("OK Invariant de composition respecté — aucune violation mesurée")
                return self._nominal_path(taus)
            strategy = custom_strategy or Strategy.PRIORITY_ENFORCE
            print(f"!! Invariant violé — stratégie : {strategy.value}")
            if strategy == Strategy.PRIORITY_ENFORCE:
                return self._priority_enforce(taus)
            if strategy == Strategy.SERIALIZE:
                return self._serialize(taus, total_notional)
            if strategy == Strategy.PARETO_RESTORE:
                return self._pareto_restore(taus)
            if strategy == Strategy.ESCALATE:
                return self._escalate(taus)
            raise ValueError(f"Stratégie '{strategy.value}' non applicable à C1")

        if conflict_type == ConflictType.C2_HORIZONTAL:
            print(f">> Demande globale : {total_notional}Me "
                  f"(plafond partagé : {self.shared_notional_limit}Me)")
            if total_notional <= self.shared_notional_limit:
                print("OK Ressource suffisante — aucune violation mesurée")
                return self._nominal_path(taus)
            strategy = custom_strategy or Strategy.SERIALIZE
            print(f"!! Ressource épuisée — stratégie : {strategy.value}")
            if strategy == Strategy.SERIALIZE:
                return self._serialize(taus, total_notional)
            if strategy == Strategy.PRIORITY_ENFORCE:
                return self._priority_enforce(taus)
            if strategy == Strategy.ESCALATE:
                return self._escalate(taus)
            raise ValueError(f"Stratégie '{strategy.value}' non applicable à C2")

        if conflict_type == ConflictType.C3_TEMPOREL:
            print(">> Rupture prévisible à terme de la séquence")
            strategy = custom_strategy or Strategy.ESCALATE
            print(f"!! Stratégie : {strategy.value}")
            if strategy == Strategy.ESCALATE:
                return self._escalate(taus)
            if strategy == Strategy.SERIALIZE:
                return self._serialize(taus, total_notional)
            raise ValueError(f"Stratégie '{strategy.value}' non applicable à C3")

        if conflict_type == ConflictType.C4_NO_PRIORITY:
            print(">> Tension sans règle de préséance déclarée dans le manifeste")
            print("!! Défaut de gouvernance — basculement de sécurité")
            self._apply_fail_closed_collectif(taus)
            return {
                "decision": "FAIL_CLOSED_COLLECTIF",
                "reason": "C4 — priorité non déclarée dans le manifeste",
            }

        raise ValueError(f"Type de conflit inconnu : {conflict_type}")

    def _priority_enforce(self, taus: List[TAU]) -> Dict:
        """Highest-priority TAU passes; remaining TAUs receive HARD_VETO."""
        ordered = sorted(taus, key=lambda tau: tau.priority)
        passed, vetoed = ordered[0], ordered[1:]
        passed.status = "PASS"
        for tau in vetoed:
            tau.status = "HARD_VETO"
        print(f"OK [Priority-Enforce] PASS : {passed.agent_id} | "
              f"HARD_VETO : {[tau.agent_id for tau in vetoed]}")
        return {
            "decision": "PARTIAL_PASS",
            "passed": passed.agent_id,
            "vetoed": [tau.agent_id for tau in vetoed],
            "progressive_unblock_max_minutes": self.max_hold_minutes,
        }

    def _serialize(self, taus: List[TAU], total_notional: float) -> Dict:
        """Allocate sequentially by priority until the shared cap is reached."""
        print("~~ [Serialize] Allocation séquentielle par priorité")
        allocated = 0.0
        for tau in sorted(taus, key=lambda item: item.priority):
            if allocated + tau.notional_requested <= self.shared_notional_limit:
                tau.status = "PASS"
                allocated += tau.notional_requested
                print(f"   -> {tau.agent_id} : PASS "
                      f"(+{tau.notional_requested}Me, cumul {allocated}Me)")
            else:
                tau.status = "HOLD"
                print(f"   -> {tau.agent_id} : HOLD (plafond atteint)"
                      f" — déblocage progressif ≤ {self.max_hold_minutes} min")
        return {
            "decision": "SERIALIZED",
            "allocated_Me": allocated,
            "status": {tau.agent_id: tau.status for tau in taus},
        }

    def _pareto_restore(self, taus: List[TAU]) -> Dict:
        """Hold the lowest-priority TAUs until the mean LCR invariant is restored."""
        print("~~ [Pareto-Restore] Recherche du sous-ensemble conforme minimum")
        for tau in taus:
            tau.status = "PASS"

        # Lowest priority first: highest numeric value under this convention.
        low_to_high = sorted(taus, key=lambda tau: -tau.priority)
        for candidate in low_to_high:
            active = [tau for tau in taus if tau.status == "PASS"]
            if not active:
                break
            active_lcr = sum(tau.lcr_local for tau in active) / len(active)
            if active_lcr >= self.lcr_group_threshold:
                break
            candidate.status = "HOLD"
            print(f"   -> {candidate.agent_id} : HOLD "
                  f"(priorité {candidate.priority} — préservation invariant)")

        passed = [tau for tau in taus if tau.status == "PASS"]
        held = [tau for tau in taus if tau.status == "HOLD"]
        if not passed:
            print("!! Aucun sous-ensemble conforme — Escalade")
            for tau in taus:
                tau.status = "HOLD"
            return {
                "decision": "ESCALATED_HOLD",
                "reason": "Pareto-Restore échoue : aucun sous-ensemble conforme",
                "status": {tau.agent_id: tau.status for tau in taus},
                "progressive_unblock_max_minutes": self.max_hold_minutes,
            }

        final_lcr = sum(tau.lcr_local for tau in passed) / len(passed)
        print(f"OK [Pareto-Restore] LCR groupe restauré : {final_lcr:.1f}% "
              f"≥ {self.lcr_group_threshold}%")
        print(f"   PASS : {[tau.agent_id for tau in passed]}"
              f" | HOLD : {[tau.agent_id for tau in held]}")
        return {
            "decision": "PARETO_RESTORED",
            "passed": [tau.agent_id for tau in passed],
            "held": [tau.agent_id for tau in held],
            "restored_lcr_pct": round(final_lcr, 1),
        }

    def _escalate(self, taus: List[TAU]) -> Dict:
        """Global HOLD and escalation to the Risk Officer."""
        print("~~ [Escalate] HOLD global + escalade vers le Risk Officer")
        for tau in taus:
            tau.status = "HOLD"
        return {
            "decision": "ESCALATED_HOLD",
            "status": {tau.agent_id: tau.status for tau in taus},
            "progressive_unblock_max_minutes": self.max_hold_minutes,
        }

    def _nominal_path(self, taus: List[TAU]) -> Dict:
        """All TAUs pass when no composition arbitration is needed."""
        for tau in taus:
            tau.status = "PASS"
        print("OK NOMINAL_PASS — toutes TAU conformes")
        return {
            "decision": "NOMINAL_PASS",
            "status": {tau.agent_id: tau.status for tau in taus},
        }

    def _apply_fail_closed_collectif(self, taus: List[TAU]) -> None:
        """Lock only TAUs in this composition; runtime recovery is out of scope."""
        print("## FAIL-CLOSED COLLECTIF (ciblé aux TAU de cette composition)")
        for tau in taus:
            tau.status = "FAIL_CLOSED"
            print(f"   -> {tau.agent_id} : VERROUILLÉ (mode restreint / lecture seule)")

    @staticmethod
    def progressive_unblock_placeholder(tau_ids: List[str], max_minutes: float) -> None:
        """Explicit non-runtime placeholder for progressive unblocking."""
        print(f"\n[Déblocage progressif — placeholder] TAUs : {tau_ids}"
              f" | délai max : {max_minutes} min")
        print("  -> logique runtime à implémenter dans l'orchestrateur")
