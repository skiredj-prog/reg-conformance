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


def validate_fault_model(profile: dict) -> tuple[list, list]:
    """Validate declared distributed-consensus fault assumptions.

    The current Raft profile supports crash-stop faults only. Byzantine and
    omission tolerance are not inferred from the generic catalog.
    Returns (blocking_errors, warnings).
    """
    config = profile.get("config") or {}
    if config.get("CONCURRENCY") != "distributed-consensus":
        return [], []

    errors, warnings = [], []
    model = profile.get("fault_model")
    if not isinstance(model, dict):
        return ["MISSING_OR_INVALID_FAULT_MODEL"], warnings

    required = ("crash", "byzantine", "omission", "quorum", "total_nodes")
    missing = [key for key in required if key not in model]
    if missing:
        return [f"MISSING_FAULT_MODEL_FIELDS:{','.join(missing)}"], warnings

    values = {}
    for key in required:
        value = model.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append(f"FAULT_MODEL_FIELD_MUST_BE_INTEGER:{key}")
        else:
            values[key] = value
    if errors:
        return errors, warnings

    for key in ("crash", "byzantine", "omission"):
        if values[key] < 0:
            errors.append(f"FAULT_COUNT_MUST_BE_NON_NEGATIVE:{key}")
    if values["total_nodes"] < 3:
        errors.append("DISTRIBUTED_CONSENSUS_REQUIRES_AT_LEAST_3_NODES")
    if values["quorum"] < 1:
        errors.append("QUORUM_MUST_BE_POSITIVE")
    if values["quorum"] > values["total_nodes"]:
        errors.append("QUORUM_GREATER_THAN_TOTAL_NODES")

    # The currently supported Raft implementation is crash-stop only.
    if values["byzantine"] != 0 or values["omission"] != 0:
        errors.append("UNSUPPORTED_FAULT_MODEL:crash-stop-only")

    n, q, f = values["total_nodes"], values["quorum"], values["crash"]
    if n >= 1:
        majority = n // 2 + 1
        if q < majority:
            errors.append(f"QUORUM_TOO_SMALL:expected>={majority},got={q}")
        elif q != majority:
            errors.append(f"QUORUM_MUST_EQUAL_MAJORITY:expected={majority},got={q}")
        if f > n - q:
            errors.append(
                "NOT_ENOUGH_NODES_FOR_DECLARED_FAULTS:"
                f"total_nodes={n},quorum={q},crash={f}"
            )
        if n % 2 == 0:
            warnings.append("EVEN_TOTAL_NODES_NOT_RECOMMENDED")
    return errors, warnings


def check_profile(path, catalog) -> list:
    """Retourne la liste des erreurs pour un profil (vide = OK)."""
    errors = []
    with open(path, encoding="utf-8") as f:
        profile = yaml.safe_load(f)
    name = os.path.basename(path)

    config = profile.get("config")
    if not config:
        return [f"{name} : section 'config' manquante (doit référencer les 4 axes)"]
    fault_errors, fault_warnings = validate_fault_model(profile)
    errors.extend(f"{name} : {error}" for error in fault_errors)
    errors.extend(f"{name} : WARNING {warning}" for warning in fault_warnings)
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
