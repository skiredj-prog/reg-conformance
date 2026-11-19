# Changelog

## Non publié

### Added

- **RFC-4 v0.3** (`reg-standards-baseline/rfc/rfc-4.md`, statut brouillon, la v0.2 reste le texte gelé jusqu'à ratification) : intègre RN-001. Borne fail-safe (τ_K sur un HOLD) contre âge du verdict, entrée épistémique (§2.3) ; résultat exigé sur dérive d'état (§2.2) ; reçu de suspension avec τ_K et condition de reprise (§3.2) ; CT-R4-014 à CT-R4-016 dans l'ensemble minimal (§5.2) ; réconciliation τ_K / âge du verdict (§7).

### Changed

- **CT-R4-004 réécrit** (RFC-4 v0.3 §5.2 item 4) : branche de refus du verdict périmé, dans `runner.py` et `harness/scenarios.py`. Commit accepté sans réadjudication enregistrée : `FAIL` ; refus `EVALUATION_EXPIRED` : `PASS` ; refus pour une autre raison : `INCONCLUSIVE` (auparavant `FAIL`). Résultats natif et HTTP inchangés (`PASS`).

## v0.7.0 — 2026-11-19

Cohérence REG / REG+ / suite, RN-001 inscrit dans le registre des vecteurs, harness neutre et `CLAIMS.md` en vigueur. Une seule version de chaque chose. Détail et état : `python tools/check_coherence.py`.

Ce que cette version ne contient pas : RFC-4 v0.3 (non ratifiée, pull request #78), le glossaire papier / suite et l'errata du manuscrit v7.2, une version 5.7.1 de TENIR-Gov. Aucune capacité n'est démontrée (0 sur 42 configurations admissibles) ; aucun résultat publié ne porte sur le runtime TENIR-Gov.

### Added

- **Suite v0.4.0** (`runner.py`, `spec.md`, `reg_common.py`) : 59 vecteurs au lieu de 56 (v0.3.2). Les rapports se distinguent ainsi de ceux de v0.6.x.
- `harness/` : port neutre (`RuntimePort`), scénarios écrits une fois, port de référence, port TENIR-Gov sur le chemin par défaut du gouverneur (correspondance des intentions et des refus provisoire, à confirmer par l'auteur du runtime), sondes d'effet `HX-EFFECT-001` à `004`, 17 contrôles de propriété, lecture par familles candidates `EGP-*` (non ratifiées). Workflow `REG Conformance - Run` (`conformance-run.yml`) et `tools/make_evidence_bundle.py` : une exécution, un paquet de preuve, `certifying: false`.
- `CLAIMS.md` en vigueur : règle d'admission du FLAG (RN-001 B1) et évaluations par des tiers (D2). `RESULTS.md` : exécutions publiées et en attente de confirmation.

- Vecteurs `CT-R4-014` (pas de dispatch sur un verdict périmé), `CT-R4-015` (l'âge n'améliore jamais une disposition) et `CT-R4-016` (une borne fail-safe refuse seule), enregistrés selon RN-001 §3 au statut `specified` ; le runner rend `IMPLEMENTATION_GAP` tant que les sondes n'existent pas. Le runner enregistre 59 identifiants au lieu de 56. `vectors/schema.json` accepte `superseded_by`.
- `reg-standards-baseline/notes/RN-001-flag-time-drift.md` : note ratifiée le 18 novembre 2026. FLAG avec condition = admission, FLAG sans condition = lacune ; borne fail-safe contre temps écoulé épistémique ; remplacement annoncé de CT-R4-004 ; résultat exigé pour C3 et CT-R4-005. Aucun résultat ni compte de vecteurs ne change.
- `tools/check_coherence.py`, `coherence-baseline.json`, job CI `coherence` : compare les registres, les documents et les fichiers publiés ; échoue sur toute contradiction nouvelle.
- `README.md` : carte du dépôt (REG, suite de conformance, REG+, crosswalk) et couverture publiée par fondement.
- Crosswalk : six correspondances vecteur REG ↔ REG+ au statut `unverified`, avec citation et limite.
- `runner.py` : `summary_by_basis` dans le rapport (vecteurs spécifiés par les RFC gelées / identifiants hors RFC).
- `catalog/capabilities-v1.yaml` : registre `guarantee_records` des fiches de `capabilities/v1.0.0/`, avec `refines` et `applies_when`. `tools/fill_catalog_guarantees.py` lit ce registre au lieu de répéter la correspondance dans le code.
- `tools/verify_capabilities.py --source DIR` : une capacité démontrée dont la commande de test nomme un fichier absent de la source épinglée est rejetée. Exécuté dans le job `pinned-raft-conformance`.

### Changed

- **TENIR-Gov épinglé une seule fois.** Le job `lifecycle` installait `b65efba`, un commit hors `main` de `tenir_governance` qui se déclare lui aussi 5.7.0 sans l'être (142 commits après le tag). Il lit maintenant `conformance-target.json` (5.7.0, `47ef67e`, tag `v5.7.0`) comme les jobs `pinned-raft-conformance` et `coherence`, et vérifie la version installée. `standard_version` du manifeste passe de `v0.5.1` à `v0.7.0`.
- Harness aligné sur RN-001 §4 : pour CT-R4-005, un commit refusé sous un autre libellé que `STATE_DRIFT`/`HARD_VETO` donne `INCONCLUSIVE`, plus `FAIL`, comme dans `runner.py`. CT-R4-014 à CT-R4-016 rattachés aux familles candidates `EGP-03`, `EGP-13` et `EGP-03` ; le port de référence rend pour eux le même `IMPLEMENTATION_GAP` que le runner.
- `RESULTS.md` : l'exécution de référence du 16 novembre a tourné sur une branche hors de cette version ; son lien est retiré en attendant une exécution sur le commit v0.7.0.
- **CT-R4-004 remplacé** par CT-R4-014 à CT-R4-016 (RN-001 §3) : `superseded_by` dans `vectors/commit.yaml` ; il reste enregistré avec son texte et ses résultats.
- **C3 et CT-R4-005 : résultat exigé** (RN-001 §4) : aucun effet, et la classe d'état rapportée (refus terminal, ou suspension avec condition de reprise déclarée). `HARD_VETO` n'est plus exigé. Les sondes ne reconnaissent encore que la branche `HARD_VETO` ; un commit refusé sous un autre libellé donne `INCONCLUSIVE`, plus `FAIL`, pour CT-R4-005 comme déjà pour C3. Aucun résultat publié ne change.
- **Invariant renommé : `I8` → `BUD`** (budget-ceiling-aggregate). Le manuscrit utilise `I8` pour un autre invariant (permanence de l'historique des tentatives). `tenir_governance` et les journaux de preuve antérieurs disent toujours `I8`. Les fiches `cap-i8-budget-*` deviennent `cap-budget-*`.
- **Propriétés du contrat de consensus renommées : `C1`, `C2`, `C3` → `SAF`, `LIV`, `FT`.** `C1` à `C5` désignent des vecteurs de la suite.
- **Quorum** : fusion de la pull request #33 (majorité `floor(n / 2) + 1`, validation du modèle de faute, cible épinglée). `resilience_bounds` du catalogue aligné sur le contrat corrigé.
- **Cible épinglée** : `conformance-target.json` passe à `tenir-governance` 5.7.0 (`47ef67e`). Le job installe l'extra `raft` de la cible.
- Catalogue des capacités : version 1.2.0.
- `specs/consensus-interface-v1.json` : la clé `invariants.I8` devient `invariants.BUD`.
- `capability-evidence-contract-v1.json` : `invariants_required` accepte les identifiants du catalogue (`BUD`, `LIN`, `AGR`, `I2`…), plus seulement `I<n>`.
- Vecteurs : `vectors/extended.yaml` réparé, statuts alignés sur `VECTORS.md`, résultats publiés identiques à ceux du runner, `vectors/dist/vectors.json` régénéré, 56 vecteurs et suite v0.3.2 partout. Les vecteurs lifecycle `CT-R4-011` à `CT-R4-013` indiquent leur fondement : manuscrit v7.2 §4.4, absent du texte gelé de RFC-4.

### Removed

- `validate_profiles.py` (racine), `compatibility-rules-v2.yaml`, `deployment-manifest.json` : doublons de `tools/validate_profiles.py`, `catalog/compatibility-rules-v1.yaml` et `conformance-target.json`. Les règles R4 à R6 de la v2 sont appliquées par `validate_fault_model` dans `tools/validate_profiles.py`.

### Fixed (vérification des capacités, fail-closed)

- `verify_capabilities.py` rejette désormais une capacité `effective_guarantee_demonstrated: true` dont `test_results_hash` est un placeholder (64 zéros ou non-hex).
- Rejet d'un `verification_timestamp` postérieur à l'instant de vérification.
- Rejet d'un invariant cité dans `invariants_required` absent de `normative_invariants` (`catalog/capabilities-v1.yaml`).

### Changed (capacités — décision de cohérence de preuve)

- Six capacités passent de `effective_guarantee_demonstrated: true` à `null` : `cap-i8-budget-inproc`, `cap-i8-budget-crossproc`, `cap-i8-budget-raft`, `cap-deterministic-replication`, `cap-dedup-local-registry`, `cap-dedup-consensus-registry`. Leur `test_results_hash` est un placeholder : aucune preuve n'est liée. Elles restent déclarées, avec la mention « non démontré ».
- Horodatage de vérification fixé à `2026-10-20T21:55:30Z` (les versions précédentes étaient dans le futur).
- `catalog/valid-configurations-v1.1.0.json` régénéré : les 42 configurations admissibles sont à `null` tant qu'une preuve n'est pas liée.
- `I2` (permit-single-use) ajouté à `normative_invariants` de `catalog/capabilities-v1.yaml`, définition importée du manuscrit v7.1. Sa vérification est à définir : aucun test de conformance ne l'exerce encore.

### Known issues

- `test_results_hash` des 12 capacités est un placeholder (zéros). `verify_capabilities.py` rejette les réclamations démontrées avec placeholder, mais ne recalcule pas encore le SHA-256 d'un fichier de preuve (rôle de `verify_effective_guarantees.py`).
- ~~`validate_profiles.py` signale `consensus-reference-single-host.yaml` comme configuration inconnue du catalogue.~~ Corrigé par la pull request #33 (voir plus haut).
- `verify_effective_guarantees.py` échoue sur `example-aggregate-budget.yaml` (attendu : preuves manquantes, cf. README).

---
- Sept fiches non démontrées nomment une commande de test qui n'existe ni dans `tenir_governance` 5.6.1 ni dans 5.7.0. Elles restent à `null`.
- Les preuves des profils datent de `tenir_governance` 5.5.0 et 5.6.0, et la validation indépendante du backend Raft de 5.6.1 : elles n'ont pas été rejouées sur la cible 5.7.0.
- `consensus-reference-single-host.yaml` : trois attestations citent `cap.concurrency.consensus-reference`, que la configuration `file-lock` ne réclame pas ; le vérificateur ne les compte pas.
- Trois fiches (`cap-budget-disttx`, `cap-dedup-local-registry`, `cap-dedup-provider-key`) sont rattachées à des configurations hors du périmètre qu'elles déclarent.

## v0.6.2 — 2026-11-18

Tag posé sur le commit `a2ec724` (30 octobre 2026), celui qui a été cité comme référence de la suite (56 vecteurs, Apache 2.0). v0.6.1 plus quatre commits :

- registre d'extériorité v0.2 (brouillon) et frontière de provenance HITL E2 (#46) ;
- JSON tranche 1 avec la séparation EV-001 ;
- synchronisation des sondes signées du cycle de vie T6–T8.

Limites de ce commit, dites plutôt que corrigées : le CHANGELOG du commit s'arrête à v0.5.1, il n'a pas de `conformance-target.json`, et l'invariant budgétaire s'y appelle encore `I8`. Le travail ultérieur de `main` n'en fait pas partie : il paraît en v0.7.0 (ci-dessus).

## v0.6.1 — 2026-10-21

### Added

- `capabilities/v1.0.0/raft-consensus-replication.json` : fiche du backend Raft, périmètre loopback, validée sur `tenir_governance` 5.6.1.

## v0.6.0 — 2026-10-20

### Added

- **Capability Evidence Contract v1.1.0** — `capability-evidence-contract-v1.json`
  - 12 capacités déclarées dans `capabilities/v1.0.0/`, avec `structural_admissibility` et `effective_guarantee_demonstrated` (true / false / null)
  - `tools/make_capabilities.py`, `tools/verify_capabilities.py`, `tools/fill_catalog_guarantees.py`
  - Workflow CI `.github/workflows/capabilities.yml`
  - `catalog/valid-configurations-v1.1.0.json`

## v0.5.1 — 2026-10-21

### Fixed (P0 Correctifs)

- **E2: Quorum formula** — Remplacé `quorum = f + 1` par `quorum = floor(total_nodes / 2) + 1`
  - Ajout de R4a, R4b dans `compatibility-rules-v2.yaml`
  - Validation automatique dans `validate_profiles.py`

- **E3: Fault model validation** — Ajout de la validation `fault_model`, `total_nodes`, `quorum`, `max_faults`
  - Ajout de R5a, R5b, R6a, R6b dans `compatibility-rules-v2.yaml`
  - `validate_profiles.py` rejette maintenant les profils avec quorum non majoritaire

- **E6: Harness version pinning** — Ajout de `deployment-manifest.json`
  - Le harnais vérifie maintenant `tenir_governance.__version__ == "5.6.1"`
  - Échec si version mismatch

- **E7: Test perimeter documentation** — Documentation complète dans `deployment-manifest.json`
  - Périmètre inclus/exclu explicitement listé
  - Commande de reproduction : `pytest -q tests/`
  - Limites connues documentées

### Changed

- `compatibility-rules-v1.yaml` → `compatibility-rules-v2.yaml` (ajout de 6 nouvelles clauses)
- `validate_profiles.py` étendu pour supporter les formules et opérateurs
- Catalogue bumpé à `catalog_version: "2.0.0"`

### Test Perimeter

**Included:**
- Unit tests: 697 tests
- Raft regression tests: 29 tests (Python 3.11 + 3.12)
- Backend integration tests: 122 tests
- **Total: 848 tests passing**

**Excluded:**
- Production multi-host network tests
- Byzantine fault tolerance
- Hardened transport security (FM-20 remains open)

**Known Limitations:**
- Raft tests are localhost only (loopback addresses)
- PySyncObj transport security not established
- Linearizability checker is a prototype (status-only comparison)

### Migration Guide

Si vous utilisez `compatibility-rules-v1.yaml` :

1. Remplacez par `compatibility-rules-v2.yaml`
2. Ajoutez les champs requis dans vos profils distribués :
   ```yaml
   fault_model: crash-stop
   total_nodes: 3  # ou 5, 7 (impair recommandé)
   quorum: 2       # floor(total_nodes / 2) + 1
   max_faults: 1   # max_faults <= total_nodes - quorum
   ```
3. Relancez `validate_profiles.py` pour vérifier la conformité

---

## v0.5.0 — 2026-10-15

Initial release avec `compatibility-rules-v1.yaml` et validation structurelle de base.
