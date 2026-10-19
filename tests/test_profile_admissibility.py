#!/usr/bin/env python3
"""
test_profile_admissibility.py — Vérifie le branchement de la validation des profils.

Indépendant : réutilise la fonction admissibility() de validate_profiles.py
mais teste des configs connues en dur, pas seulement le profil exemple.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from validate_profiles import admissibility, check_profile, load_catalog, AXES

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    failures = []
    catalog = load_catalog()

    # 1. Le profil exemple est admissible
    errs = check_profile(os.path.join(BASE_DIR, "profiles", "example-aggregate-budget.yaml"), catalog)
    if errs:
        failures.append(f"profil exemple rejeté à tort : {errs}")

    # 2. Configs connues admissibles
    admissible = [
        {"HOST_SCOPE": "mono-process", "DEDUP_LAYER": "none", "CONCURRENCY": "thread-lock", "UNCERTAINTY": "fail-open"},
        {"HOST_SCOPE": "multi-host", "DEDUP_LAYER": "distributed-consensus-registry",
         "CONCURRENCY": "distributed-consensus", "UNCERTAINTY": "fail-closed"},
    ]
    for c in admissible:
        ok, v = admissibility(c, catalog)
        if not ok:
            failures.append(f"config connue admissible rejetée : {c} → {v}")

    # 3. Configs connues rejetées, avec la clause attendue
    rejected = [
        ({"HOST_SCOPE": "mono-process", "DEDUP_LAYER": "none", "CONCURRENCY": "file-lock", "UNCERTAINTY": "fail-closed"}, "R1a"),
        ({"HOST_SCOPE": "mono-host", "DEDUP_LAYER": "distributed-consensus-registry",
          "CONCURRENCY": "distributed-transaction", "UNCERTAINTY": "fail-closed"}, "R2c"),
        ({"HOST_SCOPE": "multi-host", "DEDUP_LAYER": "local-registry", "CONCURRENCY": "distributed-transaction",
          "UNCERTAINTY": "human-escalation"}, "R3a"),
    ]
    for c, expected_clause in rejected:
        ok, violations = admissibility(c, catalog)
        clauses = {v.get("clause_id") for v in violations}
        if ok or expected_clause not in clauses:
            failures.append(f"config connue rejetée mal classée : {c} (attendu {expected_clause}, obtenu {clauses})")

    if failures:
        print("ÉCHECS :")
        for f_ in failures:
            print("  -", f_)
        sys.exit(1)
    print("OK profile_admissibility : profil exemple + 2 admissibles + 3 rejetées (clauses vérifiées).")


if __name__ == "__main__":
    main()
