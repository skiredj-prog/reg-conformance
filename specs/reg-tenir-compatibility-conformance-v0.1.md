# REG–TENIR Compatibility Conformance — profil v0.1 (candidate)

**Statut : PROPOSED / NOT RATIFIED / NO IMPLEMENTATION CERTIFICATION**  
**Référence : REG-ARCH-026 (candidate v0.4.1) — raffinement typé et preuves par transition**  
**Date : 26 octobre 2026**  
**Portée : compatibilité architecturale et sémantique ; AUCUNE obligation de déployer REG et TENIR ensemble.**

## 1. Distinctions obligatoires

- **Conformance propre à REG** : une implémentation REG satisfait son contrat REG, avec ses hypothèses et preuves propres.
- **Conformance propre à TENIR** : une implémentation TENIR satisfait son contrat TENIR, avec ses hypothèses et preuves propres.
- **REG–TENIR Compatibility Conformance** : une **relation vérifiée** entre deux profils contractuels, sous des hypothèses nommées, préservant les propriétés communes déclarées. Les composants peuvent rester autonomes et utiliser des protocoles différents.
- **Interopérabilité protocolaire** : échange effectif de messages/artefacts avec sérialisation, authentification, versionnement, gestion des erreurs et traduction d'état.
- **Conformance end-to-end** : préservation d'une propriété sur un chemin d'exécution combiné et ses effets. Elle n'est exigée **que si une revendication ou un cas d'usage en dépend**.

Deux systèmes valides indépendamment ne sont pas automatiquement compatibles. La compatibilité est une **relation**, pas une conséquence logique de deux verdicts PASS.

## 2. Niveaux, preuves et étiquettes

| Niveau | Nom | Condition minimale | Revendication autorisée |
| --- | --- | --- | --- |
| **K0** | `INDEPENDENT_VALIDITY` | Chacun a un contrat, une version, des tests et limites explicites | « deux résultats indépendants » ; **aucune** compatibilité inférée |
| **K1** | `SEMANTIC_MAPPING` | Vocabulaire, types, pré/postconditions et hypothèses explicitement appariés, contradictions cherchées | « mapping spécifié » ; pas encore démontré |
| **K2** | `PROPERTY_REFINEMENT` | Pour chaque propriété revendiquée : relation de simulation/raffinement et tests positifs, négatifs, incertitude, rejeu et transition concurrente ; contre-exemples recherchés | « compatible pour le sous-ensemble P, sous H » ; non global |
| **K3** | `PROTOCOL_INTEROPERABILITY` | Adaptateur/version de wire, vecteurs de sérialisation, signatures, cas d'erreur, négociation et round-trip ; preuve d'intégration | « interopérable sur l'interface I » |
| **K4** | `COMPOSED_END_TO_END` | Exécution combinée, identité/autorité, linéarisation, effets et reprise démontrés | « garantie end-to-end sur le périmètre D » |

**K2 n'exige ni K3 ni K4.** K3 ne prouve pas K4. Un test de K4 peut être nécessaire pour une revendication particulière, mais **n'est pas un prérequis universel** à la compatibilité REG–TENIR.

Les niveaux ne sont pas une échelle de maturité d'un produit entier : une relation peut être K2 sur les verdicts, K1 sur la quarantaine et K0 sur les effets externes.

## 3. Relation de compatibilité

Pour deux systèmes de transitions `R` (REG) et `T` (TENIR), un profil de compatibilité nomme :

- les versions, périmètres, profils d'exécution, frontières de confiance et hypothèses `H` ;
- une abstraction typée `α_R` et `α_T` vers des **observations communes** (admission, refus, incertitude, commit, quarantaine, effet revendiqué, preuves) ;
- une relation `C ⊆ States_R × States_T` et des obligations `O` ;
- des propriétés partagées `P` (ex. « aucune admission sur quarantaine active », « UNKNOWN n'autorise pas le rejeu »).

Une relation candidate est recevable seulement si les traces permises et interdites sont confrontées : pour tout scénario testé `s` sous `H`, une transition interdite par `P` ne peut devenir admissible après abstraction dans l'un ou l'autre système. Des transitions internes peuvent être **stuttering** si elles n'affectent aucune observation pertinente, à condition de documenter la règle. Une correspondance nominale de statuts ne suffit pas.

Une preuve par tests finis soutient seulement les cas testés ; une preuve générale exige des arguments de couverture, un modèle et/ou une vérification appropriés. Ceci reprend la frontière **REG-ARCH-026** ; la candidate v0.4.1 n'est pas ratifiée.

## 4. Axes de compatibilité et pièges de traduction

| Axe | Obligation | Contre-exemple à interdire |
| --- | --- | --- |
| Admission / refus | Distinguer `PASS`, `FLAG`, `HARD_VETO`, `HOLD` et les états TENIR selon leurs **effets**, pas leurs noms | Traduire `HOLD` en `PASS` ou `REJECTED` final |
| Incertitude | Préserver `UNKNOWN`, `STALE`, `LOW_CONFIDENCE`, `OUTCOME_UNKNOWN` et les exigences de réconciliation selon le profil | Timeout ou ACK perdu interprété comme « refus certain » ou « effet non produit » |
| Autorité et scope | Préserver realm/store, identité, standing, grant, epoch et révocation lorsqu'applicables | Étendre un droit ou recycler un grant entre realms |
| Continuité | Préserver monotonie, digests d'état, quarantaine et tête attestée sous les hypothèses E8/CB-05 déclarées | Restaurer une quarantaine inactive valide mais ancienne et admettre |
| Commit / idempotence | Préserver ONCE/at-most-once, état local durable et distinction avec effet fournisseur | Rejouer un effet après perte d'ACK |
| Preuve et traçabilité | Associer chaque claim à SUT SHA, profil, versions, oracle, résultat et limites | Transformer un PASS de modèle en conformité de déploiement |
| Réversibilité / frontière d'effet | Identifier le moment où une action devient irréversible et les mécanismes de HOLD | Confondre réservation simulée et exécution réelle |

**Important :** les deux protocoles de laboratoire `reg-e8-advance-lab-v0.1` et `e8-lab-preauth-v0.1` peuvent avoir des contrats locaux cohérents tout en restant **non interopérables au niveau wire**. Cela n'invalide pas une relation K1/K2 sur leurs propriétés communes, et ne permet pas d'affirmer K3.

## 5. Matrice d'acceptation minimale K1 → K2

Pour chaque propriété `P_i`, produire une ligne vérifiable :

`property_id, REG_ref+SHA, TENIR_ref+SHA, H, alpha_R, alpha_T, oracle_positive, oracle_negative, oracle_unknown, counterexample, evidence, coverage_limit, reviewer, verdict`.

Statuts : `PROPOSED`, `SUPPORTED_FOR_SCOPE`, `CONDITIONAL`, `CONTRADICTED`, `UNVERIFIABLE`, `WITHDRAWN`.

Un `SUPPORTED_FOR_SCOPE` exige des preuves et une revue ; une simple présence de deux PASS séparés donne `PROPOSED` ou `CONDITIONAL`, **jamais** `SUPPORTED_FOR_SCOPE` par déduction automatique. La découverte d'une contradiction ramène la ligne à `CONTRADICTED`, sans supprimer l'historique.

**Vecteurs initiaux (proposés, non exécutés) :**

- `RT-C01` : refus vs HOLD vs HARD_VETO, aucun downgrade vers admission.
- `RT-C02` : ACK perdu / `OUTCOME_UNKNOWN` → aucune exécution ou réémission automatique.
- `RT-C03` : même idempotency key + payload différent → conflit explicite.
- `RT-C04` : révocation de scope / epoch → non-amplification.
- `RT-C05` : restauration d'un ancien marqueur de quarantaine → aucun PASS sous hypothèse de tête indépendante.
- `RT-C06` : effet externe absent de la preuve → reçu local non converti en effet confirmé.
- `RT-C07` : preuve d'ancienne version/manifest → STALE et requalification.

Les vecteurs `RT-C05`/E8 sont **conditionnels** à l'existence d'une vraie frontière indépendante. Les contre-exemples G4-A Q1/Q6 documentés dans TENIR PR #80 empêchent toute déclaration de conformité système sur ce point.

## 6. Décision de portefeuille et garde-fous

1. Maintenir les tests REG et TENIR **indépendants**, avec leurs verdicts locaux.
2. Ouvrir un **profil REG–TENIR Compatibility** K1, puis qualifier les propriétés une par une vers K2.
3. Ne construire un adaptateur K3 que pour un besoin d'intégration explicite.
4. N'exiger K4 que pour une garantie ou un produit revendiquant le chemin REG → TENIR → effet.
5. Garder les P0 R-01, Q1/Q6, C1/C2 et `PRODUCTION HOLD` **dans le périmètre système où ils s'appliquent**, sans en faire des prérequis fictifs à toute relation architecturale.

**Verdict courant : K1 PROPOSED ; K2 NON DÉMONTRÉ ; K3 NON REQUIS ; K4 NON REQUIS.**

Aucune fusion, ratification, certification ni promotion de REG-ARCH n'est implicite.
