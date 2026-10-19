# reg-conformance

Standard de preuve runtime pour REG+. Séparation stricte : spécification (`specs/`),
données déclaratives (`catalog/`), outils (`tools/`), profils (`profiles/`), tests (`tests/`).

Le standard est **implementation-neutral** : il définit les propriétés (safety, liveness, fault tolerance, I8), pas le mécanisme. Tout backend qui implémente l'interface `ConsensusBackend` et satisfait les propriétés est conforme.

## Structure

```
reg-conformance/
├── catalog/
│   ├── hypotheses-v1.yaml            # 4 axes fermés (3×4×4×3 = 144 combinaisons)
│   ├── compatibility-rules-v1.yaml   # Règles déclaratives R1/R2/R3 (clause_id unique)
│   ├── capabilities-v1.yaml          # Capacités + preuves requises + invariants normatifs (v1.1.0)
│   └── valid-configurations-v1.json  # Généré : 42 admissibles / 102 rejetées
├── specs/
│   ├── evidence-contract-v1.json     # EvidenceRecord (JSON Schema 2020-12)
│   ├── assure-contract-v1.md         # Modèle théorique Assure (P1/P4/P5)
│   ├── consensus-contract-v1.md      # Contrat consensus : C1 safety, C2 liveness, C3 fault tolerance, I8
│   ├── consensus-interface-v1.json   # Interface ConsensusBackend (reserve/commit/release/reconcile/get_state)
│   └── evidence-type-specs-v1.md     # Spécification des 16 evidence types (schéma, protocole, critères)
├── tools/
│   ├── enumerate_configs.py          # Générateur (auto-valide le catalogue)
│   ├── validate_profiles.py          # Build wiring : profils → config admissible
│   └── verify_effective_guarantees.py# Build wiring : capacités réclamées → attestées (hash + chemin + coverage)
├── profiles/
│   ├── example-aggregate-budget.yaml             # Profil multi-host exemple (non attesté)
│   ├── example-aggregate-budget-single-host.yaml # Profil mono-host (3 preuves réelles, 1 manquante)
│   └── consensus-replicated.yaml                  # Profil consensus répliqué (modèle, non attesté)
├── evidence/
│   ├── cross-process-run.log          # Preuve réelle : test.lock.cross-process + test.idempotency.local
│   └── unknown-outcome-run.log        # Preuve réelle : test.unknown-outcome.blocks
└── tests/
    ├── _ref_impl.py                  # Référence : JCS/hash/Ed25519/injection-validator/commit
    ├── test_catalog_enumeration.py   # Indépendant du générateur (144/42/102)
    ├── test_evidence_integrity.py    # Adversarial : hash-chain, signature, continuité
    ├── test_assurance_signals.py     # Adversarial : anti-injection, anti-rejeu, fraîcheur
    ├── test_commit_semantics.py      # Adversarial : PASS+FAILED_RACE≠EXECUTED
    ├── test_profile_admissibility.py # Build wiring : profils admissibles / rejetés
    └── test_effective_guarantees.py  # Structurel ≠ effectif : 13 scénarios dont mutation tests
```

## Invariants normatifs (v1.1.0)

Le catalogue définit désormais des invariants normatifs que tout backend conforme doit maintenir :

| ID | Nom | Propriété | Périmètre |
|---|---|---|---|
| **I8** | budget-ceiling-aggregate | `reserved + committed ≤ capacity` | par resource_id |
| **LIN** | linearizability | ordre linéarisable respectant la précédence | toutes opérations |
| **AGR** | agreement | au plus un commit par réservation | tous commits |

Voir `consensus-contract-v1.md` pour les définitions formelles.

## Modèle de faute paramétrique (v1.1.0)

Le profil déclare le modèle de faute supporté :

```yaml
fault_model:
  crash: f          # nœuds qui peuvent crasher (crash-stop)
  byzantine: m      # nœuds byzantins (réponses arbitraires)
  omission: o       # nœuds en omission (perte de messages)
quorum: q           # nœuds nécessaires pour décider
total_nodes: n      # nombre total de nœuds
```

Bornes de résilience vérifiées par le validateur pour le profil Raft crash-stop (les fautes byzantines et d'omission ne sont pas attestées) :
- Crash-stop / Raft : `quorum = floor(n / 2) + 1`; disponibilité sous `f` crashs si `n - f >= quorum`
- Byzantin : `n ≥ 3m + 1`, `quorum = 2m + 1` (PBFT, Tendermint) ; non pris en charge par le profil Raft actuel

## Interface de conformance (v1.0.0)

L'interface `ConsensusBackend` (`consensus-interface-v1.json`) définit les opérations que tout backend doit implémenter :

```
reserve(key, amount, resource_id) → ReservationResult
commit(reservation_id) → CommitResult
release(reservation_id) → ReleaseResult
reconcile(key) → ReconciliationResult
get_state(resource_id) → ConsensusState
```

Le standard ne prescrit ni Raft, ni Paxos, ni etcd, ni PostgreSQL. Il prescrit ce que le backend doit garantir.

## Chiffres de référence (vérifiés par test indépendant)

- Total théorique : **144**
- Admissibles (structurel) : **42** — mono-process 9, mono-host 18, multi-host 15
- Rejetées : **102**

## Test perimeter and pinned implementation

The `conformance-target.json` manifest pins the TENIR-Gov source commit and package version, plus `catalog_version` and `rules_version`. The `pinned-tenir-gov-conformance` workflow checks out that exact source commit, verifies package/catalog/rules metadata, validates profile assumptions, and runs the pinned Raft integration suite.

### Reproduction

```bash
python tools/validate_profiles.py
python tests/test_profile_admissibility.py
pytest -q tests/test_conformance_target.py
pytest -q tenir-governance/tests/test_raft_backend.py
```

### Included
- Structural profile validation and crash-stop/quorum consistency checks.
- Exact implementation, catalog, and rules version checks.
- Local Raft integration, I8 regression, idempotent replay, amount validation, logical-clock replication, and resource re-registration tests.

### Excluded / not established
- Physical multi-host network or partition testing (the current Raft suite uses `localhost` and separate ports).
- Byzantine fault tolerance, hardened transport/authentication, third-party attestation, or exactly-once external effects.
- Formal proof of linearizability or production certification.

The CI run is the authoritative source for exact collected, passed, failed, and skipped counts. Do not combine counts from different suites without reporting each suite and its denominator. `admissible_structural` means structural coherence only; it must never be used to infer `effective_guarantee_demonstrated`.

Recorded pinned run: [GitHub Actions #39205591644](https://github.com/skiredj-prog/reg-conformance/actions/runs/39205591644) checked out TENIR-Gov commit `82037052556c5bfd731bd59fe958cf4df61d21b6`. Results: 4 target-metadata tests passed; the profile validator accepted all 4 repository profiles and its adversarial profile script passed; the pinned Raft suite collected 46 tests and passed all 46 (0 failed, 0 skipped) in 139.74 s. These are empirical localhost-lab results, not physical multi-host or production certification.
## Build

1. `python3 tools/enumerate_configs.py` — régénère `valid-configurations-v1.json`
2. `python3 tools/validate_profiles.py` — rejette tout profil référençant une config non admissible
3. `python3 tests/test_catalog_enumeration.py` — vérification indépendante du catalogue
4. Tests adversariaux : `test_evidence_integrity.py`, `test_assurance_signals.py`, `test_commit_semantics.py`
5. `python3 tools/verify_effective_guarantees.py` — rejette tout profil réclamant une capacité sans preuve **réelle** : fichier présent, SHA-256 égal à `evidence_sha256`, chemin relatif sans `..` (fail-closed). Test : `test_effective_guarantees.py` (13 scénarios dont altération et traversée).
   **Attendu** : les profils exemple et consensus-replicated échouent (exit 1) car les preuves manquent. C'est le comportement voulu, pas une erreur de build.

## Preuves réelles (état au 2026-10-19)

| Profil | Config | Preuves obtenues | Manquant |
|---|---|---|---|
| `consensus-reference-single-host.yaml` | mono-host / local-registry / file-lock / fail-closed | `test.consensus.safety` (`evidence/test-consensus-safety.log`), `test.consensus.liveness` (`evidence/test-consensus-liveness.log`), `test.fault-tolerance` (`evidence/test-fault-tolerance.log`), `test.idempotency.local` (`evidence/test-idempotency-local.log`), `test.unknown-outcome.blocks` (`evidence/unknown-outcome-run.log`) | **`deployment.manifest`** (dépendance bloquante pour l'audit externe) |
| `example-aggregate-budget-single-host.yaml` | mono-host / local-registry / file-lock / fail-closed | `test.lock.cross-process`, `test.idempotency.local` (`evidence/cross-process-run.log`), `test.unknown-outcome.blocks` (`evidence/unknown-outcome-run.log`) | **`deployment.manifest`** (dépendance bloquante pour l'audit externe) |
| `example-aggregate-budget.yaml` | multi-host / distributed-consensus | aucune | toutes : **aucune implémentation de consensus multi-hôte n'existe** |
| `consensus-replicated.yaml` | multi-host / distributed-consensus / fail-closed | aucune | toutes : modèle pour déploiement futur, adapter requis |

**`deployment.manifest` est une dépendance bloquante**, pas un détail. Sans ce manifeste, l'auditeur externe ne peut pas lier l'évidence à l'hypothèse de déploiement (`HOST_SCOPE = mono-host`). C'est le chaînon manquant pour tout audit indépendant. Seul l'opérateur peut le fournir (voir `evidence-type-specs-v1.md` §1 pour le schéma).

Les logs de preuve sont conformes au format défini dans `evidence-type-specs-v1.md` (en-têtes structurées + sortie pytest brute). Ils sont liés au commit `342bc04` de `skiredj-prog/tenir_governance` (5.5.0), avec SHA-256 dans les attestations. Ils sont produits par l'auteur (sandbox), **non par un vérificateur indépendant**.

## Types de preuve (v1.0.0)

16 evidence types sont définis dans `evidence-type-specs-v1.md` avec schéma, protocole de test, et critères d'acceptation. Voir le tableau récapitulatif dans ce fichier.

## Correctifs clés

### v1.1.0 — Consensus, I8, fault model

- **Consensus contract** : `consensus-contract-v1.md` définit formellement safety (C1), liveness (C2), fault tolerance (C3), et I8 (conservation du budget agrégé). Implementation-neutral.
- **Interface ConsensusBackend** : `consensus-interface-v1.json` définit l'API que tout backend doit implémenter. Le standard ne nomme aucune technologie.
- **I8 normatif** : I8 est désormais un invariant du standard (`normative_invariants` dans `capabilities-v1.yaml`), pas seulement un détail d'implémentation de `tenir_governance`.
- **Fault model paramétrique** : `fault_model_schema` et `resilience_bounds` dans le catalogue. Le vérificateur de profil rejette les configurations violant les bornes (Raft, PBFT).
- **Asymétrie corrigée** : `test.fault-tolerance` désormais requis pour `cap.dedup.consensus-registry` (symmetry avec `cap.concurrency.consensus`).
- **Evidence type specs** : `evidence-type-specs-v1.md` définit les 16 types de preuve avec schéma, protocole, et critères d'acceptation.
- **Profil consensus-replicated** : modèle pour déploiement futur avec adapter requis.

### v1.0 — EvidenceRecord, Assure, garantie effective

- **EvidenceRecord** : `previous_hash` dans `chain` (hors `integrity`), couvert par `current_hash` et signature. Distinction `evaluation_verdict` (pur) vs `effective_outcome` (opérationnel).
- **Assure** : rejeu et validation avant `Evaluate`. Signaux critiques expirés : défaut fail-closed (HOLD).
- **Garantie effective** : le vérificateur exige fichier de preuve + hash + chemin. Limite : `verified`/`verifier` restent déclaratifs.
