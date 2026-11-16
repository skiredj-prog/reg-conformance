# Changelog

## Non publié — cohérence REG / REG+ / suite (novembre 2026)

Une seule version de chaque chose. Détail et état : `python tools/check_coherence.py`.

### Added

- `tools/check_coherence.py`, `coherence-baseline.json`, job CI `coherence` : compare les registres, les documents et les fichiers publiés ; échoue sur toute contradiction nouvelle.
- `README.md` : carte du dépôt (REG, suite de conformance, REG+, crosswalk) et couverture publiée par fondement.
- Crosswalk : six correspondances vecteur REG ↔ REG+ au statut `unverified`, avec citation et limite.
- `runner.py` : `summary_by_basis` dans le rapport (vecteurs spécifiés par les RFC gelées / identifiants hors RFC).
- `catalog/capabilities-v1.yaml` : registre `guarantee_records` des fiches de `capabilities/v1.0.0/`, avec `refines` et `applies_when`. `tools/fill_catalog_guarantees.py` lit ce registre au lieu de répéter la correspondance dans le code.
- `tools/verify_capabilities.py --source DIR` : une capacité démontrée dont la commande de test nomme un fichier absent de la source épinglée est rejetée. Exécuté dans le job `pinned-raft-conformance`.

### Changed

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
- Les preuves des profils datent de `tenir_governance` 5.5.0 et la validation indépendante du backend Raft de 5.6.1 : elles n'ont pas été rejouées sur la cible 5.7.0.

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
