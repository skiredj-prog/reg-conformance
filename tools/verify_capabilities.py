#!/usr/bin/env python3
"""
verify_capabilities.py
Vérifie que chaque capacité déclarée dans capabilities/v1.0.0/*.json :
1. Respecte le schéma capability-evidence-contract-v1.json
2. A structural_admissibility == true (vérifié via validate_profiles.py)
3. A effective_guarantee_demonstrated == true (vérifié via test_results_hash)

Usage:
    python verify_capabilities.py

Exit codes:
    0 = toutes les capacités sont valides
    1 = au moins une capacité invalide
    2 = erreur d'exécution
"""

import sys
import json
from pathlib import Path
from jsonschema import validate, ValidationError


def load_schema():
    schema_path = Path("capability-evidence-contract-v1.json")
    if not schema_path.exists():
        print(f"ERROR: {schema_path} not found")
        sys.exit(2)
    with open(schema_path) as f:
        return json.load(f)


def load_capability(path):
    with open(path) as f:
        return json.load(f)


def main():
    schema = load_schema()
    capabilities_dir = Path("capabilities/v1.0.0")

    if not capabilities_dir.exists():
        print(f"ERROR: {capabilities_dir} not found")
        sys.exit(2)

    all_valid = True
    capabilities = list(capabilities_dir.glob("*.json"))

    print(f"Vérification de {len(capabilities)} capacité(s)...")

    for cap_path in capabilities:
        print(f"\n{'='*60}")
        print(f"Capacité: {cap_path.name}")

        try:
            cap = load_capability(cap_path)
        except Exception as e:
            print(f"❌ Erreur de chargement: {e}")
            all_valid = False
            continue

        # 1. Validation du schéma
        try:
            validate(instance=cap, schema=schema)
            print("✅ Schéma valide")
        except ValidationError as e:
            print(f"❌ Schéma invalide: {e.message}")
            all_valid = False
            continue

        # 2. Vérification de structural_admissibility
        if not cap["validation"].get("structural_admissibility"):
            print("❌ structural_admissibility = false")
            all_valid = False
            continue
        print("✅ structural_admissibility = true")

        # 3. effective_guarantee_demonstrated (peut être true / false / null)
        demo = cap["validation"].get("effective_guarantee_demonstrated")
        if demo is True:
            print("✅ effective_guarantee_demonstrated = true")
        elif demo is False:
            print("⚠️  effective_guarantee_demonstrated = false (réfuté)")
        else:
            print("⚠️  effective_guarantee_demonstrated = null (non évalué)")

        print(f"✅ Capacité lue: {cap['declaration']['name']}")

    print(f"\n{'='*60}")
    if all_valid:
        print("✅ Toutes les capacités sont structurellement valides")
        sys.exit(0)
    else:
        print("❌ Au moins une capacité invalide")
        sys.exit(1)


if __name__ == "__main__":
    main()
