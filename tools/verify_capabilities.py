#!/usr/bin/env python3
"""
verify_capabilities.py
Vérifie que chaque capacité déclarée dans capabilities/v1.0.0/*.json :
1. Respecte le schéma capability-evidence-contract-v1.json
2. A structural_admissibility == true
3. Ses invariants_required sont définis dans catalog/capabilities-v1.yaml
   (normative_invariants). Un invariant cité mais non défini fait échouer.
4. Si effective_guarantee_demonstrated == true : test_results_hash doit être
   un hash réel (pas un placeholder de zéros) et verification_timestamp ne
   doit pas être dans le futur. Sinon la capacité échoue (fail-closed).

Limite : le hash n'est pas encore recalculé contre un fichier de preuve ;
ce contrôle rejette seulement les placeholders. Le contrôle SHA-256 fichier
est dans verify_effective_guarantees.py.

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
from datetime import datetime, timezone
import re
import yaml
from jsonschema import validate, ValidationError

PLACEHOLDER_HASH = "0" * 64


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


def load_defined_invariants():
    path = Path("catalog/capabilities-v1.yaml")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {inv["id"] for inv in data.get("normative_invariants", [])}


def check_effective_claim(cap):
    """Retourne une liste d'erreurs bloquantes pour une réclamation 'démontrée'."""
    errors = []
    v = cap["validation"]
    ts = datetime.fromisoformat(v["verification_timestamp"].replace("Z", "+00:00"))
    if ts > datetime.now(timezone.utc):
        errors.append(f"verification_timestamp dans le futur ({v['verification_timestamp']})")
    if v.get("effective_guarantee_demonstrated") is not True:
        return errors
    h = cap["evidence"]["test_results_hash"]
    if h == PLACEHOLDER_HASH or not re.fullmatch(r"[a-f0-9]{64}", h):
        errors.append("effective_guarantee_demonstrated=true avec test_results_hash placeholder")
    return errors


def main():
    schema = load_schema()
    capabilities_dir = Path("capabilities/v1.0.0")

    if not capabilities_dir.exists():
        print(f"ERROR: {capabilities_dir} not found")
        sys.exit(2)

    all_valid = True
    defined = load_defined_invariants()
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

        # 3. Invariants cités doivent être définis dans le catalogue
        undefined = [i for i in cap["declaration"]["invariants_required"] if i not in defined]
        if undefined:
            print(f"❌ invariant(s) non définis dans catalog/capabilities-v1.yaml : {undefined}")
            all_valid = False
            continue
        print("✅ invariants_required définis dans le catalogue")

        # 4. effective_guarantee_demonstrated (true / false / null)
        demo = cap["validation"].get("effective_guarantee_demonstrated")
        errs = check_effective_claim(cap)
        if errs:
            for e in errs:
                print(f"❌ {e}")
            all_valid = False
            continue
        if demo is True:
            print("✅ effective_guarantee_demonstrated = true (hash réel, horodatage cohérent)")
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
