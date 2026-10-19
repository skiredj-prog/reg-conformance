# Assure Contract v1

**Modèle théorique du module Assure pour la gouvernance runtime REG+**

- Statut : spécification de référence (`reg-conformance/specs/`)
- Propriétés visées : **P1** (déterminisme / commit), **P4** (séparation de l'assurance), **P5** (intégrité / authenticité)
- Schéma associé : `evidence-contract-v1.json` (`$defs/AssuranceSignal`)
- Indépendance : aucune dépendance à AIREP ni AgentHook.

> Avertissement : ce contrat décrit les mécanismes attendus. Les propriétés P1/P4/P5 ne sont des garanties démontrées qu'une fois les validateurs d'exécution et les tests adversariaux en place (voir §7).

---

## 1. Principe fondamental (P4)

> **`Evaluate` ne détecte jamais rien. Il lit seulement l'état `s`.**

`Evaluate(σ, I*, s, τ, t_eval)` est une fonction pure. L'infrastructure n'influence la décision que par un seul canal : `s.infrastructure_signals`, peuplé exclusivement de `AssuranceSignal` signés, **acceptés au stade injection-validation**.

Trois entités disjointes :

| Entité | Responsabilité | Connaissance | État |
|---|---|---|---|
| **Assure** | Observer, détecter, produire et signer des signaux | `infra_state`, `h` | Stateful (détection) |
| **Injection-validator** | Valider signature, émetteur, format, fraîcheur initiale, rejeu, portée de corrélation | Registre de clés, registre anti-rejeu | Stateful |
| **Evaluate** | Calculer le verdict à partir d'entrées capturées | `s` (lu), `t_eval` | **PURE** |
| **Profil σ** | Traduire les signaux acceptés en stratégie de verdict | Taxonomie des `signal_type` | Déclaratif |

---

## 2. Les trois phases du module Assure

### Phase 1 — Observation et Détection (hors cycle runtime)
Assure consomme l'observabilité, détecte les violations d'hypothèses `h`, avec fenêtre de validation (persistance sur `N` cycles) contre les faux positifs.

### Phase 2 — Production et Signature
Assure produit un `AssuranceSignal` (schéma dans `evidence-contract-v1.json`) et le signe en Ed25519 (JCS, charge utile sans le champ `signature`). La signature empêche l'injection de faux signaux (ex. faux `HYPOTHESIS_VERIFIED` pour contourner un `HOLD`).

### Phase 3 — Injection dans l'état runtime
Le signal signé est soumis à l'**injection-validator** (§3). Seuls les signaux acceptés sont ajoutés atomiquement à `s.infrastructure_signals`. Les signaux rejetés sont journalisés avec la raison (preuve d'audit).

---

## 3. Le rejeu et la validation sont traités AVANT `Evaluate`

L'unicité de `signal_id` et la vérification de rejeu nécessitent un registre stateful. Cette opération **ne peut pas être cachée dans `Evaluate`** (qui doit rester pure). On distingue trois stades :

### Stade A — Injection-validation (stateful, hors Evaluate)
Pour chaque signal entrant, vérifier dans l'ordre :
1. **Format** : conforme au schéma `AssuranceSignal` (`signal_id` ULID, champs requis, `expires_at ≥ issued_at`).
2. **Signature** : vérification Ed25519 contre la clé publique résolue depuis `assure_instance_id` (registre de clés REG+).
3. **Identité de l'émetteur** : `assure_instance_id` connu et autorisé à émettre ce `signal_type`.
4. **Fraîcheur initiale** : `issued_at ≤ now ≤ expires_at` (ou TTL résolu).
5. **Anti-rejeu** : `signal_id` absent du registre des signaux déjà consommés dans la fenêtre de TTL. Présent → rejet.
6. **Portée de corrélation** : `correlation_id` correspond à une transition en vol ou à une fenêtre d'observation déclarée ouverte. Hors périmètre → rejet.

Le registre anti-rejeu est stateful, borné (fenêtre de TTL), et appartient à l'injection-validator, jamais à `Evaluate`.

### Stade B — Évaluation (pure)
`Evaluate(σ, I*, s, τ, t_eval)` traite les seuls signaux acceptés et présents dans le snapshot `s` capturé. Aucun effet de bord.

### Stade C — Audit
Conserver la preuve d'acceptation ou de rejet de chaque signal (raison, horodatage, `signal_id`). Un signal rejeté n'apparaît jamais dans `s` ni dans un EvidenceRecord valide.

### Définition précise de `correlation_id`
- **Format** : identifiant opaque (ULID ou UUID) référencé par le producteur du signal.
- **Périmètre** : il lie le signal à une run, une transaction ou une fenêtre d'observation déclarée.
- **Condition d'acceptation** : un signal est dans le périmètre si `correlation_id` correspond à une transition `τ` en cours de traitement, ou à une observation ouverte déclarée dans `s`. Un signal dont le `correlation_id` ne correspond à rien en cours est rejeté au stade A (anti-rejeu par contexte).

---

## 4. Fraîcheur compatible avec la pureté de `Evaluate`

La fraîcheur dépend de l'instant. Si `Evaluate` lisait l'horloge système, les mêmes entrées produiraient des verdicts différents selon le moment — le déterminisme (P1) serait cassé.

**Correction : l'instant d'évaluation est une entrée explicite.**

```
Evaluate(σ, I*, s, τ, t_eval) → evaluation_verdict
```

- `t_eval` est enregistré dans `evaluation_context.evaluation_time` (voir `evidence-contract-v1.json`).
- La fraîcheur est calculée : `issued_at ≤ t_eval ≤ expires_at`.
- Si `expires_at` est absent, le TTL par défaut est résolu de façon **déterministe** via `evaluation_context.signal_ttl_resolution` (clé = `signal_type`, valeur = secondes), déclaré dans σ ou dans le registre des types de signal référencé par `catalog_version`. Deux évaluateurs ne peuvent pas appliquer silencieusement des durées différentes.
- La stratégie de fraîcheur (`STRICT` / `STALE_FLAG`, voir §5) est déclarée dans σ par `signal_type`. Défaut si non déclaré : `STRICT`.

---

## 5. Signaux critiques expirés : l'absence d'information n'est pas une preuve de rétablissement

La stratégie `STRICT` (signal expiré ignoré) est dangereuse pour un signal critique : son expiration ne doit pas ramener implicitement à un état favorable. Le contrat distingue quatre états pour chaque `signal_type` déclaré :

| État | Signification |
|---|---|
| **ABSENT** | Aucun signal de ce type jamais émis ou injecté |
| **VALID_FAVORABLE** | Signal valide (frais) indiquant un rétablissement / une vérification positive |
| **VALID_DEGRADATION** | Signal valide (frais) indiquant une dégradation / violation d'hypothèse |
| **EXPIRED_CRITICAL** | Dernier signal connu était critique et est expiré ; la continuité de surveillance n'est plus démontrée |

Règles :
- La conséquence de chaque état appartient au profil σ (règles de réaction).
- **Par défaut, si σ ne déclare pas de mapping pour `EXPIRED_CRITICAL`, l'évaluateur doit fail-closed : traiter l'état comme `HOLD` au minimum**, jamais comme `VALID_FAVORABLE`.
- L'`ABSENCE` de signal n'est jamais assimilée automatiquement à `VALID_FAVORABLE`.
- Un signal `info` ou `warning` expiré peut être ignoré (`STRICT`) si σ le déclare explicitement.

---

## 6. Répartition des vérifications : schéma JSON vs validateur d'exécution

`evidence-contract-v1.json` couvre les contraintes **structurelles** (champs requis, formats, énumérations, motifs ULID/hex, conditionnels). Les vérifications suivantes relèvent d'un **validateur d'exécution** complémentaire :

| Vérification | Support |
|---|---|
| Champs requis, énumérations, motifs (ULID, hash, signature hex) | JSON Schema |
| `expires_at ≥ issued_at` | Validateur d'exécution (comparaison de dates) |
| Résolution cohérente du TTL par défaut | Validateur d'exécution (lit `signal_ttl_resolution`) |
| Vérification de la signature Ed25519 contre le registre de clés | Validateur d'exécution |
| Anti-rejeu (`signal_id` déjà consommé) | Injection-validator (stateful) |
| Portée de `correlation_id` | Injection-validator |
| Cohérence `evaluation_verdict` ↔ `commit_trace` ↔ `effective_outcome` | Validateur d'exécution (règles déclarées dans le schéma, appliquées au runtime) |

---

## 7. Propriétés de sécurité et tests adversariaux requis

| Propriété | Mécanisme | Test adversarial requis |
|---|---|---|
| Anti-injection | Signature Ed25519 par instance Assure | Injecter un signal non signé / mal signé → rejet au stade A |
| Anti-rejeu | `signal_id` + registre borné + `correlation_id` | Rejouer un signal signé valide → rejet |
| Fraîcheur déterministe | `t_eval` explicite + `signal_ttl_resolution` | Mêmes entrées, `t_eval` différent → verdict cohérent avec σ ; jamais d'horloge système |
| Pureté de Evaluate | Aucun appel hors entrées capturées | Injection-validator et Evaluate testés séparément |
| Chaîne d'évidence | `previous_hash` dans `chain` (couvert par `current_hash`) | Modifier le lien de chaîne → signature invalide |
| Commit effectif | `commit_trace` + `effective_outcome` | Provoquer une race condition → `effective_outcome=COMMIT_FAILED`, pas `PASS` |
| Surveillance critique | États §5, défaut fail-closed | Expirer un signal critique sans règle σ → HOLD au minimum |

---

## 8. Non-objectifs

- Implémentation du stockage transactionnel de `s` et du registre anti-rejeu.
- Registre de clés et révocation des instances Assure compromises (document séparé).
- Démonstration de la garantie effective des capacités (ex. `distributed-consensus`) : vérifiée au build contre des implémentations, distincte de l'admissibilité structurelle du catalogue.

---

## 9. Références

- RFC 8785 (JCS), RFC 8032 (Ed25519), JSON Schema 2020-12, ULID.
