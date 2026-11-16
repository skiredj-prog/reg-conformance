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


def missing_test_files(cap, source):
    """Fichiers de test nommés par test_command et absents de la source donnée."""
    import re
    files = re.findall(r"[\w./-]+\.py", cap["evidence"].get("test_command", ""))
    return [f for f in files if not (Path(source) / f).is_file()]


def main():
    # --source DIR : arbre de l'implémentation épinglée (conformance-target.json).
    # Une capacité « démontrée » dont la commande nomme un fichier absent de cet
    # arbre est invalide ; pour les autres, l'absence est signalée sans bloquer.
    source = None
    if "--source" in sys.argv:
        position = sys.argv.index("--source") + 1
        if position >= len(sys.argv):
            print("ERROR: --source requires DIR")
            sys.exit(2)
        source = sys.argv[position]
    try:
        target_version = json.loads(Path("conformance-target.json").read_text(encoding="utf-8"))["implementation"]["version"]
    except (OSError, KeyError, TypeError, ValueError):
        target_version = None
    if not isinstance(target_version, str) or not target_version:
        print("ERROR: conformance-target.json illisible ou sans implementation.version : la cible déclarée ne peut pas être établie")
        sys.exit(2)
    not_runnable = []
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
            shown_on = cap["evidence"].get("implementation_version")
            if target_version and shown_on != target_version:
                print(f"⚠️  démontrée sur {shown_on} ; la cible déclarée est {target_version} : non rejouée sur la cible")
        elif demo is False:
            print("⚠️  effective_guarantee_demonstrated = false (réfuté)")
        else:
            print("⚠️  effective_guarantee_demonstrated = null (non évalué)")

        if source:
            absent = missing_test_files(cap, source)
            if absent and demo is True:
                print(f"❌ démontrée, mais test_command nomme des fichiers absents de la source : {', '.join(absent)}")
                all_valid = False
                continue
            if absent:
                not_runnable.append((cap["capability_id"], absent))
                print(f"⚠️  test_command non exécutable sur la source épinglée : {', '.join(absent)}")

        print(f"✅ Capacité lue: {cap['declaration']['name']}")

    print(f"\n{'='*60}")
    if not_runnable:
        print(f"⚠️  {len(not_runnable)} capacité(s) non démontrée(s) nomment une commande de test "
              f"qui n'existe pas dans la source épinglée : {', '.join(sorted(c for c, _ in not_runnable))}")
    if all_valid:
        print("✅ Toutes les capacités sont structurellement valides")
        sys.exit(0)
    else:
        print("❌ Au moins une capacité invalide")
        sys.exit(1)


if __name__ == "__main__":
    main()
