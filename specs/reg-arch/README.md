# REG-ARCH — registre de la spécification d’architecture

Cette arborescence accueille la **spécification d’architecture REG Lifecycle**. Elle est distincte des contrats de tests, profils et preuves de conformité de `reg-conformance`.

## Autorité et statuts

- `v0.1/REG-ARCH-transcription.md` : transcription intégrale du texte extrait du document DOCX fourni le 24 octobre 2026, **document de travail**. Les tableaux et la mise en page doivent être confrontés au DOCX d’origine avant promotion.
- `v0.1/amendments/note-5.1.1-two-kernel.md` : proposition d’ajout ciblée à la section 5.1, **non encore adoptée**.
- La version v0.1 d’origine est explicitement une **« Proposition normative — à valider sur implémentation »**, et son autorité d’approbation reste à désigner.

## Règles de gouvernance proposées

1. `REG-ARCH` spécifie l’architecture (lanes, cycles, portes, événements et frontières) ; `reg-conformance` produit des contrôles et des preuves limités à leur périmètre. Une réussite de tests ne modifie pas d’elle-même la norme.
2. Chaque amendement doit référencer la section, l’exigence et la version visées ; passer en revue les conséquences pour Lane A, B, C et l’extériorité.
3. Une version approuvée doit être gelée, traçable (commit/tag) et ne pas être modifiée rétroactivement. Toute nouvelle règle exige un amendement/version.
4. Ne pas promouvoir une transcription en **source de référence approuvée** avant contrôle intégral contre le DOCX, désignation de l’autorité d’approbation et décision tracée.
5. Les implémentations (dont TENIR-Gov), le site web et les documents de conformance doivent **citer la version exacte** de REG-ARCH qu’ils revendiquent.

## Étapes avant promotion

- [ ] Joindre l’original DOCX au dépôt et comparer son contenu complet avec la transcription.
- [ ] Restaurer les tableaux et la typographie dans un Markdown sémantiquement fidèle.
- [ ] Valider ou corriger la note 5.1.1 ; l’incorporer dans la version suivante ou un amendement publié.
- [ ] Désigner l’autorité d’approbation et consigner la décision.
- [ ] Mettre à jour les références croisées et les contrôles de cohérence documentaire.

Ce dépôt n’atteste **aucune conformité d’une implémentation** par la seule présence de ces fichiers.
