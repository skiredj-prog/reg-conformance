# PREPARE/PREVENT — protocole de preuve d'exhaustivité (candidate, non ratifié)

## Objectif et limites

REG-ARCH-027 exige un manifeste fermé, mais un manifeste auto-déclaré ne prouve pas sa propre exhaustivité. Une revendication SUPPORTED doit porter sur un périmètre et une fenêtre temporelle explicites, avec une source d'inventaire indépendante du graphe PREPARE/PREVENT. Sans cette source : CONDITIONAL, jamais DEMONSTRATED.

## Contrat de preuve par périmètre

1. **Périmètre figé** : identifier tenant/realm, environnement, release, déploiements, writers, adaptateurs, points d'entrée, registres, fournisseurs, versions de règles/profils, secrets/capabilities et fenêtre d'observation.
2. **Deux inventaires indépendants** : (a) graphe des dépendances déclaré; (b) découverte depuis les surfaces réellement déployées (manifestes d'orchestration, tables de routage, introspection de plugins, registres d'API, configurations runtime et journaux d'admission). Consigner méthode, droits, horodatage, limites de visibilité et empreintes des deux inventaires.
3. **Réconciliation fermée** : comparer les ensembles d'identifiants canoniques et les versions, puis les arcs de dépendance. Un nœud ou arc découvert mais non déclaré, un writer inaccessible ou une version indéterminée => GAP/HOLD. Les objets déclarés mais non observés doivent être justifiés, jamais silencieusement supprimés.
4. **Changement concurrent** : chaque admission/consommation lit un epoch et digest du manifeste courant au point de linéarisation de son effet interne. Une modification concurrente rend STALE toute preuve de l'ancienne version, y compris verdicts déjà calculés mais non consommés.
5. **Requalification** : reconstituer les preuves pour les nœuds affectés et tous les dépendants transitifs; conserver les anciens reçus immuables avec leur statut historique, sans les réutiliser comme preuve courante.
6. **Preuves d'exécution** : enregistrer commit source, version des outils de découverte, inventaires hashés, écarts, scénario de mutation injectée, journal PREVENT, epochs avant/après, preuves rejetées et requalifiées, verdict et identité du vérificateur.

## Oracles adversariaux minimaux

- Writer clandestin découvert dans le runtime mais absent du graphe : HOLD.
- Changement de profil entre PREPARE et consommation : ancienne preuve STALE, aucun verdict autorisé.
- Changement de règle avec impact transitif à deux niveaux : tous les descendants affectés invalidés.
- Redémarrage après persistance PREVENT mais avant ACK : replay idempotent, aucune preuve ancienne réhabilitée.
- Source de découverte inaccessible ou observation partielle : CONDITIONAL/HOLD, jamais SUPPORTED.
- Même epoch mais digest de manifeste différent : refus.
- Configuration modifiée hors système de gestion déclaré : détection par inventaire indépendant ou garantie explicitement non démontrée.

## Frontière de preuve

Ces critères sont une **méthode candidate** et non une preuve que les déploiements REG, REG+ ou TENIR-Gov les satisfont. Les oracles de modèle restent distincts des tests d'intégration et de l'observation d'effets externes.
