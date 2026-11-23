# REG-ARCH — registre de la spécification d'architecture

Ce répertoire est la source de REG-ARCH, la spécification d'architecture de REG : lanes, cycles de vie, portes, événements et frontières. Il est distinct des contrats de test, des profils et des preuves de `reg-conformance` : une réussite de tests ne modifie pas la norme.

## Autorité et source

| Élément | Valeur |
| --- | --- |
| Autorité d'approbation | Abdelaziz Skiredj (décision GOV-01) |
| Source | Ce répertoire, sur la branche `main` de `skiredj-prog/reg-conformance` (décision GOV-02) |
| Version ratifiée | Aucune à ce jour |

## Versions

| Version | Statut | Emplacement |
| --- | --- | --- |
| v0.4.1 candidate | Candidate, non ratifiée. Version de travail la plus récente. | [`v0.4.1-candidate/REG-ARCH.md`](v0.4.1-candidate/REG-ARCH.md) ; origine figée : [`audits/reg-arch-v0.4.1/`](../../audits/reg-arch-v0.4.1/) |
| v0.4 | Non ratifiée. Base de la candidate v0.4.1. | [`audits/reg-arch-v0.4.1/source/`](../../audits/reg-arch-v0.4.1/source/) |
| v0.2, v0.3 | Non ratifiées. Absentes de ce répertoire. | — |
| v0.1 | Document de travail. La préface de la v0.4 déclare que celle-ci s'y substitue. | [`v0.1/REG-ARCH-transcription.md`](v0.1/REG-ARCH-transcription.md) ; note 5.1.1, non adoptée : [`v0.1/amendments/`](v0.1/amendments/) |

Aucune de ces versions ne peut être citée comme norme en vigueur.

## Préséance des sources et conservation de la lignée

1. **Registre canonique :** ce fichier, sur `main` de `reg-conformance`, est le seul index faisant foi pour l'autorité, les décisions, les versions et leurs statuts.
2. **Lecture et citation :** `specs/reg-arch/v0.4.1-candidate/REG-ARCH.md` est la seule transcription publiée de la candidate. Elle est **dérivée**, non rédigée indépendamment.
3. **Origine textuelle vérifiable :** `audits/reg-arch-v0.4.1/REG-ARCH_v0.4.1-candidate.docx` est l'entrée figée du générateur ; le DOCX v0.4 est également conservé dans `audits/reg-arch-v0.4.1/source/`. Le contrôle COH-X06 exige l'identité de régénération et des mots. En cas de divergence, de perte d'une entrée, ou de contrôle impossible, **aucune copie n'est promue automatiquement** : `CANNOT_EVALUATE` / HOLD.
4. **Lignée historique :** `draft/reg-arch-v0.4.1-candidate` et `docs/reg-arch-v0.1-source` sont les branches d'origine et de provenance documentaire ; elles ne constituent pas des sources normatives concurrentes après la fusion. Les conserver, les marquer historiquement archivées, ne pas les supprimer.
5. **Future source Markdown :** la règle 6 ci-dessous demeure une **proposition** pour v0.5, pas une migration déjà décidée.

## Statut d'applicabilité et frontière de preuve

**Source canonique établie à la fusion de ce registre sur `main` ; aucune version ratifiée ; couverture de conformité exécutable du runtime pour REG-ARCH-001–024 non démontrée ; applicabilité normative : NON.**

La candidate présente des contrats et des oracles de **modèle**. Ceux-ci ne démontrent ni le raffinement ni la conformité d'une implémentation TENIR-Gov. L'absence de machines d'états applicables au runtime demeure une lacune à traiter. Les exigences 025–027 de la candidate restent également non ratifiées. Le fait de clôturer le sprint 0 n'ouvre aucun droit de revendication normative.

## R-E — Obligation probatoire des contrôles (règle d'outillage)

L'absence de la chose qu'un contrôle est appelé à vérifier n'est jamais une absence de problème. Chaque contrôle émet un statut explicite : `PASS`, `FAIL`, `CANNOT_EVALUATE` ou `NOT_APPLICABLE`. `CANNOT_EVALUATE` est non-passant et ne peut être neutralisé par la baseline ; `NOT_APPLICABLE` requiert une déclaration explicite du périmètre par l'appelant, jamais l'inférence d'un fichier absent. Lorsque c'est possible, les tests négatifs sont eux-mêmes qualifiés par mutation du comportement fautif, avec journal archivé. Cette règle gouverne l'**outillage de preuve**, sans ratifier une version de REG-ARCH.

## Contradiction historique consignée — ESCALATED (non résolue)

- **Source antérieure alléguée :** page « Sortie de l'état ESCALATED », datée du 17 novembre 2026, actuellement **hors dépôt**. URL / identifiant de l'artefact **à verser** ; sa teneur exacte ne peut pas être opposée sans cette pièce.
- **Source postérieure déposée :** `glossary/glossary-v1.yaml` (PR #79, 20 novembre 2026), **brouillon non normatif**. Projection proposée : label runtime `ESCALATED` → état constaté `UNKNOWN`, avec réconciliation requise.
- **Lecture provisoire :** `ESCALATED_CLOSED` ne devient pas un nouvel état canonique ; la clôture administrative est à représenter comme **événement journalisé**, sans qualifier automatiquement l'issue.
- **État :** `CONTRADICTION_RECORDED / PROVISIONAL_MAPPING / HISTORICAL_SOURCE_PENDING`, **pas « resolved »**. À revoir à réception de la pièce historique et lors de l'arbitrage du glossaire.

## Transcription de la candidate

`v0.4.1-candidate/REG-ARCH.md` est généré depuis le DOCX de la candidate par `tools/reg_arch_markdown.py`. Il ne se modifie pas à la main : toute évolution du texte relève de la version suivante.

```
python tools/reg_arch_markdown.py --check
```

Ce contrôle vérifie deux choses : la régénération redonne le fichier déposé à l'octet près, et les mots du Markdown sont ceux du DOCX, dans le même ordre. Il ne dit rien de la justesse de la spécification.

## Règles de gouvernance

Les règles 1 à 5 reprennent le registre établi avec la v0.1. La règle 6 est proposée ; elle sera confirmée ou écartée avec la v0.5.

1. REG-ARCH spécifie l'architecture ; `reg-conformance` produit des contrôles et des preuves limités à leur périmètre.
2. Chaque amendement référence la section, l'exigence et la version visées, et passe en revue ses conséquences pour les lanes A, B et C et pour l'extériorité.
3. Une version ratifiée est gelée, étiquetée et jamais modifiée rétroactivement. Toute nouvelle règle exige un amendement ou une nouvelle version.
4. La ratification est une décision de l'autorité d'approbation, inscrite au journal ci-dessous avec le commit et l'étiquette concernés. La présence d'un fichier dans ce répertoire ne vaut pas ratification.
5. Les implémentations (dont TENIR-Gov), le site et les documents de conformité citent la version exacte de REG-ARCH qu'ils revendiquent, avec son statut. Une candidate se cite comme candidate.
6. Proposée : à partir de la v0.5, le texte est rédigé en Markdown dans ce répertoire ; DOCX et PDF en sont dérivés.

## Journal des décisions

| Réf. | Date | Décision | Décidée par |
| --- | --- | --- | --- |
| GOV-01 | 2026-11-17 | L'autorité d'approbation de REG-ARCH est Abdelaziz Skiredj. | Abdelaziz Skiredj |
| GOV-02 | 2026-11-17 | La source de REG-ARCH vit sur GitHub, dans ce dépôt. | Abdelaziz Skiredj |

## Avant toute ratification

- [x] Désigner l'autorité d'approbation et consigner la décision (GOV-01).
- [x] Joindre au dépôt les DOCX d'origine de la v0.4 et de la candidate v0.4.1.
- [x] Disposer d'une transcription Markdown de la candidate, contrôlée contre son DOCX.
- [ ] Joindre le DOCX d'origine de la v0.1, ou acter que sa transcription ne sera pas confrontée à l'original.
- [ ] Adopter ou écarter la note 5.1.1 (deux kernels).
- [ ] Traiter les décisions ouvertes D-01 à D-09 de la candidate, ou les déclarer hors périmètre de la version à ratifier.
- [ ] Mettre à jour les documents qui citent REG-ARCH, dont `tenir-gov-scope.md` dans `tenir_governance`, qui cite la v0.1.

Ce dépôt n'atteste aucune conformité d'une implémentation par la seule présence de ces fichiers.
