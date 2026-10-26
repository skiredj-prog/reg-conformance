# REG-ARCH-022 — Plan de tests E8 : frontières conteneurs et pré-autorisation

**Version :** 0.1 / 26 octobre 2026  
**État :** spécification de tests ; non exécutée depuis ce dépôt  
**Campagne d'origine :** [intake des 7 sondes](../evidence/e8/CONTAINER_BOUNDARY_INTAKE_2026-10-26.md)  
**Contrat supérieur :** [E8 v0.2](exteriority-e8-witness.md), [TENIR G1 × E8/CB-05 × G4-A](https://github.com/skiredj-prog/tenir_governance/blob/draft/cb05-independent-checkpoint-architecture/docs/g4a/G1_E8_CB05_G4A_JOINT_CONFORMANCE_MATRIX_v0.1.md)

## 1. Qualification des essais

Les sondes `FS`, `NET` et `KEY` ci-dessous sont **des tests de déploiement/intégration**, et non des unit tests de fonctions Python. Les tests cryptographiques de validation d'une signature, de comparaison d'empreintes et de logique de rejet peuvent être unitaires avec des fixtures locales ; ils ne prouvent pas, seuls, une séparation de domaines d'administration.

Niveaux de qualification, sans promotion implicite :
- `REPORTED_PASS` : déclaration sans logs/artefacts reproductibles dans ce dépôt.
- `ENVIRONMENT_PASS` : résultat d'une suite de déploiement avec configuration et traces vérifiables.
- `SIMULATED_INTEGRATION_PASS` : expérience same-host ou témoin mocké ; jamais `E8_INDEPENDENCE_PASS`.
- `INDEPENDENT_ADVERSARIAL_PASS` : tests négatifs multi-domaines, SHA figés, identité du vérificateur indépendante.
- `NOT_RUN` / `FAIL` / `SKIP` : P0 non fermé.

**Modèle de menace à documenter :** T0 processus applicatif dans `runtime` sans privilèges ; T1 worker séparé du G1 engine ; T2 acteur privilégié modifiant la base locale/quarantaine ; T3 administrateur de la plateforme Docker/hôte ; T4 compromission du témoin. Ne jamais attribuer à T2/T3/T4 un résultat obtenu seulement face à T0.

## 2. Contrat des sept sondes initiales

| ID | Préconditions et stimulus vérifiable | Oracle PASS | Traces obligatoires | Niveau |
|---|---|---|---|---|
| FS-POS-1 | Lancer le service `runtime` UID/GID 1000:1000 ; tenter create/fsync/unlink dans son volume **non sensible** | Succès sur ce volume ; identité effective démontrée | `id`, `stat`, commande, code sortie et nom exact du montage | Déploiement T0 |
| FS-NEG-1 | Depuis runtime, inspecter `/var/lib/tenir/witness` puis rechercher d'éventuels chemins alternatifs | Chemin absent ; aucune vue sensible accessible | `stat`/erreur, mounts, inspect Compose ; distinction ENOENT/EACCES | Déploiement T0 |
| FS-NEG-2 | Lire `/proc/self/mountinfo` depuis le runtime et recouper avec les montages OCI | Volume `tenir_witness_strict_volume` non monté dans runtime | Sortie brute filtrée + inspect des mounts du conteneur | Déploiement T0 |
| FS-NEG-3 | Tenter create/write/rename via chemins supposés de témoin depuis le runtime | Aucune mutation témoin ; errno et mécanisme explicités | Commandes + stderr/errno + état témoin avant/après, `CapEff` | Déploiement T0 |
| NET-POS-1 | Accéder `http://witness:8443/health` depuis le réseau dédié ; inspecter attachements | Health accessible uniquement selon politique d'exposition attendue | Inspect réseau, réponses et codes HTTP, ports publiés | Déploiement T0 — **non cryptographique** |
| KEY-POS-1 | Vérifier mount `:ro`, perms et ouverture en lecture de `/etc/tenir-witness/witness_pub.pem` | Fichier accessible lecture, mutation depuis runtime refusée | `mountinfo`, `stat`, write negative, état source | Déploiement T0 |
| KEY-POS-1b | Parser la clé PEM en Ed25519 et comparer sa fingerprint SHA-256 à l'épingle **indépendante** | Format Ed25519 valide **et** empreinte attendue égale ; erreur sur substitution | Fingerprint attendue avec provenance externe, commande et sorties | Unitaire crypto + intégration pin |

**Attention :** la campagne rapportée ne mentionne pour KEY-POS-1b que la validité du bloc cryptographique ; l'égalité à l'empreinte de confiance est une exigence **supplémentaire, non exécutée selon les informations reçues**.

## 3. Tests complémentaires obligatoires pour prétentions de sécurité

| ID | Niveau / menace | Scénario négatif précis | Oracle / admission | Lien risque |
|---|---|---|---|---|
| FS-NEG-4 | T1 | Worker UID essaie UPDATE SQL sur base G1/G4-A, y compris WAL/SHM et remplacement du fichier parent | OS deny avant mutation ; snapshot DB vérifié | **R-01** |
| FS-NEG-5 | T2/T3 | Acteur avec droits host/engine tente de modifier le volume témoin / son attestation | Consigner ce que le modèle de menace permet ; si modification possible, **ne pas affirmer indépendance** | CB-05 |
| NET-NEG-1 | T0/T1 | Runtime essaie de joindre un service extérieur non autorisé ; service externe tente d'atteindre witness | Refus selon topology annoncée ; indépendamment de la validité CMT | Isolation NET |
| NET-NEG-2 | T0/T1 | Fausse réponse `/health` ou imitation du témoin, y compris dans le même réseau interne | Health seul ne donne aucune autorisation ; tout CMT sans signature/pin valide rejeté | E8 identité |
| KEY-NEG-1 | T2 | Remplacer le fichier de clé source par une clé Ed25519 valide, mais non autorisée | Vérification cryptographique externe du pin échoue ; HARD_HOLD, zéro admission | C2 |
| KEY-NEG-2 | T0 | Signature Ed25519 invalide, mauvais realm/store, wrong audience, expiry ou grant | Refus signé/provenant du témoin attendu ; aucune consommation de grant ni effet | C2 / J2 |
| E8-NEG-Q6 | T2 | Restaurer JSON et sentinelle de quarantaine inactive cohérente ; garder témoin courant ; demander admission réelle | Comparaison fraîche + CAS rejetant restauration ; HOLD_GLOBAL avant commit/dispatch | **Q6** |
| E8-NEG-Q1 | T2 | Supprimer marque+sentinelle après initialisation ; re-demander admission | Store ne se réinitialise pas silencieusement ; HOLD_GLOBAL avant commit/dispatch | **Q1** |
| E8-NEG-C1 | T2 | Restaurer ancienne autorité valide, tester une **nouvelle** demande jadis non admissible | Rejet de revision/epoch/head ancienne | **C1** |
| E8-NEG-C2 | T2 | Remplacer ensemble base locale et profil de clés/racines de confiance | Pin externe refuse ; signature sous clés fournies par l'attaquant n'est pas acceptée | **C2** |
| E8-NEG-CAS | T1/T2 | Deux admissions concurrentes lisent une tête identique ; autre actor révoque/quarantaine | Un seul CAS gagnant ; aucune admission sur droit révoqué au point de linéarisation | J2/J3 |
| E8-NEG-ACK | T1 | Témoin avance, réponse CMT perdue ; redémarrage et rejeu | `WITNESS_OUTCOME_UNKNOWN`, réconciliation puis pas de deuxième effet | P6 / J4/J5 |
| E8-NEG-PARTITION | T1/T3 | Partition/timeout witness avant pré-autorisation | HOLD_GLOBAL, pas de succès de substitution ni fail-open | J6 |
| E8-NEG-DISPATCH | T1/T2 | CMT valide ancien ou consommé ; changer payload ou époque avant le dispatch | Refus du CMT rejoué / invalide ; compteur provider zéro | J2/J7 |

### Test d'intégrité d'état local préalable

Comparer, dans une transaction cohérente, **les tables métier réelles, les métadonnées d'idempotence et l'état de quarantaine faisant autorité** au digest attesté, avant toute nouvelle admission. Refaire l'empreinte après les écritures avant la fin de la transaction. Modifier les données sans modifier le head en cache doit déclencher HOLD. Un fichier de head local, seul, n'est pas une mesure indépendante des données métier. La vérification doit couvrir **les tables G4-A réelles**, pas seulement les tables du prototype G1.

Le laboratoire TENIR G1/E8 dispose d'une couverture partielle de reconstruction des lignes de ses propres tables et de tests CI, mais ne doit pas être substitué à E8-NEG-Q6 ou R-01 en production.

## 4. Format d'un résultat reproductible

Pour chaque cas :
```json
{
  "case_id": "E8-NEG-Q6",
  "classification": "NOT_RUN",
  "threat_actor": "T2",
  "sut_commit_sha": null,
  "witness_commit_sha": null,
  "compose_config_sha256": null,
  "runtime_image_digest": null,
  "witness_image_digest": null,
  "independent_pin_fingerprint": null,
  "command_log_sha256": null,
  "pre_state_digest": null,
  "post_state_digest": null,
  "witness_head_before": null,
  "witness_head_after": null,
  "admission_decision": null,
  "business_write_count": null,
  "provider_call_count": null,
  "test_operator": null,
  "independent_reviewer": null
}
```

Ne pas remplir `PASS` par défaut ; conserver `NOT_RUN` tant que les artefacts n'existent pas. Une erreur de permission, absence de chemin, refus cryptographique et HOLD runtime ne sont **pas** des résultats interchangeables.

## 5. Exécution et critères de sortie

**Ordre :** (A) capturer configuration/identités/sha ; (B) reproduire sept sondes FS/NET/KEY ; (C) négatifs G1 et pin ; (D) scénarios Q1/Q6/C1/C2 sous le vrai chemin admission ; (E) races, partition et crash ; (F) relecture indépendante.

**Gate de conformité E8 :** aucun PASS de la seule configuration Docker ne ferme les risques R-01/Q6. Il faut la preuve conjointe G1 × E8/CB-05 × G4-A sur une implantation réellement indépendante, avec les preuves d'admission et d'absence d'effet. Tant que ce seuil n'est pas atteint : **P0 OPEN / PRODUCTION HOLD**.
