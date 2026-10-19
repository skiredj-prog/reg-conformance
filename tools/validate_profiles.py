#!/usr/bin/env python3
"""
validate_profiles.py — Validation build-time des profils REG+.

Chaque profil dans profiles/*.yaml doit référencer une configuration
STRUCTURELLEMENT admissible du catalogue. Sinon le build échoue avec les
raisons de rejet. La garantie EFFECTIVE (capacité démontrée) est vérifiée
séparément, hors de ce script.

Usage : python3 tools/validate_profiles.py  (exit 0 si tous les profils sont admissibles)
"""

import glob
import json
import os
import sys

import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(BASE_DIR, "catalog", "valid-configurations-v1.json")
PROFILES_DIR = os.path.join(BASE_DIR, "profiles")
AXES = ("HOST_SCOPE", "DEDUP_LAYER", "CONCURRENCY", "UNCERTAINTY")


def load_catalog():
    with open(CATALOG, encoding="utf-8") as f:
        return json.load(f)


def admissibility(config: dict, catalog: dict) -> tuple:
    """Retourne (admissible: bool, violations: list)."""
    for c in catalog["configurations"]:
        if all(c["config"][ax] == config.get(ax) for ax in AXES):
            return c["admissible_structural"], c["violations"]
    return False, [{"message": f"configuration inconnue dans le catalogue : {config}"}]


def check_profile(path, catalog) -> list:
    """Retourne la liste des erreurs pour un profil (vide = OK)."""
    errors = []
    with open(path, encoding="utf-8") as f:
        profile = yaml.safe_load(f)
    name = os.path.basename(path)

    config = profile.get("config")
    if not config:
        return [f"{name} : section 'config' manquante (doit référencer les 4 axes)"]
    missing = [ax for ax in AXES if ax not in config]
    if missing:
        errors.append(f"{name} : axes manquants dans config : {missing}")
        return errors

    ok, violations = admissibility(config, catalog)
    if not ok:
        for v in violations:
            errors.append(f"{name} : config rejetée — {v.get('clause_id','?')} : {v['message']}")
    return errors


def main():
    catalog = load_catalog()
    profiles = sorted(glob.glob(os.path.join(PROFILES_DIR, "*.yaml")))
    if not profiles:
        print("Aucun profil trouvé dans profiles/ (rien à valider).")
        return 0

    all_errors = []
    for p in profiles:
        errs = check_profile(p, catalog)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"OK  {os.path.basename(p)}")

    if all_errors:
        print("\nÉCHEC de validation des profils :")
        for e in all_errors:
            print("  -", e)
        return 1
    print(f"\n{len(profiles)} profil(s) admissible(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
