#!/usr/bin/env python3
"""
test_catalog_enumeration.py — Vérification INDÉPENDANTE du catalogue.

Ne réutilise pas la logique de tools/enumerate_configs.py : il lit
catalog/valid-configurations-v1.json (artefact généré) et les sources YAML,
ré-énumère avec une implémentation minimale distincte, et vérifie :
  - total = 144, admissible = 42, rejetées = 102
  - breakdown par HOST_SCOPE = 9 / 18 / 15
  - toute configuration rejetée a ≥ 1 violation
  - toute configuration admissible a 0 violation
  - spot-checks de configurations connues (admissibles et rejetées)
  - les 144 configurations du JSON couvrent exactement le produit cartésien
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

EXPECTED_TOTAL = 144
EXPECTED_ADMISSIBLE = 42
EXPECTED_REJECTED = 102
EXPECTED_BREAKDOWN = {"mono-process": 9, "mono-host": 18, "multi-host": 15}


def load_yaml(name):
    with open(os.path.join(CATALOG_DIR, name), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def independent_violations(config, constraints):
    """Implémentation minimale distincte du générateur."""
    v = []
    for c in constraints:
        if config[c["condition"]["field"]] == c["condition"]["value"]:
            if config[c["requires"]["field"]] not in c["requires"]["allowed_values"]:
                v.append(c["clause_id"])
    return v


def main():
    failures = []

    hypotheses = load_yaml("hypotheses-v1.yaml")
    rules = load_yaml("compatibility-rules-v1.yaml")
    axes = hypotheses["axes"]
    constraints = rules["constraints"]

    with open(os.path.join(CATALOG_DIR, "valid-configurations-v1.json"), encoding="utf-8") as f:
        generated = json.load(f)

    cfgs = generated["configurations"]

    # 1. Comptages
    s = generated["summary"]
    for label, got, exp in [
        ("total", s["total"], EXPECTED_TOTAL),
        ("admissible", s["admissible_structural"], EXPECTED_ADMISSIBLE),
        ("rejected", s["rejected"], EXPECTED_REJECTED),
    ]:
        if got != exp:
            failures.append(f"summary.{label}={got}, attendu {exp}")

    bd = s["breakdown_by_host_scope"]
    for host, exp in EXPECTED_BREAKDOWN.items():
        if bd.get(host) != exp:
            failures.append(f"breakdown[{host}]={bd.get(host)}, attendu {exp}")

    # 2. Couverture exacte du produit cartésien
    keys = list(axes.keys())
    product = set(
        tuple(dict(zip(keys, vals))[k] for k in keys)
        for vals in itertools.product(*[axes[k]["values"] for k in keys])
    )
    seen = set(tuple(c["config"][k] for k in keys) for c in cfgs)
    if seen != product:
        failures.append(f"Couverture produit cartésien incorrecte : "
                        f"{len(seen)} vues vs {len(product)} attendues")

    # 3. Cohérence interne : violations cohérentes avec admissible_structural
    for c in cfgs:
        n = len(c["violations"])
        if c["admissible_structural"] and n != 0:
            failures.append(f"{c['config']} marqué admissible avec {n} violation(s)")
        if not c["admissible_structural"] and n == 0:
            failures.append(f"{c['config']} marqué rejeté sans violation")

    # 4. Indépendance : recalcul avec l'autre implémentation
    independent_admissible = 0
    independent_bd = {}
    mismatch = 0
    for vals in itertools.product(*[axes[k]["values"] for k in keys]):
        config = dict(zip(keys, vals))
        v = independent_violations(config, constraints)
        if not v:
            independent_admissible += 1
            h = config["HOST_SCOPE"]
            independent_bd[h] = independent_bd.get(h, 0) + 1
        # comparaison avec le JSON
        gen = next(c for c in cfgs if all(c["config"][k] == config[k] for k in keys))
        gen_clauses = set(viol["clause_id"] for viol in gen["violations"])
        if gen_clauses != set(v):
            mismatch += 1
    if independent_admissible != EXPECTED_ADMISSIBLE:
        failures.append(f"Recalcul indépendant donne {independent_admissible} admissibles")
    if independent_bd != EXPECTED_BREAKDOWN:
        failures.append(f"Recalcul indépendant breakdown={independent_bd}")
    if mismatch:
        failures.append(f"{mismatch} configuration(s) avec violations divergentes")

    # 5. Spot-checks connus
    def cfg_of(**kw):
        base = {k: axes[k]["values"][0] for k in keys}
        base.update(kw)
        return base

    spot_admissible = [
        cfg_of(HOST_SCOPE="multi-host", CONCURRENCY="distributed-consensus",
               DEDUP_LAYER="distributed-consensus-registry", UNCERTAINTY="fail-closed"),
        cfg_of(HOST_SCOPE="mono-process", CONCURRENCY="thread-lock", DEDUP_LAYER="none"),
    ]
    spot_rejected = [
        (cfg_of(HOST_SCOPE="mono-process", CONCURRENCY="file-lock"), "R1a"),
        (cfg_of(HOST_SCOPE="mono-host", CONCURRENCY="distributed-consensus"), "R1b"),
        (cfg_of(HOST_SCOPE="mono-host", DEDUP_LAYER="distributed-consensus-registry"), "R2b"),
        (cfg_of(HOST_SCOPE="multi-host", DEDUP_LAYER="local-registry"), "R3a"),
    ]
    for c in spot_admissible:
        gen = next(x for x in cfgs if all(x["config"][k] == c[k] for k in keys))
        if not gen["admissible_structural"]:
            failures.append(f"Spot-check admissible rejeté à tort : {c}")
    for c, expected_clause in spot_rejected:
        gen = next(x for x in cfgs if all(x["config"][k] == c[k] for k in keys))
        clauses = set(v["clause_id"] for v in gen["violations"])
        if gen["admissible_structural"] or expected_clause not in clauses:
            failures.append(f"Spot-check rejeté mal classé : {c} (attendu {expected_clause})")

    if failures:
        print("ÉCHECS :")
        for f_ in failures:
            print("  -", f_)
        sys.exit(1)
    print(f"OK : {EXPECTED_TOTAL} configurations, {EXPECTED_ADMISSIBLE} admissibles, "
          f"{EXPECTED_REJECTED} rejetées, breakdown {EXPECTED_BREAKDOWN}. Tous les spot-checks passent.")


if __name__ == "__main__":
    main()
