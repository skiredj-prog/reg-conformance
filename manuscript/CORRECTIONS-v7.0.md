# Tableau de correction — manuscrit v7.0

Statuts : VERIFIED (cohérent avec le code ou le dépôt, sur le commit indiqué) ·
VERIFIED — BOUNDED (vrai dans un périmètre déclaré) · CONTRADICTED (contredit une preuve
actuelle) · UNVERIFIED (non vérifié : valeur rapportée, pas relue) · MISSING (absent du
manuscrit alors qu'un élément est en place).

Ce fichier ne modifie pas le manuscrit. Chaque ligne est à valider avant application.

| ID | Ligne | Passage (résumé) | Statut | Constat | Correction proposée |
|---|---|---|---|---|---|
| C1 | 446 | « The committed reference outputs use depth 6 … depth 8 … » | CONTRADICTED | Les sorties v1 (`r6_*`, `r8_*`) sont désormais dans `experiments/e1_e2/historical/`, non reproductibles. Le texte les présente comme références. | « Les sorties v1 sont historiques et non reproductibles (`historical/`). La référence courante est l'artefact `e2-current-four-worlds` du run 38198777951 sur le commit d42499b de tenir-conformance-s1-g1. » |
| C2 | 450–452 | « run 37893221937, commit cf1b1ea … four E2 reference-output comparisons … matched their committed references » | UNVERIFIED + contradiction interne | Le §6.2 dit que le script courant produit des comptes différents de v1 ; ce passage dit que les sorties correspondent aux références commitées. Le run n'a pas été relu. | Qualifier ou retirer « matched » tant que le log du run n'est pas relu : « À cette date, les sorties ont été comparées aux fichiers de référence alors commités ; ces fichiers sont aujourd'hui classés historiques. » |
| C3 | 417 | Table 1, honest, depth 8, 36 892 | VERIFIED — BOUNDED | Déjà intitulée « historical projected-key baseline ». | Ajouter une ligne sous le tableau : « Historique, remplacé ; voir la référence courante (C1). » |
| C4 | 7, 43, 296, 378–386, 486–511, 541, 578, 618, 644 | Non-claims, garanties conditionnelles, bornes des modèles | VERIFIED — BOUNDED | Cohérent avec le code et les tests. | Aucune. |
| C5 | 245 | « `retry_eligible` is an audit annotation only » | VERIFIED | Confirmé par `reconcile` (commit 23afaf5) : le champ est `None`, et le garde ne le lit pas. | Aucune. |
| C6 | 482 | « S7 verifies Ed25519 signatures using the public key supplied by the caller » | VERIFIED | Confirmé par le README (trust anchor, PR #13) et `attestation.py`. | Aucune. |
| C7 | 616, 646 | `ESCALATED` absorbant, sortie non autorisée | VERIFIED | `reconcile` renvoie `RECONCILIATION_REJECTED_BAD_STATE` pour `ESCALATED`. | Aucune. |
| C8 | 659–662 | Appendice : reproduction à partir du commit 84e46d9 | VERIFIED (existence) | Le commit existe. La reproduction n'a pas été rejouée. | Aucune ; rejouer avant de citer comme reproduction. |
| C9 | (absent) | Ledger chaîné, ancre, checkpoint et limite de troncature | MISSING | Implémentés et testés dans tenir (PR #32 à #40), absents du manuscrit. La limite (troncature non détectée sans tête ancrée) doit figurer dans le texte. | Ajouter une sous-section « Evidence ledger » : chaîne de hachage, vérification croisée, ancre publiée, limite de troncature explicite. |
| C10 | 506 | « S12a–S12h exercise cross-Realm … » | VERIFIED — BOUNDED, à compléter | Les tests passent, mais aucune preuve S12 n'est archivée dans le CI (vérifié dans le workflow). | Ajouter : « Aucun artefact de preuve S12 n'est archivé par le CI ; les résultats reposent sur l'exécution des tests. » |

## Hors manuscrit, à traiter ailleurs

- Les valeurs du Hypothesis Lab (7 FAIL / 5 PASS / 1 VACUOUS) et le run #209 rapportés par
  un audit externe ne sont pas relus : UNVERIFIED tant que le fichier `expected_adversarial.json`
  et le log du run ne sont pas examinés.
- Le libellé « 40–50 % de la phase A » et les délais de 10–18 mois ne doivent pas figurer
  comme résultats ; ce sont des hypothèses de planification (voir le rapport d'audit).
