# Module Crosswalk : Correspondance Terminologique et Conformité (REG)

Ce module fournit une matrice de correspondance interactive et ouverte entre les concepts d'exécution du protocole **REG (Runtime Execution Governance)** et les terminologies ou cadres réglementaires/normatifs existants (NIST AI RMF, ISO/IEC 42001, EU AI Act, IAM, etc.).

---

## 🎯 Objectif et Philosophie

* **Rapprochement sémantique, non équivalence juridique** : La matrice identifie des points de contact ou de superposition conceptuelle. Elle n'affirme pas d'équivalence stricte ni de conformité automatique.
* **Transparence et indépendance** : Les termes et statuts présentés constituent des propositions soumises à la révision indépendante des auteurs des cadres cités et de la communauté.
* **Neutralité** : La mention *"Non trouvé dans les sources consultées"* indique simplement qu'un équivalent direct n'a pas été identifié lors de l'étude bibliographique initiale, et non une absence définitive dans le cadre visé.

---

## 📐 Taxonomie et Vocabulaire

### Types de Relations (`relation`)

* **`partial` (Rapprochement partiel)** : Le cadre externe couvre un besoin similaire, mais avec des mécanismes, un périmètre ou des garanties distincts.
* **`shared_word_different_object` (Mot commun, objet différent)** : Même terme utilisé dans la littérature/norme, mais désignant un objet ou un artefact technique différent.
* **`not_found_in_sources` (Non trouvé dans les sources consultées)** : Aucun terme équivalent direct identifié dans la littérature examinée à ce jour.

### Statuts de Vérification (`verification_status`)

* **`unverified` (Non vérifié)** : Proposition initiale dérivée de l'analyse bibliographique préliminaire.
* **`partially_checked` (Partiellement vérifié)** : Revue par au moins un tiers ou alignée sur un texte réglementaire/normatif spécifique.
* **`verified` (Vérifié)** : Confirmé formellement par les auteurs/experts du cadre concerné.
* **`specified-in-rfc4` (Spécifié dans RFC-4)** : Le vecteur est décrit dans la RFC, mais aucun test exécutable du dépôt de laboratoire ne le couvre encore. Ce n'est **pas** une vérification.
* **`tested` (Testé)** : Un test exécutable du dépôt de laboratoire couvre le vecteur. L'entrée porte alors un champ `evidence` avec le fichier de test, le SHA exécuté et le numéro du run CI.

* **`planned` (Planifié)** : Vecteur inscrit au catalogue `vectors/dist/vectors.json`, sans test exécutable à ce jour. Il n'apparaît pas dans le texte des RFC publiées.
* **`frozen` (Frozen)** : The source document is frozen (RFC-4, frozen version) and its vectors are covered by other rows. This status is neither a verification nor the absence of one: it only signals that a direct correspondence remains to be established.

Le statut `verified-by-vector` n'est plus utilisé : il affirmait une vérification sans preuve.

---

## 🤝 Comment contribuer ?

Les contributions sont vivement encouragées pour enrichir, corriger ou valider la matrice :

1. **Soumettre une correction ou un nouveau terme** :
   * Modifiez directement le fichier JSON : [`data/crosswalk.json`](data/crosswalk.json).
   * Proposez une *Pull Request* décrivant la modification et fournissant la référence textuelle associée.
2. **Ouvrir une discussion** :
   * Ouvrez une issue sur le dépôt avec le tag `crosswalk` pour proposer une relecture : [Créer une Issue](https://github.com/skiredj-prog/reg-conformance/issues/new).

---

## 📁 Structure du répertoire

* `index.html` : Interface web interactive (filtres, recherche, compteurs, export CSV).
* `data/crosswalk.json` : Source de données structurée pour la correspondance terminologique.
* `data/vectors.json` : Copie de secours du catalogue de vecteurs de conformité.
* `data/related-work.md` : Synthèse des travaux de recherche et normes associés.
* `data/rfc-mapping.md` : Brouillon de mapping destiné aux spécifications RFC.
