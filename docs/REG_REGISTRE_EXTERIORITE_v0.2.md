# REG — Registre d'extériorité v0.2

Brouillon · Abdelaziz Skiredj, TENIR Labs · 25 octobre 2026\n\n**Version v0.2 (draft)** : conserve les entrées E1–E3 de v0.1 ; E4–E7 restent à consolider à partir de leurs sources normatives (non inventées dans cette révision). Ajoute E8, spécifié mais non implémenté.

## 1. Objet

Ce registre liste ce que REG ne gouverne pas, et dit pour chaque zone ce que REG affirme et n'affirme pas à sa frontière. Règle unique : REG ne revendique rien au-delà de son propre enregistrement.

## 2. Format d'une entrée

Chaque entrée porte les mêmes champs : **Zone**, **REG affirme**, **REG n'affirme pas**, **Contrat d'interface**, **Propriétaire**, **Porte** (condition de refus), **Statut**.

Vocabulaire de statut : *cible* (pas encore construit), *spécifié* (écrit, non instancié), *outillé* (instancié, avec lien vers la preuve). Le mot « existe » est retiré : il ne dit pas lequel des trois.

## 3. Entrées

### E1 · Fournisseur d'un effet externe (ex. paiement)

- **REG affirme** : la décision d'admission, la tentative d'exécution, la clé ONCE consommée et le reçu, tels que journalisés par REG.
- **REG n'affirme pas** : que l'effet a eu lieu chez le fournisseur, ni que la prétention est vraie dans le monde externe. Le reçu atteste l'enregistrement de REG, pas l'effet du fournisseur.
- **Contrat d'interface** : REG transmet une requête avec clé d'idempotence ; une absence de réponse donne l'état UNKNOWN (HOLD), jamais un rejeu. La réconciliation est faite en aval (finance, conformité) à partir du reçu, avec le relevé du fournisseur, hors REG.
- **Propriétaire** : l'effet appartient au fournisseur ; l'intégration, à l'opérateur du déploiement ; le reçu, à REG. Les noms sont à fixer par déploiement.
- **Porte** : UNKNOWN → CONFIRMED est interdit sans réconciliation externe.
- **Statut** : spécifié. Source : texte d'analyse du corpus ; le carousel n'a pas été relu pour ce brouillon.

### E2 · Approbation humaine (voie ambre)

- **REG affirme** : qu'une approbation référencée a été enregistrée (qui, canal, horodatage, lien avec l'intention).
- **REG n'affirme pas** : que l'approbateur était qualifié, informé ou libre de refuser. REG ne remplace pas la décision humaine.
- **Contrat d'interface** : le canal (email, ticket) reste hors REG ; REG consomme une référence et un hash, pas le contenu.
- **Propriétaire** : l'organisation cliente.
- **Porte** : pas d'approbation référencée, pas de passage à l'admission pour une action de classe ambre.
- **Note** : cette autorité est *opérationnelle* (qui approuve, par quel canal). Elle est distincte de l'autorité *spécificatoire* de E3.
- **Clause E2 — HITL et provenance** : L'approbation humaine (HITL) est une condition nécessaire pour la classe Ambre (actions à conséquence), mais elle ne constitue en aucun cas une preuve de qualité ou de sécurité. Elle est traitée comme un mécanisme d'autorisation avec provenance. Pour que la signature ait une valeur structurelle, l'humain doit avoir un accès indépendant au contexte (le « hash » ou la donnée brute) pour éviter le biais d'automatisation. La présence d'un hash seul ne garantit toutefois ni la compréhension du contexte ni l'accès à la donnée vérifiable ; l'accès, l'identité du relecteur et le lien entre l'autorisation et l'intention doivent être vérifiés séparément. Cette clause est **spécifiée**, pas démontrée par un bouton ou une signature.

- **Statut** : spécifié. Même réserve de source que E1.

### E3 · Autorité d'admission des invariants

- **REG affirme** : qu'un invariant porte une version et une décision d'admission enregistrée.
- **REG n'affirme pas** : que l'invariant est juste, suffisant ni conforme à une norme. REG ne décide pas ce qui est admis.
- **Contrat d'interface** : l'admission est une décision humaine nommée, avec relecteur, date et version du catalogue.
- **Propriétaire** : **point ouvert**. Les leads d'architecture TENIR seuls feraient un catalogue d'éditeur ; le processus RFC avec co-auteurs en ferait un standard. À trancher.
- **Porte** : voir 4.1.
- **Statut** : cible.

### E8 · Témoin externe monotone (REG-ARCH-022)

- **REG affirme** : uniquement les transitions dont la continuité, la tête attestée et la fraîcheur ont été vérifiées auprès d'un témoin indépendant au point de décision ; aucun succès global sans confirmation du témoin.
- **REG n'affirme pas** : l'inviolabilité du témoin, la prévention des écritures locales privilégiées (G1), la reconstruction des données perdues ni l'effectivité des opérations chez un fournisseur externe (E1).
- **Contrat d'interface** : service indépendant, tête attestée `(realm_id, store_id, epoch, sequence, state_digest, key_digest, quarantine_digest, previous_head_digest)` ; lecture linéarisable et `compare_and_advance` atomique ; boot gate, transition gate et commit gate ; fail-closed.
- **Propriétaire** : opérateur de déploiement pour le service indépendant et ses clés ; gouvernance TENIR/REG pour le contrat normatif. Attribution finale à préciser par déploiement.
- **Porte** : témoin indisponible, divergent, non authentifié ou réponse incertaine → HOLD_GLOBAL / aucune nouvelle admission ; `LOCAL_COMMITTED_WITNESS_PENDING` n'est pas un succès opérationnel.
- **Statut** : **spécifié**, non implémenté, non testé officiellement. P0 R-01, Q1/Q6, C1/C2 **ouverts**.
- **Référence** : [Spécification E8 v0.2](../specs/exteriority-e8-witness.md), alignée sur TENIR CB-05.

## 4. Les trois corrections

### 4.1 Segment « invariant admis » et soudure prétention → action

La Lane A se termine par un segment **invariant admis**, après « testé » et avant « capacité réclamée ». Conditions : propriété testable, test existant, revue humaine, version (E3).

La soudure avec la Lane B est une porte : l'admission en Lane B n'évalue que des invariants **admis et versionnés**. Un invariant candidat, testable ou testé n'est pas appliqué. Refus : tout invariant non admis présenté à l'admission est rejeté.

### 4.2 Registre d'engagements : cible, non preuve

Définition cible : un registre append-only où aucune entrée n'est révoquée ; une correction est une nouvelle entrée. Statut : **cible**.

Le Point of No Return v0.2 n'est pas une preuve de cet objet. C'est une scène pédagogique fictive dont le bouton Undo retire l'entrée du registre. Il peut illustrer l'idée, pas l'établir.

### 4.3 Critère de suffisance

Le critère « chaque objet suit un seul trajet » est abandonné. Nouveau critère : **chaque passage entre lanes est une porte nommée avec une condition de refus.**

| Passage | Porte | Refus |
| --- | --- | --- |
| Lane A → pont | revue humaine ; falsifiabilité | propriété non testable |
| Pont → Lane B | invariant admis et versionné | invariant candidat ou testé |
| Lane B → Lane C | état atteint avant tout livrable | état non atteint, pas de livrable |
| Toute lane → Inconnu | non-infération ; fail-closed | passage à « confirmé » sans réconciliation |

Le modèle doit être testé sur des objets qui n'ont pas servi à le construire.

## 5. Points ouverts et vérifications

- Nommer l'autorité d'admission (E3).
- Fixer les propriétaires par déploiement (E1, E2).
- Relire le carousel, le guichet, le configurateur v2 et `badge.py` : leur contenu n'a pas été vu pour ce brouillon.
- Vérifier les numéros de version (Discovery, revue) et les références externes (AARM, IETF, Certisyn) avant toute publication.
- Ajouter une colonne « propriétaire » à la table des lanes et découper « Méta » en objets distincts.

## 6. Suite

Tranche 1 : schéma JSON d'états pour la règle de latence à 200 ms (Lane A → pont), qui consomme ce registre.