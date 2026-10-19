#!/usr/bin/env python3
"""
test_effective_guarantees.py — Garantie EFFECTIVE : preuves réelles, pas des déclarations.

Chaque scénario construit ses preuves dans un répertoire temporaire (base_dir),
avec des hashs calculés à l'exécution. Aucune preuve n'est fabriquée dans le dépôt.

Scénarios :
  1. Profil entièrement attesté (preuves présentes, hashs corrects) → accepté
  2. Preuve requise absente de la liste → rejeté (cible la capacité / preuve)
  3. verified=false → rejeté
  4. evidence_ref vide → rejeté
  5. Config structurellement admissible sans attestation → rejeté
  6. Attestation superflue (preuve réelle, non réclamée) → avertissement seulement
  7. Fichier de preuve absent → rejeté
  8. Fichier altéré après attestation (hash différent) → rejeté
  9. evidence_sha256 absent → rejeté
 10. evidence_ref absolu → rejeté
 11. evidence_ref avec '..' → rejeté
 12. Profil exemple du dépôt (aucune preuve fournie) → rejeté, preuves manquantes listées
 13. Profil mono-hôte : preuves de test réelles acceptées ; seul deployment.manifest manque
"""

import copy
import hashlib
import os
import shutil
import sys
import tempfile

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))
from verify_effective_guarantees import check_profile, load_capabilities, required_evidence  # noqa: E402

EXAMPLE = os.path.join(BASE_DIR, "profiles", "example-aggregate-budget.yaml")
CONFIG = {"HOST_SCOPE": "multi-host", "DEDUP_LAYER": "distributed-consensus-registry",
          "CONCURRENCY": "distributed-consensus", "UNCERTAINTY": "fail-closed"}


def build_attested(workdir, caps, config):
    """Crée les preuves réelles et le profil entièrement attesté dans workdir."""
    required, _ = required_evidence(config, caps)
    by_ev = {}
    for cid, ev in sorted(required):
        by_ev.setdefault(ev, []).append(cid)
    ev_dir = os.path.join(workdir, "evidence")
    os.makedirs(ev_dir, exist_ok=True)
    attestations = []
    for ev, cids in sorted(by_ev.items()):
        rel = f"evidence/{ev}.txt"
        full = os.path.join(workdir, rel)
        with open(full, "w", encoding="utf-8") as f:
            f.write(f"preuve de test pour {ev}\n")
        attestations.append({
            "capability_ids": sorted(set(cids)), "evidence_type": ev,
            "evidence_ref": rel, "evidence_sha256": sha256(full),
            "verified": True, "verifier": "test-harness", "verified_at": "2026-10-19",
        })
    profile = {"profile_id": "attested", "config": config, "attestations": attestations}
    path = os.path.join(workdir, "attested.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(profile, f)
    return path, profile


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_profile(workdir, profile, name="p.yaml"):
    path = os.path.join(workdir, name)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(profile, f)
    return path


def main():
    failures = []
    caps = load_capabilities()
    work = tempfile.mkdtemp(prefix="effg_")
    try:
        path, base_profile = build_attested(work, caps, CONFIG)

        # 1. Entièrement attesté, preuves réelles → accepté
        errs, warns = check_profile(path, caps, base_dir=work)
        if errs:
            failures.append(f"1. profil attesté rejeté : {errs}")

        def expect_error(label, profile, needle=None):
            p = write_profile(work, profile, name=f"{label}.yaml")
            errs, _ = check_profile(p, caps, base_dir=work)
            if not errs:
                failures.append(f"{label}. accepté à tort")
            elif needle and not any(needle in e for e in errs):
                failures.append(f"{label}. erreur attendue absente ({needle!r}) : {errs}")

        # 2. Preuve requise retirée → rejet ciblé
        p2 = copy.deepcopy(base_profile)
        p2["attestations"] = [a for a in p2["attestations"] if a["evidence_type"] != "test.fault-tolerance"]
        expect_error("2", p2, "test.fault-tolerance")

        # 3. verified=false
        p3 = copy.deepcopy(base_profile)
        p3["attestations"][0]["verified"] = False
        expect_error("3", p3, "verified=false")

        # 4. evidence_ref vide
        p4 = copy.deepcopy(base_profile)
        p4["attestations"][0]["evidence_ref"] = ""
        expect_error("4", p4, "evidence_ref vide")

        # 5. Structurellement admissible, aucune attestation
        bare = {"profile_id": "bare", "config": {"HOST_SCOPE": "mono-process", "DEDUP_LAYER": "none",
                "CONCURRENCY": "thread-lock", "UNCERTAINTY": "fail-closed"}, "attestations": []}
        expect_error("5", bare, "manquante")

        # 6. Attestation superflue, preuve réelle → avertissement seulement
        extra_rel = "evidence/extra.txt"
        with open(os.path.join(work, extra_rel), "w", encoding="utf-8") as f:
            f.write("preuve superflue\n")
        p6 = copy.deepcopy(base_profile)
        p6["attestations"].append({
            "capability_ids": ["cap.uncertainty.fail-open"], "evidence_type": "test.unknown-outcome.proceeds",
            "evidence_ref": extra_rel, "evidence_sha256": sha256(os.path.join(work, extra_rel)),
            "verified": True, "verifier": "test-harness", "verified_at": "2026-10-19",
        })
        p6path = write_profile(work, p6, name="p6.yaml")
        errs, warns = check_profile(p6path, caps, base_dir=work)
        if errs:
            failures.append(f"6. superflue traitée en erreur : {errs}")
        if not warns:
            failures.append("6. superflue non signalée")

        # 7. Fichier de preuve absent
        p7 = copy.deepcopy(base_profile)
        p7["attestations"][0]["evidence_ref"] = "evidence/does-not-exist.txt"
        expect_error("7", p7, "absent")

        # 8. Fichier altéré après attestation
        p8 = copy.deepcopy(base_profile)
        victim = os.path.join(work, p8["attestations"][0]["evidence_ref"])
        original = open(victim, encoding="utf-8").read()
        with open(victim, "a", encoding="utf-8") as f:
            f.write("altération\n")
        expect_error("8", p8, "hash ne correspond pas")
        with open(victim, "w", encoding="utf-8") as f:
            f.write(original)  # restaure pour les scénarios suivants

        # 9. evidence_sha256 absent
        p9 = copy.deepcopy(base_profile)
        del p9["attestations"][0]["evidence_sha256"]
        expect_error("9", p9, "evidence_sha256")

        # 10. Chemin absolu
        p10 = copy.deepcopy(base_profile)
        p10["attestations"][0]["evidence_ref"] = os.path.join(work, "evidence", "test.consensus.safety.txt")
        expect_error("10", p10, "absolu")

        # 11. Traversée de répertoire
        p11 = copy.deepcopy(base_profile)
        p11["attestations"][0]["evidence_ref"] = "../../etc/passwd"
        expect_error("11", p11, "hors du dépôt")

        # 12. Profil exemple du dépôt : aucune preuve fournie → rejet
        errs, _ = check_profile(EXAMPLE, caps)
        if not errs or not any("preuve" in e and "manquante" in e for e in errs):
            failures.append(f"12. profil exemple non rejeté avec preuves manquantes : {errs}")

        # 13. Profil mono-hôte réel : preuves de test attestées (hash vérifié),
        #     seule preuve manquante = deployment.manifest (non produisible ici)
        single = os.path.join(BASE_DIR, "profiles", "example-aggregate-budget-single-host.yaml")
        errs, _ = check_profile(single, caps)
        if len(errs) != 1 or "cap.host.single-host" not in errs[0] or "deployment.manifest" not in errs[0]:
            failures.append(f"13. profil mono-hôte : écart inattendu {errs}")
        if any("hash" in e or "absent" in e or "hors du dépôt" in e for e in errs):
            failures.append(f"13. preuve de test réelle rejetée {errs}")

    finally:
        shutil.rmtree(work, ignore_errors=True)

    if failures:
        print("ÉCHECS :")
        for f_ in failures:
            print("  -", f_)
        sys.exit(1)
    print("OK effective_guarantees : 13 scénarios passent (preuves réelles, hash, chemins, "
          "structurel≠effectif, exemple non attesté rejeté).")


if __name__ == "__main__":
    main()
