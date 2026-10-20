#!/usr/bin/env python3
"""
validate_profiles.py v2.0.0
Valide les profils REG+ contre les règles de compatibilité structurelle (v2.0.0)
et les règles de quorum/fault model (E2, E3).

Usage:
    python validate_profiles.py profiles/*.yaml

Exit codes:
    0 = toutes les validations passent
    1 = au moins une violation structurelle
    2 = erreur d'exécution
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple


def load_rules(rules_path: Path) -> List[Dict]:
    """Charge les règles depuis compatibility-rules-v2.yaml"""
    with open(rules_path) as f:
        data = yaml.safe_load(f)
    return data.get("constraints", [])


def evaluate_simple_constraint(config: Dict, constraint: Dict) -> Tuple[bool, str]:
    """Évalue une contrainte simple : SI field == value ALORS requires.field IN allowed_values"""
    condition = constraint.get("condition", {})
    requires = constraint.get("requires", {})
    
    cond_field = condition.get("field")
    cond_value = condition.get("value")
    
    # Vérifier si la condition s'applique
    if config.get(cond_field) != cond_value:
        return True, "N/A"  # Condition non applicable
    
    # Vérifier l'exigence
    req_field = requires.get("field")
    allowed = requires.get("allowed_values", [])
    
    if config.get(req_field) not in allowed:
        msg = f"{cond_field}={cond_value} exige {req_field} dans {allowed}, obtenu='{config.get(req_field)}'"
        return False, msg
    
    return True, "OK"


def evaluate_formula_constraint(config: Dict, constraint: Dict) -> Tuple[bool, str]:
    """Évalue une contrainte avec formule (quorum, fault tolerance)"""
    condition = constraint.get("condition", {})
    requires = constraint.get("requires", {})
    
    cond_field = condition.get("field")
    cond_value = condition.get("value")
    
    # Vérifier si la condition s'applique
    if config.get(cond_field) != cond_value:
        return True, "N/A"
    
    # Évaluer la formule
    formula = requires.get("formula")
    if formula:
        try:
            # Variables disponibles
            total_nodes = config.get("total_nodes", 0)
            quorum = config.get("quorum", 0)
            max_faults = config.get("max_faults", 0)
            
            # Évaluer selon le type de formule
            if "quorum >=" in formula:
                expected_quorum = (total_nodes // 2) + 1
                if quorum < expected_quorum:
                    msg = f"quorum={quorum} < floor({total_nodes}/2)+1={expected_quorum}"
                    return False, msg
            elif "total_nodes >=" in formula:
                min_nodes = 2 * max_faults + 1
                if total_nodes < min_nodes:
                    msg = f"total_nodes={total_nodes} < 2*max_faults+1={min_nodes}"
                    return False, msg
        except Exception as e:
            return False, f"Erreur d'évaluation de la formule : {e}"
    
    # Vérifier les opérateurs simples
    operator = requires.get("operator")
    if operator:
        field = requires.get("field")
        value = requires.get("value")
        value_from_field = requires.get("value_from_field")
        
        actual = config.get(field)
        
        if value_from_field:
            expected = config.get(value_from_field)
        else:
            expected = value
        
        if operator == ">=" and actual is not None and actual < expected:
            return False, f"{field}={actual} < {expected}"
        elif operator == "<=" and actual is not None and actual > expected:
            return False, f"{field}={actual} > {expected}"
    
    return True, "OK"


def validate_profile(profile_path: Path, rules: List[Dict]) -> Tuple[bool, List[Dict]]:
    """Valide un profil contre toutes les règles"""
    with open(profile_path) as f:
        profile = yaml.safe_load(f)
    
    config = profile.get("config", profile)  # Support both formats
    violations = []
    
    for constraint in rules:
        clause_id = constraint.get("clause_id")
        rule_id = constraint.get("rule_id")
        
        # Déterminer le type de contrainte
        if "formula" in constraint.get("requires", {}):
            ok, msg = evaluate_formula_constraint(config, constraint)
        else:
            ok, msg = evaluate_simple_constraint(config, constraint)
        
        if not ok and msg != "N/A":
            violations.append({
                "rule_id": rule_id,
                "clause_id": clause_id,
                "message": msg
            })
    
    return len(violations) == 0, violations


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_profiles.py <profile1.yaml> [profile2.yaml ...]")
        sys.exit(2)
    
    rules_path = Path("compatibility-rules-v2.yaml")
    if not rules_path.exists():
        print(f"ERROR: {rules_path} not found")
        sys.exit(2)
    
    rules = load_rules(rules_path)
    
    all_valid = True
    results = []
    
    for profile_path in sys.argv[1:]:
        path = Path(profile_path)
        if not path.exists():
            print(f"WARNING: {path} not found, skipping")
            continue
        
        valid, violations = validate_profile(path, rules)
        results.append({
            "profile": str(path),
            "valid": valid,
            "violations": violations
        })
        
        if not valid:
            all_valid = False
            print(f"❌ {path}: {len(violations)} violation(s)")
            for v in violations:
                print(f"   [{v['clause_id']}] {v['message']}")
        else:
            print(f"✅ {path}: OK")
    
    # Résumé
    print(f"\n{'='*60}")
    print(f"Total: {len(results)} profil(s) vérifié(s)")
    print(f"Validés: {sum(1 for r in results if r['valid'])}")
    print(f"Rejetés: {sum(1 for r in results if not r['valid'])}")
    
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
