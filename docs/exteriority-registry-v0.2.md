# REG — Registre d'extériorité v0.2

Brouillon · Abdelaziz Skiredj, TENIR Labs · 30 octobre 2026

## 1. Objet

Ce registre liste ce que REG ne gouverne pas, et dit pour chaque zone ce que REG affirme et n'affirme pas à sa frontière. Règle unique : REG ne revendique rien au-delà de son propre enregistrement.

## 2. Format d'une entrée

Chaque entrée porte les mêmes champs : **Zone**, **REG affirme**, **REG n'affirme pas**, **Contrat d'interface**, **Propriétaire**, **Porte** (condition de refus), **Statut**.

Vocabulaire de statut : *cible* (pas encore construit), *spécifié* (écrit, non instancié), *outillé* (instancié, avec lien vers la preuve).

## 3. Entrées

### E1 · Fournisseur d'un effet externe (ex. paiement)
- **REG affirme** : la décision d'admission, la tentative d'exécution, la clé ONCE consommée et le reçu.
- **REG n'affirme pas** : que l'effet a eu lieu chez le fournisseur.
- **Contrat d'interface** : REG transmet une requête avec clé d'idempotence ; une absence de réponse donne l'état UNKNOWN (HOLD). La réconciliation est faite en aval.
- **Propriétaire** : l'effet appartient au fournisseur ; l'intégration, à l'opérateur ; le reçu, à REG.
- **Porte** : UNKNOWN → CONFIRMED est interdit sans réconciliation externe.
- **Statut** : spécifié.

### E2 · Approbation humaine (voie ambre)
- **REG affirme** : qu'une approbation référencée a été enregistrée (qui, canal, horodatage, lien avec l'intention).
- **REG n'affirme pas** : que l'approbateur était qualifié, informé ou libre de refuser.
- **Contrat d'interface** : le canal (email, ticket) reste hors REG ; REG consomme une référence et un hash.
- **Propriétaire** : l'organisation cliente.
- **Porte** : pas d'approbation référencée, pas de passage à l'admission pour une action de classe ambre.
- **Statut** : spécifié.

### E3 · Autorité d'admission des invariants
- **REG affirme** : qu'un invariant porte une version et une décision d'admission enregistrée.
- **REG n'affirme pas** : que l'invariant est juste, suffisant ni conforme à une norme.
- **Contrat d'interface** : l'admission est une décision humaine nommée, avec relecteur, date et version du catalogue.
- **Propriétaire** : TENIR Labs en **phase 0** (éditeur unique, v0.x). Transfert prévu à un comité RFC en **phase 1** (v1.0+), conditionné à la signature écrite de 3 co-auteurs et à la publication de la règle de décision.
- **Porte** : voir 4.1. En phase 0, la porte exige une signature nominative référencée par `decision_ref`.
- **Statut** : **spécifié** pour la phase 0 ; **cible** pour la phase 1.

### E4 · Registre d'engagements (Point of No Return)
- **REG affirme** : qu'une entrée d'engagement a été créée de manière append-only, avec un horodatage et une référence à l'action source.
- **REG n'affirme pas** : qu'une nouvelle approbation (ou un bouton Undo) puisse révoquer l'engagement physique déjà réalisé.
- **Contrat d'interface** : l'engagement est immuable. La compensation est une nouvelle entrée dans le registre.
- **Propriétaire** : l'opérateur ; la trace, REG.
- **Porte** : un Undo sur une action déjà exécutée doit être rejeté s'il tente de supprimer l'entrée. Il doit générer une nouvelle entrée `COMPENSATION`.
- **Statut** : **cible**.

### E5 · Guichet et dossiers (La soudure Lane A → Lane B)
- **REG affirme** : qu'un refus clôt la demande. Qu'un nouveau SHA crée un **nouveau dossier**.
- **REG n'affirme pas** : que le client a bien soumis la bonne version.
- **Contrat d'interface** : le guichet associe un dossier à un `SHA` spécifique. La clôture est une transition distincte du refus (REG-ARCH-010).
- **Propriétaire** : l'équipe d'opération ; l'enregistrement, REG.
- **Porte** : un `SHA` différent = nouveau dossier. Un refus ne peut pas être "annulé" ; il est clos.
- **Statut** : **spécifié**. Source : règles du guichet 01-05.

### E6 · Configurateur de catalogue (Génération dérivée)
- **REG affirme** : que le fichier de configuration a été généré à partir du catalogue versionné, avec une provenance traçable.
- **REG n'affirme pas** : que le catalogue source n'a pas été modifié manuellement avant la génération.
- **Contrat d'interface** : génération idempotente à partir de `catalog_version`. Si un humain modifie le JSON généré sans mettre à jour le catalogue, le hash de provenance devient invalide.
- **Propriétaire** : l'équipe d'architecture ; le script de génération, REG.
- **Porte** : si le hash du fichier généré diffère du hash attendu, la porte de provenance (G-12) refuse la circulation.
- **Statut** : **spécifié**. Source : configurateur v2.

### E7 · Badge et artefacts de représentation (Lane C)
- **REG affirme** : qu'un badge reflète l'état du système au moment de la génération, avec sa chaîne de supersession.
- **REG n'affirme pas** : que le badge est vrai pour toutes les actions futures.
- **Contrat d'interface** : chaque badge doit porter sa frontière, sa date, et son SHA. La circulation d'un badge sans frontière est refusée (REG-ARCH-023).
- **Propriétaire** : l'équipe de publication ; la véracité du statut, REG.
- **Porte** : si le badge est affiché sans ses métadonnées de frontière, il est considéré comme un artefact invalide (G-12).
- **Statut** : **outillé**. Source : `badge.py` (5 états).

## 4. Les trois corrections

### 4.1 Segment « invariant admis » et soudure prétention → action
La Lane A se termine par un segment **invariant admis**, après « testé » et avant « capacité réclamée ». La soudure avec la Lane B est une porte : l'admission en Lane B n'évalue que des invariants **admis et versionnés**. Un invariant candidat, testable ou testé n'est pas appliqué.

### 4.2 Registre d'engagements : cible, non preuve
Définition cible : un registre append-only où aucune entrée n'est révoquée ; une correction est une nouvelle entrée. Statut : **cible** (voir E4).

### 4.3 Critère de suffisance
Le critère est : **chaque passage entre lanes est une porte nommée avec une condition de refus.**

| Passage | Porte | Refus |
| --- | --- | --- |
| Lane A → pont | revue humaine ; falsifiabilité | propriété non testable |
| Pont → Lane B | invariant admis et versionné | invariant candidat ou testé |
| Lane B → Lane C | état atteint avant tout livrable | état non atteint, pas de livrable |
| Toute lane → Inconnu | non-infération ; fail-closed | passage à « confirmé » sans réconciliation |

## 5. Points ouverts et vérifications
- Nommer l'autorité d'admission (E3) : **résolu en phase 0** (TENIR Labs).
- Fixer les propriétaires par déploiement (E1, E2).
- **Corriger E4 (PNR)** : le bouton Undo doit être retiré ou redéfini comme une compensation.
- Vérifier les numéros de version et les références externes avant toute publication.
