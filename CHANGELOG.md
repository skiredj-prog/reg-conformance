# Changelog

## v0.6.0 — 2026-10-20 (non publié, branche fix/capability-evidence-verification)

### Added

- **Capability Evidence Contract v1.1.0** — `capability-evidence-contract-v1.json`
  - 12 capacités déclarées dans `capabilities/v1.0.0/`, avec `structural_admissibility` et `effective_guarantee_demonstrated` (true / false / null)
  - `tools/make_capabilities.py`, `tools/verify_capabilities.py`, `tools/fill_catalog_guarantees.py`
  - Workflow CI `.github/workflows/capabilities.yml`
  - `catalog/valid-configurations-v1.1.0.json`

### Fixed (vérification des capacités, fail-closed)

- `verify_capabilities.py` rejette désormais une capacité `effective_guarantee_demonstrated: true` dont `test_results_hash` est un placeholder (64 zéros ou non-hex).
- Rejet d'un `verification_timestamp` postérieur à l'instant de vérification.
- Rejet d'un invariant cité dans `invariants_required` absent de `normative_invariants` (`catalog/capabilities-v1.yaml`).

### Known issues

- Les 12 fichiers de capacités ont tous `test_results_hash` à zéros (placeholder produit par `make_capabilities.py`). Ce contrôle ne vérifie pas encore un SHA-256 de fichier de preuve.
- `I2` est cité par 4 capacités (`cap-dedup-*`, `cap-exactly-once-external`) mais n'est pas défini dans `normative_invariants`.
- Les 6 capacités déclarées démontrées (`cap-i8-budget-inproc`, `cap-i8-budget-crossproc`, `cap-i8-budget-raft`, `cap-dedup-local-registry`, `cap-dedup-consensus-registry`, `cap-deterministic-replication`) ne passent pas tant que la preuve n'est pas liée.

---

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
