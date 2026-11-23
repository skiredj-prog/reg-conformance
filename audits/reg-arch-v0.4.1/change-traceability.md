# Matrice de traçabilité des amendements — REG-ARCH v0.4 → v0.4.1 candidate

La candidate locale est une proposition amendée non ratifiée. La matrice trace les modifications vers les ruptures observées dans le PDF v0.4 et vers des oracles de contrat. Les oracles exécutables portent sur un modèle abstrait, pas sur une implémentation.

| ID | Constat v0.4 | Amendement candidate | Relation / preuve attendue | Oracle reproductible | État |
|---|---|---|---|---|---|
| P0.1 | 010bis exige un Écart, mais permet une transition informelle ; G-Écart non définie (010bis, 007, D-02) | 010bis réécrite ; REG-ARCH-025 définit contrôleur réservé, liaison de capacité, version active, schéma de trace, clé déterministe, atomicité et reprise idempotente | Refus journalisé à contexte nul; collision trace le contexte courant, motif, empreinte SHA-256(JCS/RFC 8785) du préimage exact de 17 propriétés et événement précédent; précommit sans création partielle; postcommit/ACK perdu/retry | A-11/A-12/A-24/A-25/A-26; tests de schéma, refus, collision, recomputation indépendante de l’empreinte et drift version/manifeste | Correctif après revue 8; revue indépendante 9 en cours; preuve d’identité déployée reste externe |
| P0.2 | Appendice prescriptif sans statut ; relation REG-ARCH/REG/REG+/TENIR-Gov évoque équivalence sans contrat (Appendice §§1–3, 001–024) | Appendice v0.4 remplacé par une note générique nonnormative; REG-ARCH-026 impose abstraction, appariement des transitions, couverture refus/erreur et hypothèses vérifiées | Trace permise acceptée, transition interdite contredite; pas de preuve exhaustive à partir des seuls tests finis | A-16/A-17 | Correction après revue #3; revue indépendante 5 en cours |
| P0.3 | Pas de graphe de dépendances, propagation PREVENT ni invalidation `STALE` (008, 014, 015, 024, Appendice P1/P6) | REG-ARCH-027 définit manifeste fermé, inventaire indépendant, epoch, reprise idempotente, usage linéarisable, comparaison du digest, `STALE` et requalification | Entrée effective non déclarée échoue; ancienne epoch/digest non consommable; retry même epoch; preuve nouvelle liée au manifest courant | A-13/A-14/A-15/A-18/A-19/A-20/A-21/A-22/A-23 | Correction post-review #3; revue indépendante 5 en cours |
| P1.1 | Rapport v0.4 incohérent sur PDF fourni ; A-11/A-12 absents du YAML | Copies source hashées et contrôlées par builder ; statut candidate rectifié ; A-11 à A-23 documentés | SHA-256 à chaque génération ; 17 tests du modèle | Hashs et tests dans README | Contrôlé localement |
| D-01..D-09 | Décisions laissées ouvertes dans v0.4 | Toutes restent ouvertes ; D-02 ne décide plus si G-Écart existe, mais reste ouverte pour automates complets | La candidate ne transforme pas une décision métier en règle implémentation | §18 du document candidate | OUVERTES |

## Sens des états PREPARE/PREVENT

`DÉMONTRÉ` signifie que le contrat ou la relation possède une preuve contrôlable dans le périmètre déclaré. `CONDITIONNEL` signifie qu’une hypothèse explicite reste à satisfaire. `MANQUANT` signifie qu’une relation ou obligation normative n’existait pas. `INVALIDE` signifie qu’une contradiction ou relation fausse est établie. Les tests du modèle n’élèvent aucun de ces états pour une implémentation particulière.

| Depuis → vers | PREPARE descendant | PREVENT ascendant | v0.4.1 candidate |
|---|---|---|---|
| Exigence → garantie | Résoudre les garanties revendiquées | Identifier les garanties impactées par changement d’exigence | Normatif via 026/027, preuves d’application requises |
| Garantie → obligations | Énumérer obligations requises | Propager changement d’obligation vers les garanties | Normatif via 026/027 |
| Obligation → porte/règle | Vérifier règle/porte et version | Détecter règle modifiée/révoquée | Normatif via 026/027 |
| Porte/règle → profil | Contrôler correspondance et snapshot | Invalider profils dépendants | Normatif si relation déclarée ; exactitude du mapping doit être prouvée |
| Profil → configuration | Vérifier la configuration résolue | Impacter les hypothèses/configurations dérivées | Normatif via 027 |
| Configuration → hypothèse | Valider satisfaction par configuration exacte | Marquer hypothèses invalidées et garanties aval | Normatif via 027; satisfaction empirique conditionnelle à la méthode |
| Configuration → preuve | Confirmer les versions exactes | Marquer STALE/ancienne époque et bloquer toute lecture | Normatif via 027 ; A-19 teste la course |
| Preuve → verdict | Refuser preuve périmée/insuffisante | Invalider verdict dérivé avant publication/consommation | Normatif via 027 |

## Résultat des passes indépendantes 1–9

P0.1 et P0.2 : **SUPPORTED au niveau du contrat normatif pour les scénarios couverts**. P0.1 reste conditionnel pour les preuves d’identité, persistance et atomicité d’un déploiement; le validateur JSON Schema local et le modèle JCS Python sont des contrôles partiels. P0.2 ne démontre aucun raffinement concret : celui-ci reste UNVERIFIABLE sans preuve spécifique.

P0.3 : **CONDITIONAL**. Le mécanisme normatif et ses courses modélisées sont définis; il faut encore une méthode et des preuves propres au périmètre démontrant l’exhaustivité de l’inventaire effectif et la validité empirique des hypothèses. La candidate ne ferme donc pas les preuves de garantie d’un système particulier.

Le graphe seul établit la traçabilité, pas la validité d’une relation. La validité demande une justification vérifiable de chaque arc ; la garantie effective demande en plus preuves suffisantes et hypothèses satisfaites. Toute étape non prouvée bloque `SUPPORTED`.
