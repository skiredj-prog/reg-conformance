# Proposition d’amendement REG-ARCH — Note 5.1.1

**Document visé :** REG-ARCH v0.1 · §5.1, après REG-ARCH-007 et avant §5.2.  
**Statut :** Proposition non adoptée ; ne modifie pas la norme tant que l’autorité compétente ne l’a pas approuvée.

## Note 5.1.1 — Le deux-kernel est une implémentation, pas une prescription

REG-ARCH-007 exige une porte explicite avec identité, conditions, refus et les autres champs prévus au contrat. Il n’exige pas que cette porte résulte de deux kernels composés.

TENIR-Gov compose un scoring continu (évaluation de conditions graduées) et une membrane discrète (évaluation d’invariants). Cette composition **vise à produire** des décisions de passage répondant à REG-ARCH-007. Sa conformité effective exige la vérification du contrat complet de la porte et des preuves associées.

Un implémenteur alternatif PEUT satisfaire REG-ARCH-007 par une porte unique, trois composants ou un autre mécanisme, pour autant que les exigences observables de la spécification soient effectivement satisfaites. Le deux-kernel est un choix de TENIR-Gov, non une forme requise de toute porte conforme.

## Motif et garde-fous

Clarifier la neutralité d’implémentation de REG-ARCH sans transformer un choix de conception TENIR-Gov en norme universelle. Ne vaut pas constat de conformité de TENIR-Gov, ni nomination de l’autorité d’admission.
