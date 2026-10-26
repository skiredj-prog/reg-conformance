# REG / E8 — Intake de validation des frontières conteneurisées

**Identifiant :** REG-E8-INTAKE-20261026-01  
**Date déclarée de campagne :** 26 octobre 2026  
**Origine :** compte rendu fourni par l'opérateur dans la conversation ; rapports bruts non joints  
**Référence architecturale :** REG-ARCH-022 / [E8 v0.2](../specs/exteriority-e8-witness.md) ; [TENIR CB-05 / PR #77](https://github.com/skiredj-prog/tenir_governance/pull/77)  
**Statut des résultats :** `REPORTED_PASS` (7/7), **non reproduits indépendamment**, environnement non figé par SHA  
**Décision de gouvernance :** `CONTAINER_BOUNDARY_EVIDENCE_REPORTED / R01_OPEN / Q6_OPEN / PRODUCTION_HOLD`

## 1. Objet et provenance

Archiver **sans surinterprétation** les sept sondes FS/NET/KEY déclarées PASS sur une stack conteneurisée séparant un service `runtime` et un service `witness`. Le seul artefact reçu à cette date est une synthèse narrative. Aucun fichier Compose, image OCI identifiée par digest, manifeste de volumes, commande de sonde, résultat brut/JUnit, signature d'attestation E8 ou hash de preuves n'a été fourni avec ce compte rendu.

Le terme `PASS` dans les sept lignes ci-dessous signifie **« PASS déclaré par l'auteur de la campagne »**, et non un PASS de conformité E8 vérifié par ce dépôt. Il faut retenir le périmètre observé, le modèle d'attaque et le niveau de preuve séparément.

## 2. Registre des sept observations

| ID | Résultat rapporté | Observation décrite | Ce que cela démontre au plus, sous réserve de reproduction | Ce que cela ne démontre PAS |
|---|---|---|---|---|
| `FS-POS-1` | REPORTED_PASS | `runtime` UID/GID `1000:1000`, écriture réussie dans son volume dédié | Écriture non-root sur **son propre** volume | Que ce volume n'est pas le stockage G1/G4-A protégé ; exclusivité du moteur |
| `FS-NEG-1` | REPORTED_PASS | `/var/lib/tenir/witness` absent du namespace runtime | Chemin sensible non visible au point inspecté | Impossibilité absolue d'accès par d'autres chemins, sockets ou APIs |
| `FS-NEG-2` | REPORTED_PASS | `/proc/self/mountinfo` ne mentionne pas `tenir_witness_strict_volume` | Volume témoin non monté dans le conteneur inspecté | Impossibilité pour un administrateur du moteur Docker/hôte de changer les montages |
| `FS-NEG-3` | REPORTED_PASS | Écriture vers l'espace témoin refusée ; `cap_drop: [ALL]` annoncé | Le chemin d'attaque utilisé n'a pas écrit dans le témoin | Identité de la cause du refus sans errno/commande ; un ENOENT n'est pas un EACCES ; protection contre host-root/daemon Docker |
| `NET-POS-1` | REPORTED_PASS | `runtime` atteint `http://witness:8443/health` sur pont `internal: true` | Routage vers le service dans le réseau isolé | Chiffrement, authentification du témoin, intégrité des CMT ou exclusivité des membres du réseau |
| `KEY-POS-1` | REPORTED_PASS | Clé publique montée `:ro` dans `/etc/tenir-witness/witness_pub.pem` | Chemin déclaré en lecture seule dans le runtime | Impossibilité pour l'opérateur du host de remplacer la source du montage ; épingle indépendante |
| `KEY-POS-1b` | REPORTED_PASS | PEM non vide et structure cryptographique valide | Fichier de clé parsable | Correspondance de la clé avec la véritable identité du témoin ; vérification de la signature contre une racine épinglée à l'extérieur |

### Points de précision indispensables

- **`internal: true` n'implique pas TLS.** L'URL `http://witness:8443/health` n'apporte à elle seule ni chiffrement ni authentification cryptographique : le port `8443` n'est pas une preuve de HTTPS.
- **`cap_drop: [ALL]` ne neutralise pas l'administration de l'hôte.** L'étanchéité est relative à un acteur situé dans le conteneur runtime et privé de chemins d'administration/sockets privilégiés ; elle n'est pas une séparation de deux autorités indépendantes si les deux conteneurs et leurs volumes sont administrés par le même hôte.
- **L'indépendance E8** exige une autorité de confiance, une persistance, une identité et une administration du témoin hors du domaine de compromission retenu pour G1. Deux services dans le même démon Docker sont un palier de laboratoire, pas automatiquement deux domaines de confiance.
- **FS-POS-1 n'est pas un test G1** tant que la destination de l'écriture positive n'est pas distinguée du répertoire SQLite / WAL / SHM / sidecars du moteur, que le worker ne devrait pas pouvoir modifier directement.

## 3. Mapping explicite vers les risques

| Risque | Contribution des 7 sondes | Statut de fermeture |
|---|---|---|
| R-01 — écrivain local privilégié / exclusivité d'autorité | Sépare le volume *witness* du conteneur *runtime* ; aucune attaque SQL privilégiée contre la base G1/G4-A n'est exercée | **P0 OUVERT** |
| Q6 — restauration cohérente d'une quarantaine inactive | Aucun rollback du magasin local, aucune comparaison d'une tête E8 indépendante et aucun nouvel appel d'admission après restauration n'est décrit | **P0 OUVERT** |
| Q1 — suppression de marque/sentinelle | Aucune suppression/restauration suivie d'une tentative d'admission n'est décrite | **P0 OUVERT** |
| C1/C2 — rollback d'autorité / substitution de clés | Une clé est montée RO, mais le retour arrière de la tête et la substitution des racines n'ont pas été soumis à un vérificateur externe indépendant | **P0 OUVERT** |
| NET/FS/KEY — configuration de base des conteneurs | Sept vérifications positives/négatives rapportées | **Configuration testée — preuves brutes en attente** |

**Aucune fermeture de P0 n'est prononcée sur la seule base des sept lignes.** Le témoin externe n'a pas encore été démontré comme *précondition synchrone de chaque admission critique*. Voir INT-E8-01 dans la [matrice TENIR conjointe](https://github.com/skiredj-prog/tenir_governance/blob/draft/cb05-independent-checkpoint-architecture/docs/g4a/G1_E8_CB05_G4A_JOINT_CONFORMANCE_MATRIX_v0.1.md).

## 4. Pièces minimales requises avant promotion probante

Conserver et lier par SHA-256 à la **même exécution** :

1. SHA du dépôt de la stack ; fichier(s) Compose effectivement appliqués et rendu `docker compose config` **expurgé des secrets** ; identité du moteur Docker, hôte/OS, volume drivers, réseaux et leur portée.
2. Digests OCI des images, UID/GID effectifs, `CapEff`/`CapBnd`, montages effectifs du runtime et du témoin, chemin du socket Docker absent ou disposition justifiée.
3. Commandes exactes FS-POS/NEG, sorties, `exit_code`, `errno` quand disponible, horodatage, preuve qu'aucune écriture témoin n'a eu lieu.
4. Captures des contrôles NET ; politique de canal et identité du témoin authentifiée **distinctes** de l'atteignabilité de `/health`.
5. Empreinte de clé publique Ed25519 et preuve que l'empreinte attendue était provisionnée sur un canal indépendant du runtime, plus essai de substitution de clé.
6. Logs signés de CMT et tête monotone du témoin, état/quarantaine locale avant-après une attaque Q6/Q1, décision d'admission et compteur d'effets externes.
7. Manifeste SHA-256 des rapports, identité/opérateur des essais et, pour qualifier l'indépendance, relecture/reproduction par un acteur distinct.

## 5. Porte de décision

- **Maintenant :** `7/7 REPORTED_PASS` sur l'isolation conteneurisée, sans archive brute ni attestation d'un second opérateur.
- **Après reproduction :** `CONFIG_BOUNDARY_VERIFIED` seulement pour le modèle de menace précisément testé, si les négatifs FS/NET/KEY sont confirmés.
- **Pour R-01 :** tests de mutation de SQLite et de ses sidecars depuis les UIDs non autorisés, chemins privilégiés et scripts réels (G1) ; absence de modification démontrée.
- **Pour Q6/Q1 :** restauration/suppression de quarantaine puis tentative de nouvelle admission, rejet synchrone via ancrage indépendant `compare-and-advance`, et absence de mutation métier/dispatch.
- **Pour l'indépendance E8 :** provisionnement de clé et tête sur une autre autorité/hôte ou domaine réellement indépendant, canal authentifié, tests de fork/replay/partition et reprise après crash.

**REG n'affirme rien au-delà des preuves archivées. PRODUCTION HOLD.**
