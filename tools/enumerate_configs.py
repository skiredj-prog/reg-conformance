#!/usr/bin/env python3
"""
enumerate_configs.py — Générateur de référence du catalogue REG+.

Lit catalog/hypotheses-v1.yaml (axes fermés) et catalog/compatibility-rules-v1.yaml
(règles déclaratives), énumère le produit cartésien et produit
catalog/valid-configurations-v1.json.

Corrections par rapport à la version initiale :
  1. validate_config retourne TOUTES les violations (liste), pas la première.
  2. validate_catalog auto-valide le catalogue lui-même (champs référencés,
     valeurs autorisées, unicité des clause_id).
  3. Distinction structurel / effectif : le générateur ne calcule que
     l'admissibilité STRUCTURELLE. La garantie effective (capacité démontrée
     par l'implémentation) est vérifiée séparément au build.
"""

import itertools
import json
import os
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML requis : pip install pyyaml\n")
    sys.exit(2)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_DIR = os.path.join(BASE_DIR, "catalog")


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_catalog(axes, constraints):
    """Auto-valide le catalogue : champs référencés, valeurs, unicité des clause_id."""
    errors = []
    axis_names = set(axes.keys())

    # 1. Chaque règle référence des axes existants et des valeurs autorisées.
    clause_ids = set()
    for c in constraints:
        rid = c.get("rule_id", "<sans rule_id>")
        cid = c.get("clause_id")
        if cid is None:
            errors.append(f"Règle {rid} : clause_id manquant.")
            continue
        if cid in clause_ids:
            errors.append(f"clause_id dupliqué : {cid} (règle {rid}).")
        clause_ids.add(cid)

        cond = c.get("condition", {})
        req = c.get("requires", {})
        for label, node in (("condition", cond), ("requires", req)):
            field = node.get("field")
            if field not in axis_names:
                errors.append(
                    f"Clause {cid} ({rid}) : {label}.field='{field}' "
                    f"n'existe pas dans les axes {sorted(axis_names)}."
                )
        # Valeurs autorisées ⊆ valeurs de l'axe cible.
        req_field = req.get("field")
        if req_field in axis_names:
            allowed = set(req.get("allowed_values", []))
            declared = set(axes[req_field]["values"])
            unknown = allowed - declared
            if unknown:
                errors.append(
                    f"Clause {cid} ({rid}) : allowed_values contient des valeurs "
                    f"non déclarées pour {req_field} : {sorted(unknown)}."
                )
        cond_field = cond.get("field")
        if cond_field in axis_names:
            cond_val = cond.get("value")
            declared = set(axes[cond_field]["values"])
            if cond_val not in declared:
                errors.append(
                    f"Clause {cid} ({rid}) : condition.value='{cond_val}' non déclarée "
                    f"pour {cond_field}."
                )

    if errors:
        raise ValueError("Catalogue invalide :\n  - " + "\n  - ".join(errors))


def validate_config(config, constraints):
    """Retourne la LISTE de toutes les violations applicables (vide = admissible)."""
    violations = []
    for c in constraints:
        cond = c["condition"]
        req = c["requires"]
        if config.get(cond["field"]) == cond["value"]:
            actual = config.get(req["field"])
            if actual not in req["allowed_values"]:
                violations.append({
                    "rule_id": c["rule_id"],
                    "clause_id": c["clause_id"],
                    "message": (
                        f"{cond['field']}={cond['value']} exige {req['field']} dans "
                        f"{req['allowed_values']}, obtenu={actual!r}"
                    ),
                })
    return violations


def main():
    hypotheses = load_yaml(os.path.join(CATALOG_DIR, "hypotheses-v1.yaml"))
    rules = load_yaml(os.path.join(CATALOG_DIR, "compatibility-rules-v1.yaml"))

    axes = hypotheses["axes"]
    constraints = rules["constraints"]

    # Auto-validation du catalogue (échoue fort si le catalogue est incohérent).
    validate_catalog(axes, constraints)

    keys = list(axes.keys())
    values_lists = [axes[k]["values"] for k in keys]

    configurations = []
    breakdown = {}  # HOST_SCOPE -> count admissible

    for values in itertools.product(*values_lists):
        config = dict(zip(keys, values))
        violations = validate_config(config, constraints)
        admissible_structural = len(violations) == 0

        host = config["HOST_SCOPE"]
        if admissible_structural:
            breakdown[host] = breakdown.get(host, 0) + 1

        configurations.append({
            "config": config,
            "admissible_structural": admissible_structural,
            "effective_guarantee_demonstrated": None,  # vérifié séparément au build
            "violations": violations,
        })

    total = len(configurations)
    valid = sum(1 for c in configurations if c["admissible_structural"])
    rejected = total - valid

    print(f"Total théorique        : {total}")
    print(f"Admissibles (structurel) : {valid}")
    print(f"Rejetées                 : {rejected}")
    print("Breakdown par HOST_SCOPE :")
    for host in axes["HOST_SCOPE"]["values"]:
        print(f"  {host:<15} {breakdown.get(host, 0)}")

    out = {
        "catalog_version": hypotheses["version"],
        "rules_version": rules["version"],
        "note": (
            "admissible_structural = cohérence structurelle uniquement. "
            "effective_guarantee_demonstrated est vérifié séparément au build "
            "contre les capacités démontrées par l'implémentation."
        ),
        "summary": {
            "total": total,
            "admissible_structural": valid,
            "rejected": rejected,
            "breakdown_by_host_scope": breakdown,
        },
        "configurations": configurations,
    }

    out_path = os.path.join(CATALOG_DIR, "valid-configurations-v1.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\nFichier généré : {out_path}")


if __name__ == "__main__":
    main()
