# Evidence Type Specifications v1

**Spécification des types de preuve exigés par le catalogue de capacités REG+**

- Statut : spécification de référence (`reg-conformance/specs/`)
- Catalogue associé : `catalog/capabilities-v1.yaml`
- Contrat associé : `consensus-contract-v1.md`

> Chaque evidence type nommé dans `capabilities-v1.yaml` est défini ici avec son schéma, son protocole de test, et ses critères d'acceptation. Une attestation qui référence un evidence type non défini ici est invalide.

---

## Format commun

Chaque evidence type est spécifié avec :

1. **ID** — l'identifiant utilisé dans `capabilities-v1.yaml`
2. **Description** — ce que la preuve démontre
3. **Schéma** — structure du fichier de preuve attendu
4. **Protocole de test** — comment exécuter le test
5. **Critères d'acceptation** — conditions de passage
6. **Limite** — ce que la preuve n'établit pas

---

## 1. `deployment.manifest`

**Description** : Décrit le déploiement réel de l'opérateur — topologie, hôtes, processus, backends, configuration réseau.

**Schéma** (YAML) :
```yaml
manifest_version: "1.0"
operator: <string>                    # identifiant de l'opérateur
deployment_date: <ISO-8601 date>
topology:
  hosts:
    - id: <string>
      address: <string>
      processes: [<string>]
  networks:
    - id: <string>
      hosts: [<string>]
      partition_model: <string>        # description du modèle de partition
backend:
  type: <string>                       # etcd, postgresql, raft-native, file-lock, etc.
  version: <string>
  configuration: <object>               # configuration pertinente (quorum, replication factor, etc.)
resources:
  - resource_id: <string>
    capacity: <integer>
    currency: <string>                 # USD, EUR, tokens, etc.
```

**Protocole** : Fourni par l'opérateur. Vérifié par le vérificateur de profil (existence et validité structurelle).

**Critères d'acceptation** :
- Fichier présent dans le dépôt
- `manifest_version` = "1.0"
- Au moins un hôte déclaré
- Backend déclaré avec type et version
- Au moins une ressource avec capacité

**Limite** : Le manifeste est déclaratif. Il décrit ce que l'opérateur déploie, pas ce qui est réellement en production. Sa vérification est structurelle.

---

## 2. `test.lock.cross-process`

**Description** : Prouve que la coordination inter-processus repose sur un verrou de fichier (`fcntl.flock` ou équivalent).

**Schéma** (log pytest) :
```
# Evidence: test.lock.cross-process
# repo: <url>
# commit: <sha>
# test file sha256: <hash>
# command: <command>
# executed: <ISO-8601>
# executed by: <environment>
----
<pytest output brut>
```

**Protocole** :
1. Lancer `pytest tests/test_cross_process.py -v` (ou équivalent) dans le dépôt `tenir_governance`
2. Au moins 2 processus distincts participent
3. Le test vérifie que le registre durable utilise `fcntl.flock`

**Critères d'acceptation** :
- Tous les tests passent (0 FAILED, 0 SKIPPED pour les tests de file-lock)
- Au moins 2 processus distincts dans le log
- Le mécanisme de verrouillage est `fcntl.flock` (visible dans le code ou le log)

**Limite** : Prouve la coordination inter-processus sur un seul hôte (système de fichiers partagé). Ne prouve pas la coordination inter-hôtes.

---

## 3. `test.idempotency.local`

**Description** : Prouve qu'une clé d'idempotence n'est acceptée que par un seul processus sur un hôte.

**Schéma** : Même format que `test.lock.cross-process`.

**Protocole** :
1. Lancer le test inter-processus avec deux processus tentant d'enregistrer la même clé
2. Vérifier qu'un seul réussit

**Critères d'acceptation** :
- Deux processus tentent la même clé
- Exactement un réussit
- Le second est rejeté

**Limite** : Local à un hôte. Ne prouve pas l'idempotency inter-hôtes.

---

## 4. `test.idempotency.distributed`

**Description** : Prouve qu'une clé d'idempotence n'est acceptée que par un seul nœud dans un déploiement multi-hôtes.

**Schéma** : Même format que `test.lock.cross-process`, avec en plus :
```
# hosts: <list>
# nodes: <list>
```

**Protocole** :
1. Déployer ≥ 2 nœuds sur ≥ 2 hôtes
2. Deux nœuds tentent d'enregistrer la même clé simultanément
3. Exactement un réussit

**Critères d'acceptation** :
- ≥ 2 hôtes, ≥ 2 nœuds
- Exactement un nœud accepte la clé
- Les autres sont rejetés
- L'état est répliqué (le nœud qui refuse voit la clé après réplication)

**Limite** : Ne prouve pas l'idempotency sous partition réseau.

---

## 5. `test.idempotency.provider`

**Description** : Prouve que le provider externe déduplique via une clé d'idempotency.

**Schéma** :
```yaml
provider: <string>                    # Stripe, etc.
contract_reference: <url>             # lien vers la documentation du provider
key_header: <string>                  # Idempotency-Key, etc.
test_method: <string>                 # description du test
result: <string>                      # PASS / FAIL
evidence: <text>                      # sortie de test ou capture
```

**Protocole** :
1. Envoyer deux requêtes au provider avec la même clé d'idempotency
2. Vérifier qu'un seul effet est produit

**Critères d'acceptation** :
- `result` = PASS
- Deux requêtes, un seul effet
- `contract_reference` pointe vers la documentation du provider

**Limite** : Dépend du provider. Ne prouve pas le comportement sous failure du provider.

---

## 6. `test.consensus.safety`

**Description** : Prouve que le backend de consensus maintient safety (linearizability, accord, validité, I8) sous concurrence et sous fautes déclarées.

**Schéma** (log structuré) :
```
# Evidence: test.consensus.safety
# backend: <type> <version>
# commit: <sha>
# nodes: <n>
# quorum: <q>
# fault_model: { crash: <f>, byzantine: <m>, omission: <o> }
# linearizability_checker: <name> <version>
# command: <command>
# executed: <ISO-8601>
----
<linearizability checker output>
<budget conservation check output>
<agreement check output>
```

**Protocole** :
1. Déployer `n` nœuds du backend
2. Lancer `N` processus clients concurrents effectuant `reserve/commit/release`
3. Enregistrer l'historique complet (invocation + response events)
4. Injecter `f` crashs, `m` comportements byzantins, `o` omissions
5. Vérifier :
   a. Linearizability : l'historique est sérialisable (Wing-Gong ou équivalent)
   b. I8 : à chaque état intermédiaire, `reserved + committed ≤ capacity` par resource_id
   c. Accord : au plus un commit par réservation
   d. Validité : pas d'opération fantôme

**Critères d'acceptation** :
- Linearizability checker : PASS (historique sérialisable)
- I8 : 0 violation à chaque état intermédiaire
- Accord : 0 double-commit
- Validité : 0 opération fantôme
- Fault injection : `f` crashs, `m` byzantins, `o` omissions injectés et documentés
- Safety maintenue pendant les fautes

**Limite** : Test empirique, pas preuve formelle. La couverture dépend du nombre d'opérations et de la diversité des interleavings. Ne couvre pas tous les interleavings possibles (explosion combinatoire).

---

## 7. `test.consensus.liveness`

**Description** : Prouve que toute opération non bloquée par HOLD/HARD_VETO se termine en temps borné sous quorum sain.

**Schéma** :
```
# Evidence: test.consensus.liveness
# backend: <type> <version>
# commit: <sha>
# nodes: <n>
# quorum: <q>
# T_max: <seconds>
# command: <command>
# executed: <ISO-8601>
----
<liveness harness output>
# operations_invoked: <count>
# operations_completed: <count>
# operations_blocked_hold: <count>
# operations_blocked_veto: <count>
# max_latency: <seconds>
# all_completed_under_T_max: <bool>
```

**Protocole** :
1. Déployer `n` nœuds, maintenir quorum `q` pendant tout le test
2. Invoquer `N` opérations `reserve/commit/release`
3. Mesurer le temps de terminaison de chaque opération
4. Vérifier que toutes se terminent avant `T_max`

**Critères d'acceptation** :
- `operations_completed` = `operations_invoked` - `operations_blocked_hold` - `operations_blocked_veto`
- `all_completed_under_T_max` = true
- `max_latency` < `T_max`
- Aucune opération non-bloquée ne reste en attente

**Limite** : Liveness prouvée seulement sous quorum sain. Sous partition, l'attente est acceptable (safety prime). `T_max` dépend du backend et de la configuration.

---

## 8. `test.fault-tolerance`

**Description** : Prouve que le backend maintient safety sous les fautes déclarées (crash, byzantin, omission).

**Schéma** :
```
# Evidence: test.fault-tolerance
# backend: <type> <version>
# commit: <sha>
# nodes: <n>
# quorum: <q>
# fault_model: { crash: <f>, byzantine: <m>, omission: <o> }
# fault_injection: <method>            # tc netem, process kill, mock byzantine
# command: <command>
# executed: <ISO-8601>
----
<fault harness output>
# faults_injected: <count>
# safety_violations: <count>
# recovery_successful: <bool>
# linearizability_maintained: <bool>
# I8_maintained: <bool>
```

**Protocole** :
1. Déployer `n` nœuds
2. Démarrer des opérations concurrentes
3. Injecter `f` crashs (kill -9), `m` byzantins (réponses arbitraires), `o` omissions (perte de messages)
4. Vérifier safety pendant les fautes
5. Récupérer les nœuds crashés
6. Vérifier que la récupération est correcte (pas de reprise d'opérations déjà commitées)

**Critères d'acceptation** :
- `safety_violations` = 0
- `linearizability_maintained` = true
- `I8_maintained` = true
- `recovery_successful` = true
- Les fautes injectées correspondent au modèle déclaré

**Limite** : Jepsen-style, pas preuve formelle. La couverture dépend des scénarios de faute testés. Ne couvre pas tous les modèles de faute possibles.

---

## 9. `test.cross-host.communication`

**Description** : Prouve que les nœuds sur des hôtes distincts peuvent communiquer et coordonner.

**Schéma** :
```
# Evidence: test.cross-host.communication
# backend: <type> <version>
# commit: <sha>
# hosts: <list>
# command: <command>
# executed: <ISO-8601>
----
<cross-host test output>
# hosts_reachable: <count>
# messages_exchanged: <count>
# coordination_successful: <bool>
```

**Protocole** :
1. Déployer ≥ 2 nœuds sur ≥ 2 hôtes distincts
2. Un nœud réserve, l'autre commit (ou inverse)
3. Vérifier que l'état est répliqué
4. Vérifier que les messages sont échangés

**Critères d'acceptation** :
- `hosts_reachable` ≥ 2
- `coordination_successful` = true
- L'état répliqué est cohérent entre les hôtes

**Limite** : Ne prouve pas la coordination sous partition. Ne prouve pas la linearizability (voir `test.consensus.safety`).

---

## 10. `test.mutex.exclusion`

**Description** : Prouve que le verrou de thread assure l'exclusion mutuelle dans un seul processus.

**Schéma** : Même format que `test.lock.cross-process`.

**Protocole** :
1. Lancer `N` threads dans un seul processus
2. Chaque thread tente de réserver le même budget
3. Vérifier qu'un seul à la fois tient le verrou

**Critères d'acceptation** :
- Exclusion mutuelle vérifiée
- Pas de deadlock
- Tous les threads finissent par passer (liveness intra-process)

**Limite** : Single-process uniquement. Ne prouve pas l'exclusion inter-processus.

---

## 11. `test.2pc.commit`

**Description** : Prouve que le protocole 2PC commit correctement (prepare → commit).

**Schéma** : Même format que `test.lock.cross-process`.

**Protocole** :
1. Initier une transaction 2PC
2. Phase 1 (prepare) : tous les participants votent
3. Phase 2 (commit) : le coordinator commit
4. Vérifier que tous les participants ont commité

**Critères d'acceptation** :
- Prepare réussi
- Commit réussi
- Tous les participants cohérents

**Limite** : 2PC est blocking. Si le coordinator tombe pendant prepare, les participants restent bloqués. Voir `test.2pc.abort` pour le chemin abort.

---

## 12. `test.2pc.abort`

**Description** : Prouve que le protocole 2PC abort correctement (prepare → abort si un participant vote non).

**Schéma** : Même format que `test.lock.cross-process`.

**Protocole** :
1. Initier une transaction 2PC
2. Phase 1 (prepare) : au moins un participant vote non
3. Phase 2 (abort) : le coordinator abort
4. Vérifier qu'aucun participant n'a commité

**Critères d'acceptation** :
- Prepare échoué (au moins un vote non)
- Abort réussi
- Aucun participant n'a commité

**Limite** : Ne prouve pas le comportement sous crash du coordinator pendant prepare.

---

## 13. `test.unknown-outcome.blocks`

**Description** : Prouve qu'un résultat UNKNOWN bloque la transition (fail-closed).

**Schéma** : Même format que `test.lock.cross-process`.

**Protocole** :
1. Provoquer un résultat UNKNOWN (timeout, perte de réponse)
2. Vérifier que l'opération passe en `human_review`
3. Vérifier que la reprise est bloquée (HARD_VETO ou HOLD)

**Critères d'acceptation** :
- État = `UNKNOWN` → `human_review`
- Reprise bloquée
- Aucun effet produit pendant l'incertitude

**Limite** : Ne prouve pas que la réconciliation finit par résoudre (voir liveness).

---

## 14. `test.unknown-outcome.proceeds`

**Description** : Prouve qu'un résultat UNKNOWN laisse passer la transition (fail-open).

**Schéma** : Même format que `test.lock.cross-process`.

**Protocole** :
1. Provoquer un résultat UNKNOWN
2. Vérifier que l'opération passe (pas de blocage)

**Critères d'acceptation** :
- État = `UNKNOWN` → transition autorisée
- Effet produit

**Limite** : Fail-open est dangereux. Cette preuve documente le comportement, ne le certifie pas comme sûr.

---

## 15. `test.unknown-outcome.escalates`

**Description** : Prouve qu'un résultat UNKNOWN déclenche une escalade humaine.

**Schéma** : Même format que `test.lock.cross-process`.

**Protocole** :
1. Provoquer un résultat UNKNOWN
2. Vérifier que l'escalade est déclenchée (notification, ticket, etc.)

**Critères d'acceptation** :
- État = `UNKNOWN` → `human_review`
- Escalade déclenchée
- Pas d'effet produit en attendant la résolution humaine

**Limite** : Ne prouve pas que l'escalade est reçue par un humain.

---

## 16. `provider.contract.reference`

**Description** : Référence documentée au contrat du provider externe pour l'idempotency.

**Schéma** :
```yaml
provider: <string>
contract_url: <url>
idempotency_mechanism: <string>       # description
verified_date: <ISO-8601 date>
```

**Protocole** : Fourni par l'opérateur. Référence la documentation du provider.

**Critères d'acceptation** :
- `contract_url` valide
- `idempotency_mechanism` décrit

**Limite** : Ne prouve pas que le provider respecte son contrat.

---

## Tableau récapitulatif

| Evidence type | Capacité(s) | Preuve requise | Test automatique |
|---|---|---|---|
| `deployment.manifest` | cap.host.* | Manifeste de déploiement | Non (opérateur) |
| `test.lock.cross-process` | cap.concurrency.file-lock | Log pytest inter-processus | Oui |
| `test.idempotency.local` | cap.dedup.local-registry | Log pytest déduplication locale | Oui |
| `test.idempotency.distributed` | cap.dedup.consensus-registry | Log pytest déduplication distribuée | Oui |
| `test.idempotency.provider` | cap.dedup.provider-key | Test provider + référence contrat | Oui |
| `test.consensus.safety` | cap.concurrency.consensus, cap.dedup.consensus-registry | Linearizability + I8 + accord + validité | Oui |
| `test.consensus.liveness` | cap.concurrency.consensus, cap.dedup.consensus-registry | Terminaison sous quorum | Oui |
| `test.fault-tolerance` | cap.concurrency.consensus | Safety sous fautes injectées | Oui |
| `test.cross-host.communication` | cap.host.multi-host | Communication inter-hôtes | Oui |
| `test.mutex.exclusion` | cap.concurrency.thread-lock | Exclusion mutuelle intra-process | Oui |
| `test.2pc.commit` | cap.concurrency.distributed-transaction | Commit 2PC | Oui |
| `test.2pc.abort` | cap.concurrency.distributed-transaction | Abort 2PC | Oui |
| `test.unknown-outcome.blocks` | cap.uncertainty.fail-closed | UNKNOWN → blocage | Oui |
| `test.unknown-outcome.proceeds` | cap.uncertainty.fail-open | UNKNOWN → passage | Oui |
| `test.unknown-outcome.escalates` | cap.uncertainty.human-escalation | UNKNOWN → escalade | Oui |
| `provider.contract.reference` | cap.dedup.provider-key | Référence contrat provider | Non (opérateur) |
