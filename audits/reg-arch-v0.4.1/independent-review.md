# Relectures indépendantes — REG-ARCH v0.4.1 candidate

## Passe indépendante 1 — rejetée, défauts intégrés

Périmètre examiné : première génération de la candidate, script de construction, matrice, fixtures et oracles. Aucune implémentation REG/TENIR n’a été utilisée comme source normative.

| Point | Verdict de la première passe | Constat |
|---|---|---|
| P0.1, 010bis/G-Écart | CONTRADICTED | Note de transition informelle non remplacée à cause d’une ponctuation dans le motif de construction ; renvoi §15 ambigu et sections dupliquées ; autorité « reconnue » non définie ; reprise après commit/ACK perdu absente ; trace conditionnelle. |
| P0.2, statut/raffinement | GAP | Appendice informatif mais contenu affirmant encore une équivalence exacte ; relation de raffinement sans critère de simulation/couverture ; A-16 ne testait que l’absence de mapping. |
| P0.3, PREPARE/PREVENT | GAP | Fermeture du graphe, complétude des entrées et course PREPARE/PREVENT insuffisamment définies ; tests limités à un graphe choisi par le test. |
| D-02 | INCOHÉRENT | Tableau demandait encore de définir G-Écart alors que le nouveau texte la déclarait définie. |
| Traçabilité de génération | FRAGILE | Builder dépendait du DOCX original à l’extérieur du dossier candidat. |

Corrections apportées après cette revue : note informelle remplacée ; G-Écart renumérotée au §17 et décisions ouvertes déplacées au §18 ; D-02 limitée explicitement aux automates LC complets ; contrôleur système réservé, manifeste normatif actif, trace obligatoire, clé déterministe et reprise postcommit idempotente définis ; appendice réécrit comme illustration sans équivalence absolue ; critère de simulation/abstraction et couverture ajouté ; manifeste fermé comparé à l’inventaire effectif ; epochs et validation avant publication/consommation ajoutés ; scénarios A-17 à A-19 et oracles renforcés ; copies hashées des sources incorporées pour rendre la construction reproductible.

**Cette première passe ne constitue pas l’approbation de la version corrigée. Une seconde relecture indépendante est nécessaire.**

## Passe indépendante 2 — conclusions sur la génération intermédiaire

| Point | Verdict | Constat indépendant |
|---|---|---|
| P0.1 | CONDITIONAL | Corps cohérent, transition informelle supprimée, D-02 réconciliée. Restait une discordance entre les champs YAML et les champs réellement vérifiés; l’identité du contrôleur devait aussi avoir un critère probatoire. |
| P0.2 | CONDITIONAL | Pas d’équivalence globale normative; restaient des labels assertifs dans le diagramme informatif et un besoin de préserver l’indépendance des implémentations. |
| P0.3 | GAP | L’epoch était vérifié à la publication mais pas atomiquement au point de consommation; A-19 ne testait pas l’usage concurrent. A-20 ne vérifiait pas le lien versionné complet de la preuve nouvelle. Reprise PREVENT postcommit/ACK perdu absente du YAML. |
| Présentation/reproductibilité | RÉSERVES | Le redémarrage de PREVENT et l’appendice nécessitaient des références stables; builder devait vérifier les copies sources par hash. |

## Corrections après passe 2 — en attente de passe 3

- P0.1 : schéma obligatoire défini par `trace-schema.json`, réutilisé comme liste canonique dans A-11 et vérifié par le test Python; trace enrichie du principal, de l’assertion de capacité et de la liaison de confiance; échec fermé si l’identité/capacité ne se valide pas.
- P0.2 : labels du diagramme et descriptions de REG/REG+/TENIR neutralisés comme illustrations; rubriques d’appendice nommées A.1–A.4; description de l’allocation et du registre réécrite comme facultative.
- P0.3 : époque incrémentée avant activation de configuration; preuves d’époque ancienne rejetées immédiatement; jeton de consommation vérifié au même point de linéarisation que l’usage; opération PREVENT idempotente après ACK perdu; A-21/A-22 testent consommation et reprise; A-20 vérifie epoch et digest de manifeste de la preuve nouvelle.
- Reproductibilité : builder vérifie les SHA-256 des copies PDF et DOCX locales avant de générer.

Ces corrections ne sont pas validées par la passe 2. Elles sont soumises à une troisième revue indépendante.

## Passe indépendante 3 — conclusions sur la génération intermédiaire

| Point | Verdict | Constat |
|---|---|---|
| P0.1 | CONDITIONAL | Le JSON et A-11 ont les mêmes 27 champs ; G-Écart est décrite, mais collision de clé avec contenu divergent non testée et identité réelle toujours conditionnée à une preuve de confiance. |
| P0.2 | GAP | Appendice encore trop produit-spécifique (descriptions assertives de REG/REG+/TENIR, registre exemple avec ciblage produit et prochaines étapes prescriptives), malgré disclaimer informatif. |
| P0.3 | CONDITIONAL | Epoch/linéarisation sont présents ; A-20 ne détaillait pas le digest dans le YAML et aucun test isolé du mauvais digest à epoch identique n’était présent. |

Corrections postérieures à la passe 3 : collision de clé avec contenu divergeant refusée et testée; appendice produit-specific supprimé en entier et remplacé par trois paragraphes génériques facultatifs; A-20 relie le digest courant; A-23 teste un mauvais digest à epoch identique; le validateur fixe désormais l’appendice générique plutôt que les anciens labels.

**Une quatrième revue indépendante est requise.** Les verdicts de la passe 3 ne sont pas automatiquement applicables à la nouvelle génération.

## Passe indépendante 4 — génération corrigée

| Point | Verdict | Constat indépendant |
|---|---|---|
| P0.1 | CONTRADICTED | Le texte demande une trace REFUSED avec champs inconnus nuls, mais le schéma impose des chaînes pour certains champs; le modèle renvoie REFUSED sans événement. |
| P0.2 | SUPPORTED au niveau normatif | Appendice générique informatif; contrat de raffinement borné sans équivalence globale. Les preuves concrètes restent propres au périmètre. |
| P0.3 | SUPPORTED au niveau normatif, CONDITIONAL pour déploiement | Fermeture, impact, epochs, STALE et requalification sont définis; preuve réelle d’exhaustivité et de bon fonctionnement non fournie. |

Correction post-passe 4 : les champs de contexte connus comme potentiellement inconnus sont nuls dans le schéma; événements REFUSED sont journalisés par le modèle; tests de refus et absence du journal ajoutés; A-24/A-25 ajoutés. Cette passe ne valide pas ces changements.

## Passe indépendante 5 — génération après premier correctif P0.1

| Point | Verdict | Constat indépendant |
|---|---|---|
| P0.1 | CONTRADICTED | Des champs source/cible et `refusal_category` demeurent non nullables; un conflit d’idempotence divergeant renvoie sans événement de tentative. A-24/A-25 sont YAML seulement et ne sont pas exécutés par des tests. |
| P0.2 | SUPPORTED au niveau du contrat | Raffinement explicite, borné par garantie, hypothèses et traces. Aucun raffinement concret n’est démontré. |
| P0.3 | CONDITIONAL | Spécification d’impact satisfaisante au niveau normatif; exhaustivité de l’inventaire et validité empirique des hypothèses restent sous-déterminées. |
| Reproductibilité | RÉSERVE | Vérificateur local ne couvre pas l’ensemble de JSON Schema; empreintes/compte des tests du rapport étaient dépassés. |

Corrections post-passe 5 : nullabilité étendue aux champs source/cible et motif avec contrainte de non-nullité conditionnelle pour CREATED/REUSED; conflit de clé journalisé en REFUSED; tests exécutés A-24/A-25 et validation du refus de collision. Génération courante : 19 tests, A-11 à A-25, empreintes DOCX `6B8A8E10C6FB9BD7B06D839881BB3B1CD49CEB3345F61DFA7D5931A2FB879562`, PDF `B001E7D9B09B89D695260AC6E2635D8E8A802929E4767AA12437B7BE36F5AE39`. Un validateur JSON Schema standard est absent de l’environnement; signalé comme réserve reproductible.

**La passe indépendante 6 examine le correctif courant.** Aucun résultat n’est anticipé; cette génération ne doit pas être considérée clôturée tant que cet examen n’est pas enregistré.

## Passe indépendante 6 — après nullabilité / collision journalisée

| Point | Verdict | Constat indépendant |
|---|---|---|
| P0.1 | CONTRADICTED | La collision générait sa trace en copiant la trace d’origine et remplaçait seulement une partie des champs. L’événement ne décrivait pas nécessairement la demande rejetée, notamment si version/manifeste changeaient. |
| P0.2 | SUPPORTED au niveau normatif; UNVERIFIABLE pour un raffinement concret sans preuve | Contrat borné adéquat. |
| P0.3 | CONDITIONAL | Méthode de preuve d’exhaustivité de l’inventaire/hypothèses terrain non spécifiée suffisamment. |

## Passe indépendante 7 — première correction de fidélité de collision

| Point | Verdict | Constat indépendant |
|---|---|---|
| P0.1 | CONTRADICTED | Le modèle copiait encore le trace original puis surchargeait une partie; l’empreinte canonique et tous les champs courants n’étaient pas vérifiés. |
| P0.2 | SUPPORTED au niveau normatif; UNVERIFIABLE pour un raffinement concret sans preuve | Pas d’équivalence globale. |
| P0.3 | CONDITIONAL | La preuve de complétude d’inventaire et des hypothèses demeure une exigence à établir par périmètre. |

Correction post-passe 7 : trace collision construite sans copie de l’événement d’origine, empreinte JSON canonique (champs triés), `requested_reason` capturé, test d’empreinte recalculé indépendamment et scénario de collision avec changement de version/manifeste ajouté à l’oracle. Génération courante : DOCX `DEB30C7DC29B78960AA7166DFE2C42CDE179579C0BBAF673FB34928F6ABB1C95`, PDF `0B0A1E3903FF5607359090E034FCC96B3535A536E631C56FEC8C185CE024BFD4`, 19 tests, 15 scénarios.

**Passe indépendante 8 en cours; aucun verdict n’est anticipé.**

## Passe indépendante 8 — fidélité de collision et première formalisation de l’empreinte

| Point | Verdict | Constat indépendant |
|---|---|---|
| P0.1 | CONTRADICTED | Trace construite à partir du contexte courant et test de drift partiel présents, mais REG-ARCH-025 ne définissait ni le préimage exact de `request_fingerprint` ni sa sérialisation canonique. A-11 n’explicitait pas le drift version/manifeste. |
| P0.2 | SUPPORTED au niveau normatif; UNVERIFIABLE pour un raffinement concret sans preuves | Contrat borné et appendice informatif. |
| P0.3 | CONDITIONAL | Exhaustivité réelle du manifeste et validation des hypothèses requièrent preuves du périmètre. |

Correction post-passe 8 : REG-ARCH-025 prescrit SHA-256 sur UTF-8 de JCS conforme à RFC 8785, sur un objet JSON à exactement 17 propriétés nommées, avec null pour l’inconnu et sans propriétés supplémentaires. A-26 formalise le drift de version/manifeste; test dédié vérifie les valeurs courantes. Génération courante : 20 tests, 16 scénarios, DOCX `2C86C2CF275CF2C4028C0F2437DE332D3BC1C5B99C4967EB68C8AEF0DB1532C4`, PDF `6BE9328006812EF6ED98E7D07AE89FCF68ED08FF8A1C4E5694C4E08AAD0F62BC`.

**Passe indépendante 9 en cours; aucun verdict n’est anticipé.**

## Passe indépendante 9 — candidate v0.4.1 corrigée

| Point | Verdict | Constat indépendant |
|---|---|---|
| P0.1 | SUPPORTED pour la cohérence normative et le cas collision A-26 du modèle; CONDITIONAL pour tout déploiement | 17 propriétés du préimage explicitement listées; JCS/RFC 8785 sur UTF-8 et SHA-256; version/manifeste courants, motif, identifiant d’événement antérieur et digest recalculé vérifiés pour A-26. Revue indépendante a recalculé le hash d’exemple et obtenu la même valeur. |
| P0.2 | SUPPORTED pour le contrat normatif; UNVERIFIABLE pour tout raffinement concret sans preuves propres au périmètre | Appendice informatif, raffinement limité aux garanties revendiquées, pas d’équivalence globale présumée. |
| P0.3 | CONDITIONAL | Obligations de propagation/epochs/STALE/consommation/requalification et oracles présents; exhaustivité des inventaires réels et validation empirique des hypothèses restent à démontrer pour chaque périmètre. |
| Validation du schéma | RÉSERVE | Aucun validateur JSON Schema standard n’est disponible dans l’environnement; le validateur local est partiel. Le modèle emploie `json.dumps(sort_keys=True)` et ses fixtures ASCII concordent avec JCS, sans démontrer la conformité générale RFC 8785 pour toutes chaînes JSON. |

Vérification locale : 20 tests réussissent; A-26 inclus; 16 scénarios; neuf décisions ouvertes; PDF 13 pages; empreintes candidate contrôlées dans le rapport. La revue 9 est indépendante de l’éditeur, mais n’est pas une preuve d’implémentation.
