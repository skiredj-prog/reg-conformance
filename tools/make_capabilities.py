#!/usr/bin/env python3
"""Génère capabilities/v1.0.0/*.json de façon déterministe.
--check : vérifie que les fichiers commités correspondent au générateur."""
import json, sys, argparse
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "capabilities" / "v1.0.0"
IMPL, TEST = "5.6.1", "0.6.0"
TS = "2026-10-21T07:29:00Z"  # horodatage release v5.6.1 (déterministe)
PH = "0" * 64  # placeholder : sera lié au hash CI réel en v0.6.1

def cap(cid, name, desc, inv, perimeter, demo, scope, cmd, limits, note):
    return {
        "capability_id": cid,
        "declaration": {
            "name": name, "description": desc,
            "invariants_required": inv, "deployment_perimeter": perimeter,
        },
        "evidence": {
            "implementation_version": IMPL, "test_version": TEST,
            "test_results_hash": PH, "test_command": cmd,
        },
        "demonstration_scope": scope,
        "status_note": note,
        "limitations": {"known_limits": limits},
        "validation": {
            "structural_admissibility": True,
            "effective_guarantee_demonstrated": demo,
            "verification_timestamp": TS,
        },
    }

MP = {"HOST_SCOPE": "mono-process", "CONCURRENCY": "thread-lock"}
MH = {"HOST_SCOPE": "mono-host", "CONCURRENCY": "file-lock"}
MX = {"HOST_SCOPE": "multi-host", "CONCURRENCY": "distributed-consensus"}

CAPS = [
    cap("cap-i8-budget-inproc", "Conservation budget mono-process",
        "reserved + committed <= capacity sous concurrence threadée.", ["I8"], MP,
        True, "production-equivalent",
        "pytest -q tests/test_budget_i8.py tests/test_hold_budget_regression.py",
        ["single-process only"], "Démontré : 9 chemins I8 (v5.4.2) + régressions v5.6.1."),
    cap("cap-i8-budget-crossproc", "Conservation budget cross-process",
        "I8 préservé entre processus via fcntl.flock + état durable.", ["I8"], MH,
        True, "production-equivalent",
        "pytest -q tests/test_cross_process_i8.py",
        ["single-host only (flock ne traverse pas les hôtes)"], "Démontré : 10 tests I8 cross-process (v5.5.0)."),
    cap("cap-i8-budget-raft", "Conservation budget Raft",
        "I8 préservé sur cluster Raft répliqué.", ["I8"], MX,
        True, "loopback-test-only",
        "pytest -q tests/raft/test_i8_raft.py",
        ["FM-20 ouvert : transport PySyncObj non sécurisé",
         "adresses loopback uniquement",
         "déploiement multi-host physique NON supporté"],
        "Démontré UNIQUEMENT en périmètre de test loopback (v5.6.1)."),
    cap("cap-deterministic-replication", "Réplication déterministe",
        "Même log => même état : horloge logique, IDs client-side, Decimal.", ["I8"], MX,
        True, "loopback-test-only",
        "pytest -q tests/raft/test_determinism.py",
        ["périmètre loopback"], "E1 corrigé : plus de time.time() répliqué."),
    cap("cap-dedup-local-registry", "Déduplication registre local",
        "Clé idempotente réclamée durablement avant évaluation ; replay = état réel.", ["I2"],
        {"HOST_SCOPE": "mono-host", "CONCURRENCY": "file-lock"},
        True, "production-equivalent",
        "pytest -q tests/test_idempotency.py",
        ["single-host"], "E5 corrigé : replay retourne RESERVED/COMMITTED/RELEASED réel."),
    cap("cap-dedup-provider-key", "Déduplication par clé provider",
        "Idempotence déléguée au provider externe.", ["I2"],
        {"HOST_SCOPE": "mono-host", "CONCURRENCY": "file-lock"},
        None, None,
        "n/a (preuve externe requise)",
        ["dépend des sémantiques du provider"], "NON évalué : exactement-once externe non prouvé."),
    cap("cap-dedup-consensus-registry", "Déduplication registre consensus",
        "Registre de déduplication répliqué via Raft.", ["I2"], MX,
        True, "loopback-test-only",
        "pytest -q tests/raft/test_registry.py",
        ["périmètre loopback", "FM-20"], "Démontré en test loopback."),
    cap("cap-i8-budget-disttx", "Conservation budget transaction distribuée",
        "I8 via backend distributed-transaction.", ["I8"],
        {"HOST_SCOPE": "multi-host", "CONCURRENCY": "distributed-transaction"},
        None, None, "n/a (aucune implémentation en 5.6.1)",
        ["slot structurel seulement"], "NON évalué : aucun backend implémenté."),
    cap("cap-linearizability-verification", "Vérification de linéarisabilité",
        "Preuve C1 par checker formel.", ["I8"], MX,
        False, None, "pytest -q tests/raft/test_linearizability.py",
        ["checker prototype (F-03)", "comparaison status-only", "specs raccourcies"],
        "RÉFUTÉ en l'état : ne pas citer comme preuve C1."),
    cap("cap-secure-consensus-transport", "Transport consensus sécurisé",
        "Chiffrement/authentification du transport Raft.", ["I8"], MX,
        False, None, "n/a",
        ["FM-20 ouvert", "pickle non authentifié"], "RÉFUTÉ : transport non durci."),
    cap("cap-byzantine-tolerance", "Tolérance byzantine",
        "Résistance aux nœuds malveillants.", ["I8"], MX,
        False, None, "n/a", ["Raft = crash-stop uniquement"], "RÉFUTÉ : hors périmètre."),
    cap("cap-exactly-once-external", "Exactly-once externe",
        "Un seul effet externe par décision.", ["I2"], MX,
        False, None, "n/a", ["états gouvernés seulement (UNKNOWN/HOLD)"],
        "RÉFUTÉ : gouverné, pas prouvé."),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    ok = True
    for c in CAPS:
        p = OUT / f"{c['capability_id']}.json"
        if args.check:
            if not p.exists() or json.loads(p.read_text()) != c:
                print(f"DRIFT: {p.name}")
                ok = False
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n")
            print(f"wrote {p.name}")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
