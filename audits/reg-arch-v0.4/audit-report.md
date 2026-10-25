# Audit contradictoire de REG-ARCH v0.4

Date : 2026-10-25
Sujet principal : `REG-ARCH_v0_4 (1).pdf` fourni par l’utilisateur, corroboré par le DOCX
Périmètre : cohérence, complétude et vérifiabilité de REG-ARCH comme référentiel architectural. Les implémentations TENIR, REG Engine, REG+ et les tests de conformité sont des sujets de preuve potentiels, jamais des sources normatives.

## Verdict exécutif

REG-ARCH v0.4 est une proposition architecturale nettement plus complète que la transcription v0.1 précédemment disponible. Elle contient bien les 25 obligations annoncées, y compris REG-ARCH-010bis, les 14 portes G-01 à G-14, les 9 cycles LC-01 à LC-09, l’enveloppe d’événement 012, les relations de causalité 013 et les tests T-01 à T-13.

Elle ne soutient toutefois pas encore toutes les garanties qu’elle décrit. Le résultat global est **CONDITIONAL**, avec trois ruptures P0 :

1. REG-ARCH-010bis impose la création d’un Écart par une transition qui devrait elle-même être gouvernée par une porte, mais le document reconnaît que cette porte n’est pas définie et autorise provisoirement une transition informelle ;
2. l’appendice décrit une chaîne normative et technique complète, une équivalence de raffinement et six paquets de preuves, sans préciser clairement si ces prescriptions sont normatives, informatives ou hors périmètre ;
3. PREPARE/PREVENT, la propagation des changements de configuration et l’invalidation transitive des preuves ne sont pas définis comme obligations exécutables, alors que l’appendice les présente comme la chaîne nécessaire pour prouver l’équivalence.

Les garanties de traçabilité bornée et de non-confusion entre intégrité, vérité et effet externe sont **SUPPORTED sous conditions**. Les garanties de non-promotion, de HOLD et de non-rejeu sont **CONDITIONAL**. Les garanties d’équivalence REG-ARCH → REG → REG+ → TENIR-Gov et d’invalidation automatique des preuves sont **GAP**. « Exactement un effet externe » est explicitement hors garantie et doit rester **UNVERIFIABLE** au niveau de REG-ARCH seul.

## 1. Source, version et statut

| Élément | Résultat |
|---|---|
| Fichier principal | `C:\Users\hp\Downloads\REG-ARCH_v0_4 (1).pdf` |
| Source corroborante | `C:\Users\hp\Downloads\REG-ARCH_v0_4.docx` |
| Version dans le document | 0.4, autonome, se substitue à v0.1, v0.2 et v0.3 |
| Date dans le document | 25 octobre 2026 |
| SHA-256 PDF | `4BE9D68CA8DCE3557655905467C0975758E82AB2888F974B0B9439D59620B939` |
| SHA-256 DOCX | `46752A0E1CD7AAE430742878C14C6B5C28FE1DA8167C9A81D78B23D9BAA7D3C2` |
| Autorité d’approbation | À désigner |
| Obligations | 001–024 + 010bis, soit 25 |
| PDF canonique | Non fourni et non vérifié |
| Rendu visuel PDF | 11 pages A4 rendues et contrôlées ; aucune anomalie de clipping ou chevauchement observée |

Le PDF se déclare autonome, mais son champ `Source` indique « REG-ARCH v0.1 à v0.3 + corrections ciblées ». La lignée est décrite dans la préface et le journal des changements, mais aucun identifiant de révision source, hash des versions antérieures, décision d’approbation ou registre de supersession n’est incorporé. L’autonomie textuelle est donc établie ; l’autorité normative reste conditionnelle.

## 2. Examen clause par clause

| Clause | Exigence v0.4 examinée | Analyse contradictoire | Statut |
|---|---|---|---|
| 001 | Distinguer proposé, spécifié, implémenté, vérifié | Distinction claire et non auto-certifiante. Ne définit pas de schéma de statut ni de contrôle de transition entre statuts. | SUPPORTED sous conditions |
| 002 | Séparer lanes, cycles, portes et événements | Taxonomie claire ; le test de non-confusion et la représentation canonique ne sont pas définis. | CONDITIONAL |
| 003 | Identifiant stable, type, version, responsable | Base suffisante ; unicité, portée globale, résolution de version et révocation manquent. | CONDITIONAL |
| 004 | Acteur, rôle, mandat, périmètre et validité | Exigence forte ; modèle d’identité, révocation, horloge et vérification du mandat renvoyés à D-01/D-08. | GAP P0 |
| 005 | États, transitions, préconditions, effets et refus par cycle | Les machines LC-01 à LC-09 sont listées, mais les états et transitions canoniques ne sont pas entièrement formalisés dans un schéma machine lisible. | GAP P1 |
| 006 | Absence de promotion implicite | Le texte et le tableau des distinctions couvrent les confusions principales ; les transitions interdites et le mécanisme de blocage restent à définir. | CONDITIONAL |
| 007 | Toute porte définit identité, entrées, demande, conditions, autorité, refus, effets, traces, frontière | Le tableau de contenu obligatoire est utile ; atomicité, décision concurrente, fail-closed, version de porte et invalidation ne sont pas entièrement contraints. | GAP P1 |
| 008 | Runtime lié à la version d’invariant et au snapshot des règles | Bonne liaison locale ; absence de règle normative imposant le lien inverse et la propagation aux profils/configurations/preuves. | GAP P0 |
| 009 | Capture, rattachement et qualification distincts | Distinction explicite et test T-05 cohérent ; critères d’indépendance et de qualification restent partiellement déclaratifs. | SUPPORTED sous conditions |
| 010 | Refus sans mutation de l’objet cible | Règle claire, incluant clôture distincte et causalité ; atomicité multi-objets seulement ajoutée comme incident en 018. | CONDITIONAL |
| 010bis | Refus structurel crée un Écart LC-08 via transition causale | Le périmètre structurel et les exclusions sont clairs. Contradiction explicite : la porte G-Écart n’est pas définie et la transition informelle est temporairement permise. | CONTRADICTED / GAP P0 |
| 011 | REQUESTED, DECIDED, APPLIED distincts | Sémantique claire ; absence de contrat d’ordre global, de transitions interdites et d’obligation d’invalidation des décisions non appliquées. | CONDITIONAL |
| 012 | Enveloppe d’événement avec champs applicables | Champs détaillés, versions de mandat et digest de politique ajoutés ; « applicables » autorise encore une omission ambiguë par type d’événement. | CONDITIONAL |
| 013 | `prev_object_event_id` distinct de `causation_event_ids` | Relations bien distinguées ; aucun contrôle normatif des cycles, de la complétude ou de la résolution interobjets. | GAP P1 |
| 014 | Objet/version, méthode/version, éléments, résultat, portée, vérificateur | Critères minimaux bien posés ; pas de niveau de preuve exigé par garantie ni de verdict invalidable automatiquement. | CONDITIONAL |
| 015 | Application seulement sur versions et préconditions valides | Revalidation et non-application exigées ; point de course, atomicité et propagation à la preuve ne sont pas spécifiés. | GAP P0 |
| 016 | Journal append-only logique et corrections additives | Bonne règle ; complétude, disponibilité, rétention, ancrage et audit de suppression physique restent hors contrat. | CONDITIONAL |
| 017 | Hash/signature/ancre ne prouvent ni vérité, ni légitimité, ni propriété, ni effet fournisseur | Limite normative précise et essentielle ; modèle de confiance et vérification des clés renvoyés à D-08. | SUPPORTED borné |
| 018 | Blocage si trace durable impossible ; incident si effet possible | Ajout utile sur persistance partielle et application partielle ; la frontière entre blocage préalable et effet déjà engagé reste opérationnelle. | CONDITIONAL |
| 019 | Absence de contradiction/réponse/preuve négative ne confirme pas | Règle claire ; aucune mesure de complétude d’observation ou de preuve positive minimale. | CONDITIONAL |
| 020 | HOLD et interdiction du rejeu jusqu’à réconciliation G-07 | Protection contre le rejeu bien formulée ; « a pu avoir lieu » et les obligations de détection d’effet sont non vérifiables. | CONDITIONAL |
| 021 | ONCE précise domaine, clé, durée, concurrence | Bonne distinction entre ingestion, clé d’exécution et fournisseur ; aucun contrat de crash point ou de propagation de clé externe. | GAP P0 |
| 022 | Registre d’extériorité par interface | Responsabilités, attentes et exclusions sont structurées ; le document dit lui-même que les entrées sont un modèle initial non vérifié. | CONDITIONAL |
| 023 | Livrable porte version, statut, portée, exclusions, traçabilité et supersession | Exigence robuste ; révocation côté consommateur, cache, circulation et obligation de rejet d’un artefact supersédé non spécifiées. | CONDITIONAL |
| 024 | Artefact régénérable lié aux sources, générateur et paramètres | Bonne base ; environnement, dépendances, hash du générateur et effet d’un changement de source ne sont pas obligatoires. | GAP P1 |

## 3. Garanties revendiquées

| Garantie | Clauses/portes | Hypothèses | Preuve minimale | Lacune | Verdict |
|---|---|---|---|---|---|
| Traçabilité d’une décision gouvernée | 003, 007, 011–016, 023–024 ; G-01 à G-14 | Journal accessible, identités et versions fiables | Reconstruction indépendante de la demande à l’application/non-application | Graphe de complétude et obligations PREVENT absents | CONDITIONAL |
| Non-promotion implicite | 001, 002, 006, 007, 011 | Toutes les portes passent par le catalogue versionné | Oracle indépendant des transitions et tests négatifs | Catalogue des états/portes pas entièrement formalisé | CONDITIONAL |
| Séparation décision/application | 011, 015 | Événements persistants et concurrence contrôlée | ACCEPTED sans APPLIED, changement de version, course | Atomicité et revalidation détaillées insuffisamment | CONDITIONAL |
| Intégrité et provenance d’un enregistrement | 009, 012–018, D-08 | Chaîne, clés, ancrage et stockage disponibles | Vérification indépendante des digests/signatures | Intégrité ne valide pas automatiquement les relations sémantiques | SUPPORTED borné |
| Refus fail-closed en cas d’autorité ou critère manquant | 004, 006, 007, 010bis ; G-03 | Autorité désignée ou absence détectable | T-04 avec Écart et état cible inchangé | G-Écart non défini, donc boucle de dépendance | GAP P0 |
| HOLD en cas d’issue externe inconnue | 018–021 ; G-07 | Observation incomplète explicitement reconnue, réconciliation disponible | Perte ACK, effet tardif, retry, crash | Aucun contrat de couverture de l’observation | CONDITIONAL |
| Absence de double effet externe | 020–021 ; G-06/G-07 | Membrane avant tous les chemins d’effet, clé consommée atomiquement | Crash après dispatch et concurrence multi-process | Dépend de composants et du fournisseur, non établi par REG-ARCH | UNVERIFIABLE |
| Exactement un effet externe | 017, 021, 022 | Fournisseur dédoublonne et expose un contrat d’effet | Preuve fournisseur et réconciliation | Explicitement exclu par 017 et §9 | SUPPORTED comme non-garantie |
| Propagation d’une modification de configuration | 008, 014, 015, 024, appendice P1/P6 | Graphe complet et versions immuables | Mutation C1→C2, impact hypothèses/garanties/preuves | Aucun mécanisme PREVENT normatif | GAP P0 |
| Obsolescence des preuves | 001, 003, 008, 014–016, 024 | Comparaison exacte des versions et invalidation | Changement de SHA/règle/profil/environnement | `STALE`/révocation transitive non défini | GAP P0 |
| Sortie bornée et non trompeuse | 017, 022–024 | Consommateurs respectent le registre | Rejet si portée/frontière absente ou supersédée | Enforcement des consommateurs absent | CONDITIONAL |
| Équivalence REG-ARCH → REG → REG+ → TENIR-Gov | Appendice §§1–3, P1–P6 | Raffinement formel, oracle, schemas, PBT, evidence pack | Inclusion des traces concrètes dans les traces autorisées | Appendice prescriptif mais statut normatif ambigu ; aucun contrat de raffinement dans 001–024 | GAP P0 |

## 4. Contradictions, ambiguïtés et dépendances circulaires

| ID | Constat | Références | Niveau |
|---|---|---|---|
| C-01 | 010bis exige une transition causale pour créer un Écart, mais autorise une transition informelle jusqu’à définition de sa porte | 010bis, 007, D-02 | P0, contradiction interne explicite |
| C-02 | D-02 doit décider la porte G-Écart alors que 010bis la rend déjà obligatoire | 010bis, §14 D-02 | P0, dépendance circulaire |
| C-03 | L’appendice décrit quatre niveaux et une preuve d’équivalence, mais le périmètre normatif des 001–024 se limite au modèle architectural et à la traçabilité | Métadonnées, §15, appendice §§1–3 | P0, frontière normative ambiguë |
| C-04 | P1 exige pour chaque obligation un module, un test et une trace, alors que le §12 dit qu’aucun résultat d’exécution n’est revendiqué | appendice P1, §12 | P1, état de preuve non distingué |
| C-05 | `G-10` dépend d’une propriété ayant passé G-02, mais le modèle ne définit pas l’invalidation si la méthode ou la propriété testable change | G-02, G-10, 014, 024 | P0 |
| C-06 | 012 rend les champs « applicables » ; l’applicabilité dépend de l’événement mais aucune matrice obligatoire par type n’est normative | 012, tables 8–9 | P1 |
| C-07 | 016 garantit l’append-only logique, mais ne garantit ni la complétude ni la disponibilité permettant la reconstruction | 016–018 | P1 |
| C-08 | 021 sépare l’idempotence locale de l’effet fournisseur, mais aucun contrat ne rattache la clé locale à la transaction externe | 021–022 | P0 |
| C-09 | Le tableau d’extériorité dit que ses contrats sont proposés et non vérifiés, alors que 022 en fait une exigence de frontière | 022, §9 | P1 |
| C-10 | Le journal des changements v0.3→v0.4 ne fournit pas de décision, auteur habilité, hash de version précédente ou preuve de comparaison | §16, D-01/D-08 | P1 |

## 5. PREPARE et PREVENT

La traçabilité, la validité d’une relation et la garantie effective sont trois propriétés différentes. v0.4 traite bien la première par les identifiants, versions, digests et relations causales. Elle ne définit pas suffisamment la deuxième et la troisième.

| Transformation | PREPARE descendant | PREVENT ascendant | Verdict |
|---|---|---|---|
| Exigence → garantie | Les garanties sont listées mais ne possèdent pas de registre normatif explicite | Une configuration ne déclare pas obligatoirement les garanties affectées | Manquante |
| Garantie → obligations | La matrice obligation/garantie doit être construite par l’auditeur | Aucun impact inverse quand une obligation change | Partielle |
| Obligation → porte/règle | G-01 à G-14 donnent une première décomposition | Le changement d’une porte ne déclenche pas d’invalidation normative | Partielle |
| Porte/règle → profil | G-04 exige un snapshot de règles runtime | Le profil réellement chargé et son digest ne sont pas obligatoires dans un registre d’impact | Partielle |
| Profil → configuration | G-04 et LC-06 décrivent une évaluation située | Aucun événement obligatoire `configuration_changed` | Manquante |
| Configuration → hypothèses | D-04/D-08/D-09 exposent des dépendances | La satisfaction ou invalidation d’une hypothèse n’a pas de propagation obligatoire | Manquante |
| Configuration → preuve | 014 et 024 demandent version et sources | Une preuve devenue ancienne n’est pas automatiquement `STALE` | Manquante |
| Preuve → verdict | 009/014/017 bornent la qualification | Aucun refus générique de verdict antérieur après mutation transitive | Partielle |

### Test de référence

1. C1 utilise la règle R1, le profil P1, la configuration K1 et l’hypothèse H1 ; la preuve E1 est qualifiée.
2. C1 devient C2 par changement de topologie, timeout, SHA du code, version de règle ou environnement, tout en conservant un identifiant humain identique.
3. PREVENT doit produire l’impact `C2 → H1 → garanties → E1`, marquer E1 obsolète et suspendre les verdicts.
4. PREPARE doit refuser E1 pour C2, exiger une nouvelle qualification et distinguer la nouvelle preuve de l’ancienne.

REG-ARCH v0.4 fournit les identifiants nécessaires pour représenter ces liens, mais aucune obligation ne définit le graphe d’impact, l’événement d’obsolescence, la règle de calcul ou le refus automatique. Le test est donc **GAP P0**.

## 6. Scénarios adversariaux reproductibles

Le manifeste machine-readable associé se trouve dans `adversarial-scenarios.yaml`.

| ID | Attaque | Attendu normatif | Faiblesse testée |
|---|---|---|---|
| A-01 | Changer le contenu de R1 sans changer son identifiant | Refus de la preuve liée à l’ancienne règle | 008, 014 |
| A-02 | Changer topologie/timeout en conservant `config_id` | Impact et suspension | PREVENT absent |
| A-03 | Changer le SHA du sujet après qualification | `STALE`, nouvelle qualification | 024 et invalidation absente |
| A-04 | Modifier la révision entre DECIDED et APPLIED | Refus et nouvelle décision | 015 |
| A-05 | Effet externe possible, ACK perdu, retry avec nouvelle clé | HOLD, aucun rejeu aveugle | 018–021 |
| A-06 | Attestation de non-exécution fausse | Hypothèse déclarée et preuve insuffisante | modèle de confiance absent |
| A-07 | Faire dépendre une preuve du verdict qu’elle doit établir | Cycle rejeté | 013 |
| A-08 | ACK fournisseur sans preuve d’effet | Reçu borné seulement | 017, 022 |
| A-09 | Révoquer le mandat avant promotion | Promotion refusée | 004, D-01 |
| A-10 | Diffuser une représentation après supersession de sa configuration | Rejet ou marquage supersédé | 023, 024 |
| A-11 | Refus G-03 faute d’autorité et création d’Écart | Passage par G-Écart versionnée | 010bis, C-01 |
| A-12 | Persistance partielle multi-objets avant crash | Incident, pas d’application partielle implicite | 018 |

## 7. Décisions ouvertes D-01 à D-09

| Décision | Dépendances | État |
|---|---|---|
| D-01 Autorité du mandat d’admission | 004, 006, 007 | Bloque l’activation des portes |
| D-02 États/transitions canoniques et porte G-Écart | 005, 010bis, 011–016 | Bloque la cohérence de 010bis |
| D-03 Définitions des règles du guichet | 007, 008, 015 | Bloque la reproductibilité |
| D-04 Assertion de latence 200 ms | 014, 024 | Fixture non vérifiable sans percentile, charge, période, environnement |
| D-05 Validation des approbations humaines | 004, 022 | Contrat d’interface ambre à définir |
| D-06 Persistance, concurrence, récupération | 011, 015, 018–021 | Bloque les garanties de crash/course |
| D-07 Rétention, accès, protection | 016–018, 022 | Bloque la complétude et l’accessibilité de preuve |
| D-08 Confiance signatures, horloges, ancrages | 012–017 | Bloque la validité des relations cryptographiques |
| D-09 Première validation réelle | 014, 023–024, P6 | Bloque toute qualification empirique indépendante |

## 8. Corrections normatives minimales

### P0

1. Définir et versionner la porte G-Écart avant d’autoriser toute application de 010bis ; supprimer la transition informelle ou la qualifier comme état explicitement non conforme et non promouvable.
2. Déclarer le statut normatif de l’appendice. Si P1–P6 sont obligatoires, les intégrer dans des obligations identifiées ; sinon les marquer informatifs et retirer toute formulation d’équivalence exigible.
3. Ajouter un registre normatif des garanties avec, pour chacune, obligations nécessaires, hypothèses, périmètre, preuves minimales, verdicts permis et exclusions.
4. Ajouter un graphe de dépendances versionné `exigence → garantie → obligation → porte/règle → profil → configuration → hypothèse → preuve → verdict`.
5. Rendre obligatoire l’invalidation transitive après changement de règle, profil, configuration, SHA, environnement, mandat ou hypothèse ; le verdict et les preuves deviennent `STALE` jusqu’à requalification.
6. Rendre PREVENT obligatoire et définir l’événement d’impact, son calcul, son stockage et son effet sur PREPARE.
7. Définir le modèle d’observation et de confiance pour distinguer effet externe possible, effet observé, non-exécution attestée et résultat fournisseur.

### P1

1. Publier les automates LC-01 à LC-09 et G-01 à G-14 dans un format lisible par machine avec transitions interdites.
2. Remplacer « champs applicables » par une matrice obligatoire par `event_type`.
3. Définir atomicité, crash points, récupération et concurrence pour REQUESTED/DECIDED/APPLIED et la consommation ONCE.
4. Définir les cycles interdits du graphe causal et les conditions d’indépendance d’une preuve.
5. Transformer le registre d’extériorité en contrat versionné avec responsable, expiration, tests et méthode de réconciliation.

### P2

1. Ajouter des vecteurs négatifs versionnés pour chaque obligation, y compris 010bis.
2. Définir formellement la fixture de latence 200 ms : percentile, population, charge, environnement, période et version.
3. Publier le PDF canonique, le DOCX source, leurs hashes, la décision d’approbation et le registre de supersession.

## Conclusion finale

REG-ARCH v0.4 établit un vocabulaire, des objets, des portes, des relations et des limites de garantie utiles. Il soutient **sous conditions** la traçabilité bornée d’une décision et la distinction entre intégrité, vérité et effet externe.

Il ne définit pas encore des obligations suffisantes, cohérentes et vérifiables pour PREPARE/PREVENT, l’invalidation des preuves, l’équivalence entre REG-ARCH et ses niveaux opérationnels, ni la création conforme d’un Écart sous 010bis. La réponse finale est donc : **REG-ARCH v0.4 est partiellement soutenable, mais nécessite les corrections P0 avant toute déclaration de couverture architecturale complète.**
