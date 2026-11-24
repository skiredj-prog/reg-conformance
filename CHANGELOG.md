# Changelog

## Non publié

### Changed

- **Vocabulaire aligné sur les errata ratifiés de la v7.2** (`manuscript/ERRATA-v7.2.md`, ratifiés par l'auteur le 23 novembre 2026). Textes seulement : aucun identifiant, statut, attendu ni résultat de vecteur ne change.
  - τ_R remplace τ_K là où la fenêtre de qualification du reçu est visée : en-tête et descriptions T6/T7 de `runner.py`, entrée de `CT-R4-011` (`vectors/core.yaml`), `lifecycle/register_core_lifecycle.py`. τ_K garde son sens REG (fenêtre de résolution d'un HOLD, RFC-0 §6) partout ailleurs.
  - `CT-R4-011` cite T6 au vocabulaire de cycle de vie de cette suite (`LIFECYCLE_INTEGRATION.md`, `lifecycle/attempt_state.py`), et `CT-R4-013` cite T8 à `tenir-conformance-s1-g1` en `8bc0e5e` (note T6/T8 des errata : le manuscrit ne nomme que T7, en §4.4).
  - `vectors/dist/vectors.json` régénéré par `vectors/compile.py` ; `VECTORS.md` aligné.
  - Glossaire (brouillon) : éléments en attente de `GL-TAU-R` et `GL-LIFECYCLE-T` clos. Restent en attente le libellé I8 du port TenirGov (`harness/ports/tenir_gov.py`, modifié par le port 5.7.7 local) et le renommage I8 → BUD dans `tenir_governance`, prévu en 5.8.0.

## v0.7.0 — 2026-11-20

Cohérence REG / REG+ / suite, RN-001 inscrit dans le registre des vecteurs, harness neutre et `CLAIMS.md` en vigueur. Une seule version de chaque chose. Détail et état : `python tools/check_coherence.py`.

RFC-4 v0.3, révision datée du 19 novembre 2026, est ratifiée par l'auteur et en vigueur à partir de cette version, hors baseline gelé : `rfc-4.md` v0.2 reste le texte gelé, inchangé, et `CT-R4-004a` / `CT-R4-004b` sont des vecteurs en vigueur. Seule reste ouverte la correspondance avec STA-EA-02, qui ne change pas la révision. Ce que cette version ne contient pas : le glossaire papier / suite et l'errata du manuscrit v7.2, le correctif τ_K de TENIR-Gov (prévu en 5.7.5, non publié). La seule version de TENIR-Gov épinglée et citée est 5.7.0 (`47ef67e`). Aucune capacité n'est démontrée (0 sur 42 configurations admissibles) ; aucun résultat publié ne porte sur le runtime TENIR-Gov.

### Added

- **Suite v0.4.0** (`runner.py`, `spec.md`, `reg_common.py`) : 61 vecteurs au lieu de 56 (v0.3.2). Les rapports se distinguent ainsi de ceux de v0.6.x.
- `harness/` : port neutre (`RuntimePort`), scénarios écrits une fois, port de référence, port TENIR-Gov sur le chemin par défaut du gouverneur (correspondance des intentions et des refus provisoire, à confirmer par l'auteur du runtime), sondes d'effet `HX-EFFECT-001` à `004`, 17 contrôles de propriété, lecture par familles candidates `EGP-*` (non ratifiées). Workflow `REG Conformance - Run` (`conformance-run.yml`) et `tools/make_evidence_bundle.py` : une exécution, un paquet de preuve, `certifying: false`.
- **Révision RFC-4 v0.3 du 19 novembre 2026** (`revisions/rfc-4-v0.3-2026-11-19.md`, ratifiée par l'auteur le 19 novembre 2026 et amendée par lui le 20 novembre 2026 sur le rejet observé, §2.2 et §2.3 ; en vigueur, hors baseline gelé ; `reg-standards-baseline/rfc/rfc-4.md` v0.2 reste gelée et inchangée). La borne se lit selon l'objet qui la porte : l'autorisation (§2.1, aucun effet sous une autorisation dont la borne déclarée est dépassée ; une autorisation fraîche est une politique déclarée, à quatre conditions, attribuée à la nouvelle autorisation) ou la tentative retenue (§2.2, disposition pré-déclarée, refus terminal par défaut pour cette identité de tentative). Axe épistémique orthogonal (§2.3) : l'état enregistré suit ce que l'évidence disponible établit, pas l'historique du dispatch. `CONFIRMED_NONEXECUTION` si la tentative n'a jamais été dispatchée, si un rejet qualifié de ce dispatch a été observé, ou si une attestation de non-exécution qualifiée et vérifiée existe (cas T7), `UNKNOWN` et réconciliation sinon ; `FAILED` est une étiquette runtime à mapper selon la même règle. Résultat exigé sur dérive d'état (§3, RN-001 §4). Lecture « l'expiration force une réadjudication » de RN-001 §2b-§3 retirée (§4). Correspondance avec STA-EA-02 (§6) : REG admet les deux modèles, le grant borné et l'adjudication fraîche à chaque crossing (une autorisation fraîche au sens du §2.1, admise comme politique déclarée à ses quatre conditions) ; c'est à STANAIC de dire si STA-EA-02 est compatible avec l'un ou les deux, et lequel est préféré, et cette réponse se range sous §2.1 et §2.2 sans les changer.
- Vecteurs `CT-R4-004a` (autorité valide au moment de l'effet, `implemented`) et `CT-R4-004b` (tentative retenue à sa borne déclarée, REG-STATE-024, `specified`), en vigueur avec la révision. `CT-R4-004a` : `PASS` natif et HTTP sur le noyau de référence. `CT-R4-004b` : scénario harness ; `ADAPTER_REQUIRED` sur le noyau de référence et le shim, qui ne déclarent aucune borne sur une tentative retenue (leur seul HOLD est l'insuffisance d'évidence).
- `CLAIMS.md` en vigueur : règle d'admission du FLAG (RN-001 B1) et évaluations par des tiers (D2). `RESULTS.md` : exécutions publiées et en attente de confirmation.

- Vecteurs `CT-R4-014` (pas de dispatch sur un verdict périmé), `CT-R4-015` (l'âge n'améliore jamais une disposition) et `CT-R4-016` (une borne fail-safe refuse seule), enregistrés selon RN-001 §3 au statut `specified` ; le runner rend `IMPLEMENTATION_GAP` tant que les sondes n'existent pas. Remplacés dans la même version par `CT-R4-004a` et `CT-R4-004b` (voir Changed). `vectors/schema.json` accepte `superseded_by`.
- `reg-standards-baseline/notes/RN-001-flag-time-drift.md` : note ratifiée le 18 novembre 2026. FLAG avec condition = admission, FLAG sans condition = lacune ; borne fail-safe contre temps écoulé épistémique ; remplacement annoncé de CT-R4-004 ; résultat exigé pour C3 et CT-R4-005. Aucun résultat ni compte de vecteurs ne change.
- `tools/check_coherence.py`, `coherence-baseline.json`, job CI `coherence` : compare les registres, les documents et les fichiers publiés ; échoue sur toute contradiction nouvelle.
- `README.md` : carte du dépôt (REG, suite de conformance, REG+, crosswalk) et couverture publiée par fondement.
- Crosswalk : six correspondances vecteur REG ↔ REG+ au statut `unverified`, avec citation et limite.
- `runner.py` : `summary_by_basis` dans le rapport (vecteurs spécifiés par les RFC gelées ou une révision ratifiée / identifiants qu'aucun texte ratifié ne spécifie ; les noms de clés ne changent pas).
- `catalog/capabilities-v1.yaml` : registre `guarantee_records` des fiches de `capabilities/v1.0.0/`, avec `refines` et `applies_when`. `tools/fill_catalog_guarantees.py` lit ce registre au lieu de répéter la correspondance dans le code.
- `tools/verify_capabilities.py --source DIR` : une capacité démontrée dont la commande de test nomme un fichier absent de la source épinglée est rejetée. Exécuté dans le job `pinned-raft-conformance`.

### Changed

- **TENIR-Gov épinglé une seule fois.** Le job `lifecycle` installait `b65efba`, un commit hors `main` de `tenir_governance` qui se déclare lui aussi 5.7.0 sans l'être (142 commits après le tag). Il lit maintenant `conformance-target.json` (5.7.0, `47ef67e`, tag `v5.7.0`) comme les jobs `pinned-raft-conformance` et `coherence`, et vérifie la version installée. `standard_version` du manifeste passe de `v0.5.1` à `v0.7.0`.
- **Noyau de référence : garde de finitude** (décision de l'auteur du 19 novembre 2026). Toute comparaison avec NaN est fausse : `S < seuil` ne se déclenchait jamais et le noyau admettait une mesure NaN. Une mesure qui n'est pas un nombre réel fini (None, NaN, ±inf, booléen, chaîne, entier trop grand pour un flottant) est désormais une insuffisance d'évidence : `HOLD`, `reason: INSUFFICIENT_EVIDENCE`, `unmeasured_axes`, `s_score: null`, jamais `PASS`. Un veto qui tient sans S reste appliqué, car la disposition la plus restrictive l'emporte (RFC-0 §4) : K = 0 donne `HARD_VETO` même si P ou V n'est pas mesuré, avec ces axes dans `unmeasured_axes`. Un dénominateur nul (P × V + ε = 0) ne fait plus lever d'exception : `HOLD`, ou `HARD_VETO` si K = 0. Sur le fil, le shim reçoit et renvoie `null` (jamais NaN, le JSON reste strict) avec `unmeasured_axes` ; un axe omis n'a plus de valeur par défaut favorable ; un booléen JSON ou une chaîne numérique est refusé (422) au lieu d'être lu comme une mesure ; une vitesse que le shim ne peut pas dériver de la pression et de la volatilité (axe manquant, produit négatif, entier trop grand pour un flottant) reste non mesurée, au lieu d'une erreur 500. `PX-REG-STATE-001` passe de `FAIL` à `PASS` sur le noyau de référence ; les 15 PASS des vecteurs ne changent pas.
- **Harness : FLAG sans condition** (`CLAIMS.md`, RN-001 §1, décision 3 de l'auteur). Le résultat obtenu sur un `FLAG` sans condition explicite reste celui de la correspondance déclarée, avec la réserve « obtained under a declared mapping interpretation, pending ratification; the FLAG on this path states no condition. » ; la lacune d'implémentation est enregistrée à part, quel que soit le résultat (`admission.implementation_gaps`, repris dans `verdict.json`) ; seul un `PASS` porte la réserve.
- **Harness : `NOT_IN_PERIMETER`** (décision 1). Un implémenteur peut déclarer une propriété hors du périmètre de son runtime (`not_in_perimeter`, avec auteur et motif) ; le contrôle de propriété correspondant rend `NOT_IN_PERIMETER`, ni `PASS` ni `FAIL`. Port TENIR-Gov : la correspondance `out_of_scope` → `Agent.capabilities`, champ que le runtime ne lit pas, est retirée ; CT-R3-007 est déclaré hors périmètre (« la portée est une préoccupation L1 »).
- Harness : un port ne peut plus déclarer `not_applicable` un vecteur qui a un scénario neutre (même règle que pour `run_custom`).
- Harness aligné sur RN-001 §4 : pour CT-R4-005, un commit refusé sous un autre libellé que `STATE_DRIFT`/`HARD_VETO` donne `INCONCLUSIVE`, plus `FAIL`, comme dans `runner.py`. CT-R4-014 à CT-R4-016 rattachés aux familles candidates `EGP-03`, `EGP-13` et `EGP-03` ; le port de référence rend pour eux le même `IMPLEMENTATION_GAP` que le runner.
- `RESULTS.md` : l'exécution de référence du 16 novembre a tourné sur une branche hors de cette version ; son lien est retiré en attendant une exécution sur le commit v0.7.0.
- **CT-R4-004 remplacé** par CT-R4-004a et CT-R4-004b (révision RFC-4 v0.3, §5) : `superseded_by` dans `vectors/commit.yaml` ; il reste enregistré avec son texte et ses résultats. `CT-R4-014` et `CT-R4-015` (lecture réadjudication, retirée) passent `superseded_by` `CT-R4-004a`, `CT-R4-016` `superseded_by` `CT-R4-004b` ; aucun des trois n'avait de sonde ni de résultat.
- `tools/check_coherence.py` : un identifiant de vecteur peut finir par une lettre minuscule (`CT-R4-004a`).
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
