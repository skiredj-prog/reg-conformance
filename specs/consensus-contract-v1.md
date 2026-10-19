# Consensus Contract v1

**Modèle théorique du consensus distribué pour la gouvernance runtime REG+**

- Statut : spécification de référence (`reg-conformance/specs/`)
- Propriétés visées : **C1** (safety / accord), **C2** (liveness / terminaison), **C3** (tolérance aux pannes), **I8** (conservation du budget agrégé)
- Interface associée : `consensus-interface-v1.json` (`ConsensusBackend`)
- Indépendance : aucune dépendance à un protocole spécifique (Raft, Paxos, 2PC, ou backend externe). Le contrat définit les propriétés, pas le mécanisme.

> Avertissement : ce contrat décrit les propriétés attendues. Elles ne sont des garanties démontrées qu'une fois les tests adversariaux (fault harness, linearizability checker) en place et passés (voir §7).

---

## 1. Principe fondamental

> **Le standard définit les propriétés, pas le mécanisme.**

Un backend de consensus est conforme à ce contrat s'il satisfait les propriétés C1, C2, C3 et I8 pour les paramètres déclarés dans le profil. Le standard ne prescrit ni Raft, ni Paxos, ni etcd, ni PostgreSQL. Il prescrit ce que le backend doit garantir.

L'interface `ConsensusBackend` (voir `consensus-interface-v1.json`) est le point de conformance. Tout backend qui implémente cette interface et satisfait les propriétés est conforme.

---

## 2. Safety (C1) — Accord et linearizability

### 2.1 Linearizability

Chaque opération (`reserve`, `commit`, `release`, `reconcile`) prend effet à **un point unique** entre son invocation et sa réponse. L'ordre des opérations effectuées est un ordre linéarisable : il respecte l'ordre réel (precedence) des opérations non-chevauchantes.

Formellement : pour toute histoire d'exécution `H`, il existe une sérialisation `S` telle que :
1. `S` est équivalente à `H` (mêmes opérations, mêmes résultats) ;
2. `S` respecte la relation de précédence de `H` (si `op₁` termine avant que `op₂` commence, alors `op₁` précède `op₂` dans `S`) ;
3. `S` satisfait la spécification séquentielle de chaque opération.

**Vérification** : un linearizability checker enregistre les événements d'invocation et de réponse, construit l'histoire, et vérifie l'existence d'une sérialisation valide (algorithme Wing-Gong ou équivalent).

### 2.2 Accord (agreement)

Pour toute opération `commit(reservation_id)` :
- Si le commit réussit, alors exactement un nœud a commité cette réservation.
- Si deux nœuds tentent de commiter la même réservation, au plus un réussit.

### 2.3 Validité (integrity)

- Toute réservation réussie correspond à un `reserve()` antérieur non libéré.
- Tout commit réussi correspond à une réservation existante non commitée.
- Toute libération correspond à une réservation existante (commitée ou non).

### 2.4 Conservation du budget agrégé (I8)

Pour tout état du système à tout instant :

```
Σ(reserved) + Σ(committed) ≤ capacity
```

où :
- `Σ(reserved)` est la somme des montants réservés non encore commités ni libérés ;
- `Σ(committed)` est la somme des montants commités non encore libérés ;
- `capacity` est le plafond budgétaire déclaré dans le profil.

Cette invariant doit tenir **à chaque état intermédiaire**, pas seulement à l'état final. Sous concurrence, deux `reserve()` simultanées ne doivent pas faire dépasser le plafond même si chacune individuellement respecte `available >= amount`.

**Périmètre** : I8 s'applique par `resource_id`. Le profil peut déclarer plusieurs ressources, chacune avec son propre plafond. L'invariant est par ressource, pas global.

---

## 3. Liveness (C2) — Terminaison

### 3.1 Terminaison sous quorum

Si au moins `quorum` nœuds sont vivants et communiquent (pas de partition réseau entre eux), alors toute opération non bloquée par `HOLD` ou `HARD_VETO` finit par se terminer.

Formellement : il existe un temps borné `T_max` tel que toute opération invoquée à `t₀` se termine avant `t₀ + T_max`, sous réserve que le quorum soit maintenu pendant `[t₀, t₀ + T_max]`.

### 3.2 Liveness conditionnelle

La liveness n'est exigée que sous le quorum déclaré. Sous partition réseau (quorum non atteignable), le système peut bloquer — c'est acceptable. Ce qui n'est **pas** acceptable est de violer safety sous partition.

**Pas de garantie de terminaison sous** :
- Partition réseau réduisant le quorum en dessous du seuil ;
- Crash de plus de `f` nœuds ;
- Comportement byzantin non couvert par le modèle de faute.

### 3.3 Reconciliation liveness

Une opération en état `UNKNOWN` doit pouvoir être réconciliée : `reconcile(key)` doit retourner un résultat définitif (`CONFIRMED` ou `FAILED`) si le provider est joignable. Si le provider est injoignable, l'opération reste `UNKNOWN` et passe en `human_review` — c'est un comportement de safety, pas une violation de liveness.

---

## 4. Tolérance aux pannes (C3)

### 4.1 Modèle de faute paramétrique

Le profil déclare le modèle de faute supporté :

```yaml
fault_model:
  crash: f          # nombre maximal de crash-stop déclarés
  byzantine: m      # fautes byzantines déclarées
  omission: o       # fautes d'omission déclarées
  quorum: q         # quorum de décision
  total_nodes: n    # nombre total de nœuds
```

Le profil Raft actuellement pris en charge est **crash-stop uniquement** :
`byzantine = 0` et `omission = 0`. Toute autre tolérance doit être implémentée et démontrée séparément ; elle ne découle pas de ce contrat générique.

### 4.2 Bornes de résilience

Le profil doit satisfaire les bornes théoriques :

| Modèle de faute | Condition nécessaire | Référence |
|---|---|---|
| Crash-stop uniquement | `quorum = floor(n / 2) + 1`, `n - f ≥ quorum` pour la disponibilité déclarée | Raft, Paxos |
| Crash-stop + omission | `quorum = floor(n / 2) + 1`, disponibilité conditionnée aux nœuds et liens encore opérationnels | Paxos |
| Byzantin | `n ≥ 3m + 1`, `quorum = 2m + 1` | PBFT, Tendermint |

Le validateur actuel applique ces contrôles au profil Raft crash-stop uniquement. Les bornes byzantines et crash-stop + omission sont des références théoriques dans ce contrat ; elles ne sont ni validées par ce profil ni attestées comme capacités implémentées.

### 4.3 Safety sous faute

Le système doit maintenir C1 (safety) et I8 (budget) sous les fautes déclarées :
- `f` nœuds crashent à un moment arbitraire ;
- `m` nœuds produisent des réponses arbitraires (byzantins) ;
- `o` nœuds perdent des messages (omission).

Safety doit tenir **pendant** la faute, pas seulement après récupération.

### 4.4 Récupération

Un nœud qui crashe et redémarre doit :
1. Recharger son état depuis le stockage durable ;
2. Rattraper les opérations manquantes via le log replicé ;
3. Ne pas reprendre d'opérations déjà commitées par d'autres nœuds.

---

## 5. Interface de conformance

L'interface `ConsensusBackend` (voir `consensus-interface-v1.json`) définit les opérations que tout backend doit implémenter :

```
reserve(key, amount) → ReservationResult
commit(reservation_id) → CommitResult
release(reservation_id) → ReleaseResult
reconcile(key) → ReconciliationResult
get_state() → ConsensusState
```

Chaque opération a une spécification séquentielle précise (préconditions, postconditions, effets). Le linearizability checker valide que les histories concurrentes respectent ces spécifications.

### Spécification séquentielle

**`reserve(key, amount)`** :
- Précondition : `amount > 0`
- Postcondition : si succès, `reservation_id` unique créé, `reserved += amount`, `available -= amount`
- Échec : si `available < amount`, retourne `INSUFFICIENT_BUDGET` sans effet
- Idempotence : `reserve(key, amount)` avec une clé déjà réservée retourne la réservation existante si le montant correspond, sinon `DUPLICATE_KEY`

**`commit(reservation_id)`** :
- Précondition : `reservation_id` existe et est non commitée
- Postcondition : `reserved -= amount`, `committed += amount`
- Échec : si `reservation_id` n'existe pas ou est déjà commitée, retourne `NOT_FOUND` ou `ALREADY_COMMITTED` sans effet

**`release(reservation_id)`** :
- Précondition : `reservation_id` existe et est non commitée
- Postcondition : `reserved -= amount`, `available += amount`
- Échec : si `reservation_id` n'existe pas, `NOT_FOUND` sans effet

**`reconcile(key)`** :
- Précondition : `key` a une opération en état `UNKNOWN`
- Postcondition : retourne `CONFIRMED` (effet eu lieu) ou `FAILED` (pas d'effet) ou `UNRESOLVED` (provider injoignable)
- Si `CONFIRMED` : `committed += amount` si pas déjà commité
- Si `FAILED` : `reserved -= amount`, `available += amount`

**`get_state()`** :
- Postcondition : retourne `{ available, reserved, committed, capacity, reservations: [...] }`
- Pure : ne modifie aucun état

---

## 6. Répartition des vérifications

| Vérification | Support |
|---|---|
| Interface conforme au schéma JSON | `consensus-interface-v1.json` |
| Safety (linearizability) | Linearizability checker (Wing-Gong) |
| Safety (accord, validité) | Tests adversariaux (double-commit, clé dupliquée) |
| I8 (conservation budget) | Budget harness multi-processus |
| Liveness (terminaison) | Liveness harness (timeout sous quorum) |
| Fault tolerance | Fault harness (partitions, crashs, byzantins) |
| Profil admissible (bornes) | Vérificateur de profil |

---

## 7. Propriétés et tests adversariaux requis

| Propriété | Mécanisme | Test adversarial requis |
|---|---|---|
| Linearizability | Ordre linéarisable | Enregistrer une histoire concurrente, vérifier la sérialisabilité |
| Accord | Au plus un commit par réservation | Deux nœuds tentent le même commit → au plus un réussit |
| Validité | Pas d'effet fantôme | Commiter une réservation inexistante → échec sans effet |
| I8 (budget) | `reserved + committed ≤ capacity` | N processus réservent simultanément → somme ne dépasse jamais capacity |
| Terminaison | Opération se termine sous quorum | Invoquer sous quorum sain → se termine en temps borné |
| Safety sous partition | Safety tient pendant partition | Partitionner le réseau, effectuer des opérations → safety non violée |
| Récupération | Nœud crashé reprend correctement | Crasher un nœud, le redémarrer → ne reprend pas d'opérations déjà commitées |
| Anti-double-spend | Une clé = une réservation | Deux nœuds réservent la même clé → un seul gagne |

---

## 8. Non-objectifs

- Implémentation d'un protocole de consensus spécifique (Raft, Paxos, PBFT). Le contrat est implementation-neutral.
- Gestion de la membership dynamique (ajout/retrait de nœuds en cours d'exécution).
- Synchronisation d'horloge (le contrat suppose des horloges logiques, pas physiques).
- Garantie de terminaison sous partition totale (FLP impossibility).
- Preuve formelle mécanisée (Coq/TLA+). Les tests adversariaux sont empiriques, pas des preuves.

---

## 9. Références

- Wing & Gong, "A Modular Approach to Monitoring Linearizability" (1993)
- Lamport, "The Part-Time Parliament" (Paxos, 1998)
- Ongaro & Ousterhout, "In Search of an Understandable Consensus Algorithm" (Raft, 2014)
- Castro & Liskov, "Practical Byzantine Fault Tolerance" (PBFT, 1999)
- Fischer, Lynch & Paterson, "Impossibility of Distributed Consensus with One Faulty Process" (FLP, 1985)
- Herlihy & Wing, "Linearizability: A Correctness Condition for Concurrent Objects" (1990)
