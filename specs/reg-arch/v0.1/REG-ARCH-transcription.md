# REG-ARCH v0.1 — transcription de travail

> **Statut :** Proposition normative — à valider sur implémentation. Autorité d’approbation à désigner.
>
> **Provenance :** transcription textuelle du document « REG Lifecycle - Specification d'architecture - cycles, lanes et décisions(1).docx », daté du 24 octobre 2026, fourni dans les échanges du projet.
>
> **Important :** cette transcription préserve le texte extrait, mais la mise en forme du DOCX (notamment les tableaux) doit être relue avant d’en faire une publication normative. Ne pas interpréter ce dépôt comme une approbation, un audit ou une certification.

---

````text
REG — Spécification d’architecture

Articulation des cycles, des lanes et traçabilité des décisions

Champ                     Valeur

Référence                 REG-ARCH

Version                   0.1

Date                      24 octobre 2026

Statut                    Proposition normative — à valider sur implémentation

Source                    Texte de conception et analyses fournis dans cette conversation

Autorité d’approbation À désigner

Périmètre                 Modèle architectural et exigences de traçabilité

                          Certification, vérification des dépôts et attestation de comportements
Hors périmètre
                          existants

1. Objet et conventions

1.1. Objet

La présente spécification définit comment REG articule :

         les lanes, qui distinguent la nature des activités ;

         les cycles de vie, qui définissent les états autorisés des objets ;

         les portes, qui gouvernent les transitions et les passages entre objets ;

         les événements, qui rendent chaque décision reconstructible ;

         les frontières, qui bornent les responsabilités et la portée des conclusions.

L’architecture vise la propriété suivante :

Chaque objet conserve son identité ; chaque passage significatif est gouverné par une porte nommée
; chaque décision est traçable ; aucune conclusion ne dépasse la portée de ses éléments justificatifs.

1.2. Portée normative

DOIT et NE DOIT PAS expriment une obligation de conformité à cette spécification. DEVRAIT exprime
une recommandation dont toute dérogation doit être justifiée. PEUT désigne une possibilité.

Ces termes ne revendiquent aucune conformité à un standard externe.

REG-ARCH-001 — Distinction des statuts. Toute présentation de cette architecture DOIT distinguer :

    1. une exigence proposée ;

    2. un comportement spécifié ;

    3. un comportement implémenté ;

    4. un comportement vérifié sur pièces.

Le présent document ne démontre que la formulation d’une architecture proposée.



2. Modèle architectural

2.1. Niveaux de description

Niveau       Question traitée                                                   Artefact de référence

Lane         Quelle est la nature de l’activité ?                               Carte topologique

Cycle        Quels états cet objet peut-il prendre ?                            Machine à états typée

                                                                                Contrat de porte
Porte        À quelles conditions le passage est-il permis ?
                                                                                versionné

             Quelle demande, quelle décision et quelle application ont eu
Événement                                                                 Journal
             lieu ?

Frontière    Que gouverne REG et que laisse-t-il à l’extérieur ?                Registre d’extériorité

REG-ARCH-002 — Séparation des niveaux. Une lane NE DOIT PAS être utilisée comme machine à
états. Une porte NE DOIT PAS être confondue avec un état. Un événement enregistré NE DOIT PAS
être assimilé à une transition appliquée.

2.2. Les trois lanes

Lane                   Responsabilité                              Objets principaux

                       Formuler, qualifier et admettre ce qui      Hypothèse, propriété, invariant,
A — Prétention
                       peut être affirmé du système                qualification probatoire

                       Gouverner une tentative d’exécution et      Intention, tentative, réservation,
B — Action
                       traiter son issue                           résultat, réconciliation, reçu

C—                     Produire et faire circuler une              Badge, brief, export, déclaration
Représentation         représentation fidèle d’un état qualifié    publique

Les services de preuve, de journalisation, de versionnement et de gestion des dossiers peuvent servir
plusieurs lanes. Ils ne constituent pas une quatrième lane générique.

2.3. Articulation générale

LANE A — PRÉTENTION

Hypothèse ── création liée ──> Propriété candidate

                       │

                 Admission autorisée

                       │

                Invariant admis/versionné

                       │

            Liaison explicite aux règles runtime

                       ▼
LANE B — ACTION

Intention ── autorisation ──> Tentative ── engagement ──> Issue

                    │              │

                    └──── HOLD / réconciliation

                                   │

                           Reçu à portée bornée

                                   │

            Qualification et autorisation de représentation

                                   ▼
LANE C — REPRÉSENTATION

État qualifié ──> Livrable borné ──> Circulation ──> Supersession



Services communs :

preuves · vérifications · journal · dossiers · artefacts · mandats



Frontières explicites :

approbation humaine · fournisseur externe · consommateurs aval

Les flèches représentent des dépendances gouvernées, non une chaîne automatique de promotions.



3. Identité et responsabilité des objets

3.1. Identité stable

REG-ARCH-003 — Identité typée. Tout objet gouverné DOIT posséder un identifiant stable, un type,
une version ou révision pertinente, et un responsable.

Une hypothèse soutenue ne devient pas une propriété par changement de type. Elle peut être la
source d’une nouvelle propriété, liée à l’hypothèse d’origine.

L’admission d’une propriété qualifie une version déterminée. Elle ne vaut pas admission de ses
versions futures.

3.2. Objets minimaux

Objet                  Fonction

Hypothèse              Supposition explicitée et confrontable

Objet                  Fonction

Propriété              Énoncé auquel peuvent être associés un périmètre et une méthode de contrôle

Invariant admis        Version de propriété admise par une autorité habilitée

Tentative              Unité d’exécution gouvernée

Élément de preuve Pièce conservée avec provenance et intégrité identifiables

Vérification           Opération portant sur un objet, une méthode et une portée déterminés

Reçu                   Attestation bornée d’un enregistrement ou d’une décision REG

Dossier                Unité de demande, d’instruction et de clôture

Représentation         Objet destiné à communiquer un état qualifié

Écart                  Différence identifiée entre contrat, implémentation ou preuve

Artefact               Livrable versionné

Mandat                 Référence d’habilitation d’un acteur

3.3. Responsabilité

REG-ARCH-004 — Attribution effective. Un rôle documentaire ne constitue pas une nomination.
Avant activation d’une porte exigeant une autorité, REG DOIT pouvoir identifier :

         l’acteur effectif ;

         son rôle au moment de la décision ;

         son mandat applicable ;

         le périmètre et la validité de cette habilitation.

Une porte nécessitant une autorité non désignée DOIT rester inactive ou refuser les demandes
concernées. Les contrôles indépendants de cette autorité peuvent continuer.



4. Articulation des cycles de vie

Les neuf cycles constituent l’inventaire initial. Leur maintien comme machines autonomes dépend de
la stabilité de leurs objets et de leurs responsabilités.

                                                                                 Responsable fonctionnel
Cycle                   Objet gouverné                 Position architecturale
                                                                                 proposé

                        Propriété et admission
LC-01 — Autorité                                       Lane A ; liaison vers B   Autorité d’admission
                        d’une version

                                                       Service commun,           Responsable de
LC-02 — Preuve          Qualification probatoire
                                                       principalement A          qualification

LC-03 — Hypothèse Supposition                          Lane A                    Responsable Discovery

                                                                                 Responsable fonctionnel
Cycle                Objet gouverné                    Position architecturale
                                                                                 proposé

LC-04 — Exécution Tentative runtime                    Lane B                    Responsable d’exécution

LC-05 —              Entrée, chaîne, checkpoint,
                                                 Service commun                  Responsable du journal
Enregistrement       ancre

LC-06 —              Évaluation d’une
                                                       Workflow de dossier       Responsable du guichet
Configuration        configuration versionnée

LC-07 —              Déclaration et                                              Responsable de
                                                       Lane C
Réclamation          représentation publique                                     publication

LC-08 — Écart        Gap classé et vérifié             Service commun            Responsable d’audit

                                                                                 Responsable de
LC-09 — Artefact     Version d’un livrable             Service commun
                                                                                 publication technique

Ces responsabilités sont des rôles proposés, non des nominations effectives.

4.1. Machines distinctes

REG-ARCH-005 — États locaux. Chaque cycle DOIT définir ses propres états, transitions,
préconditions, effets et refus.

Les expressions suivantes NE DOIVENT PAS être fusionnées :

       hypothèse non résolue ;

       élément de preuve non lié ;

       résultat d’exécution indéterminé ;

       dossier incomplet.

Leur point commun est une règle de non-promotion, pas un état universel.

4.2. Distinctions obligatoires

REG-ARCH-006 — Absence de promotion implicite.

Qualification obtenue      Ne permet pas de conclure automatiquement

Propriété testable         Propriété admise

Propriété admise           Propriété satisfaite

Test exécuté               Test réussi

Journal intègre            Affirmation vraie

Configuration admissible Capacité démontrée

Décision acceptée          Transition appliquée

Reçu émis                  Effet fournisseur réalisé

4.3. Terminaison et correction

La supersession remplace une référence courante sans effacer l’historique. La réfutation conteste
une prétention sur la base d’éléments identifiés. Le retrait cesse d’autoriser une représentation ou
un usage.

Une compensation externe est une nouvelle action. Elle NE DOIT PAS être décrite comme
l’effacement rétroactif de l’action initiale.



5. Contrat des portes

5.1. Contenu obligatoire

REG-ARCH-007 — Porte explicite. Toute porte DOIT définir :

Champ      Contenu

Identité   Identifiant et version

Entrées    Objets et versions considérés

Demande Transition ou création demandée

Conditions Critères vérifiables d’acceptation

Autorité   Acteur ou politique habilitée

Refus      Codes de motif et conditions de déclenchement

Effets     Objets créés ou états modifiés

Trace      Événements exigés

Frontière Conclusions et effets non couverts

Un passage entre lanes ou une création causale entre objets DOIT référencer une porte. Les simples
consultations ne constituent pas nécessairement des transitions.

5.2. Catalogue initial proposé

Porte                Passage gouverné                          Condition principale de refus

G-01 —               Hypothèse → nouvelle propriété
                                                               Énoncé ou filiation insuffisant
Formulation          candidate

G-02 — Testabilité Candidate → propriété testable              Méthode ou critères indéfinis

                                                               Autorité, mandat ou conditions
G-03 — Admission Propriété → version admise
                                                               manquants

G-04 — Liaison       Invariant admis → règles applicables à    Version incompatible, invalide ou non
runtime              une tentative                             résolue

G-05 — ADMIT         Intention → autorisation située           Conditions d’autorisation non

Porte                Passage gouverné                            Condition principale de refus

                                                                 satisfaites

                     Autorisation →                              Clé déjà consommée ou contrôle
G-06 — ONCE
                     réservation/consommation de clé             concurrent non garanti

G-07 —
                     Issue indéterminée → issue qualifiée        Éléments insuffisants
Réconciliation

                                                                 Provenance ou intégrité minimales
G-08 — Capture       Pièce reçue → pièce enregistrée
                                                                 insuffisantes

G-09 —
                     Pièce → objet et version désignés           Liaison invalide ou ambiguë
Rattachement

G-10 —               Pièce liée → conclusion probatoire          Méthode, portée ou résultat
Qualification        bornée                                      insuffisant

                                                                 Enregistrement durable ou portée
G-11 — Reçu          Enregistrement qualifié → reçu
                                                                 manquante

G-12 — Circulation État qualifié → représentation diffusée       Sur-revendication ou frontière absente

G-13 —               Version publiée → nouvelle référence
                                                                 Filiation ou autorité manquante
Supersession         courante

G-14 — Clôture       Dossier ouvert → dossier clos               Motif ou décision de clôture absent

5.3. Admission et runtime

REG-ARCH-008 — Liaison explicite. Toute décision runtime utilisant un invariant DOIT référencer sa
version admise et le snapshot des règles effectivement évaluées.

L’admission ne constitue ni une autorisation universelle d’exécution ni une preuve d’effet externe.

5.4. Preuve

REG-ARCH-009 — Trois opérations distinctes. La capture d’une pièce, son rattachement et sa
qualification probatoire DOIVENT être distingués.

Un benchmark peut être conservé sans être reconnu comme preuve d’une propriété admise.

5.5. Refus et clôture

REG-ARCH-010 — Effets séparés. Le refus d’une transition NE DOIT PAS modifier l’état de l’objet
cible.

Si ce refus entraîne la clôture d’un dossier, cette clôture DOIT être une transition distincte,
causalement liée au refus.

Une demande portant sur un autre SHA constitue un nouveau dossier lorsque la règle du workflow
l’exige ; elle ne réouvre pas silencieusement le dossier clos.



6. Traçabilité de chaque décision

6.1. Trois faits distincts

REG-ARCH-011 — Séparation temporelle. Le modèle DOIT distinguer :

Événement Signification

REQUESTED Une transition a été demandée

DECIDED         Une porte a accepté ou refusé la demande

APPLIED         La transition acceptée a effectivement été appliquée

Une décision ACCEPTED peut rester sans application. L’absence de APPLIED NE DOIT PAS être
interprétée comme une application réussie.

La persistance de l’événement est une propriété indépendante. RECORDED n’est donc pas une
alternative à REFUSED.

6.2. Enveloppe commune

REG-ARCH-012 — Données minimales. Chaque événement DOIT porter les informations applicables
suivantes.

Groupe           Champs

Identification event_id, event_type, schema_version

Objet            object_id, object_type, object_revision

Ordre local      object_event_sequence, prev_object_event_id

Causalité        correlation_id, causation_event_ids

Demande          request_id, transition demandée, état/version attendus

Acteur           Identité effective, rôle, mandate_ref lorsque requis

Porte            gate_id, gate_version, référence ou digest des règles

Temps            Date d’enregistrement et, si distincte, date déclarée du fait

Décision         ACCEPTED ou REFUSED, uniquement pour DECIDED

Motifs           Codes stables et explication contextualisée

Application      Référence de la décision et état effectivement obtenu

Justificatifs    Références, versions, digests et algorithmes

Frontières       Références des contrats externes pertinents

Une séquence d’événements et une révision d’état sont distinctes : un refus enrichit la première sans
nécessairement modifier la seconde.

6.3. Chaînage et causalité

REG-ARCH-013 — Deux relations distinctes.

prev_object_event_id relie les événements d’un même objet.

causation_event_ids relie un événement aux faits qui l’ont causé, y compris sur d’autres objets.

La création d’une propriété peut ainsi référencer une décision concernant une hypothèse sans
fusionner leurs historiques.

6.4. Vérification qualifiée

REG-ARCH-014 — Portée de vérification. Toute vérification DOIT identifier :

       l’objet et sa version ;

       la méthode et sa version ;

       les éléments examinés ;

       le résultat ;

       la portée de la conclusion ;

       l’acteur ou le système vérificateur.

Un statut VERIFIED sans ces précisions est insuffisant pour autoriser une promotion.

6.5. Concurrence

REG-ARCH-015 — Application sur version attendue. Une transition acceptée NE DOIT être appliquée
que si les préconditions et versions requises restent valides.

Si l’objet a changé, REG DOIT enregistrer la non-application et imposer une nouvelle évaluation
lorsque nécessaire. Il NE DOIT PAS réutiliser silencieusement la décision sur un autre état.



7. Journal, reconstruction et intégrité

7.1. Journal append-only

REG-ARCH-016 — Historique non effacé. Le journal des décisions DOIT être append-only au niveau
logique. Une correction DOIT ajouter un événement référençant l’élément corrigé.

Un mécanisme d’interface « Undo » peut demander une nouvelle action ; il NE DOIT PAS supprimer
la trace historique de la décision initiale.

7.2. Reconstruction

Pour un objet donné, le lecteur autorisé DOIT pouvoir reconstruire :

    1. les demandes ;

    2. les règles évaluées ;

    3. les acteurs et mandats ;

    4. les décisions et motifs ;

    5. les applications effectives ;

    6. les pièces justificatives ;

    7. les corrections et supersessions ;

    8. les frontières de portée.

L’ordre entre objets repose sur les liens causaux. Les horodatages seuls ne suffisent pas à établir cet
ordre.

7.3. Limites de l’intégrité

REG-ARCH-017 — Non-confusion des garanties. Un hash, une signature ou une ancre peut
contribuer à établir l’intégrité ou la provenance d’un enregistrement. Aucun de ces mécanismes ne
démontre, à lui seul :

       la vérité de son contenu ;

       la légitimité de l’acteur ;

       la satisfaction d’une propriété ;

       l’effet réalisé par un fournisseur.

7.4. Défaut de persistance

REG-ARCH-018 — Sortie gouvernée. Lorsque la trace durable est une précondition d’engagement,
l’impossibilité de l’établir DOIT bloquer cet engagement.

Si un effet externe a néanmoins pu se produire, REG DOIT traiter la situation comme un incident à
réconcilier, sans présumer l’annulation ni autoriser un rejeu aveugle.



8. Inconnu et exécution externe

8.1. Règle de non-promotion

REG-ARCH-019 — Justification positive. L’absence de contradiction, de réponse ou de preuve
négative NE DOIT PAS être utilisée comme justification d’une confirmation.

8.2. HOLD

REG-ARCH-020 — Issue indéterminée. Lorsqu’un engagement externe a pu avoir lieu sans issue
déterminée, la tentative DOIT interdire le rejeu non autorisé jusqu’à application de la procédure de
réconciliation.

HOLD ne signifie ni échec certain, ni absence d’effet, ni annulation.

8.3. Idempotence

REG-ARCH-021 — Portée locale. Le contrôle ONCE DOIT préciser son domaine, sa clé, sa durée et son
comportement concurrent.

L’idempotence d’ingestion d’un événement, la consommation d’une clé d’exécution et l’idempotence
du fournisseur sont trois garanties distinctes. Une clé locale ne suffit pas à garantir un effet externe «
exactement une fois ».



9. Registre d’extériorité

REG-ARCH-022 — Contrat de frontière. Chaque interface externe pertinente DOIT posséder une
entrée identifiant les responsabilités, les éléments attendus et les conclusions exclues.

                    Ce que REG peut          Ce qu’il n’affirme pas        Contrat et responsable
Zone
                    affirmer sous conditions automatiquement               proposés

                    Décision locale,
                                                                           Contrat fournisseur,
                    émission de demande,     Débit, remboursement ou
Fournisseur de                                                             identifiants de transaction,
                    réponse reçue,           règlement effectif à partir
paiement                                                                   règles de réconciliation ;
                    réconciliation           du seul envoi
                                                                           responsable intégration
                    documentée

                                            Remplacement de                Identité, mandat, portée,
                    Réception et validation
Approbation                                 l’approbateur ou validité      durée, canal et retrait ;
                    d’une approbation selon
humaine ambre                               d’un email par sa seule        responsable du processus
                    une méthode définie
                                            présence                       d’approbation

                                            Rapprochement financier Accusé de réception et
Consommateurs       Émission ou remise d’un
                                            ou constitution effective du règles d’usage ;
aval du reçu        reçu borné
                                            dossier d’audit              responsable aval

Ces entrées sont un modèle initial, non des contrats déjà vérifiés.

Le reçu DOIT préciser ce qu’il atteste dans REG et ce qu’il n’établit pas dans le monde externe.



10. Représentation et provenance

REG-ARCH-023 — Frontière transportable. Tout livrable sortant DOIT porter, directement ou par
référence durable accessible :

       l’objet et la version concernés ;

       le statut représenté ;

       la portée de la qualification ;

       les exclusions pertinentes ;

       une référence de traçabilité ;

       son statut de validité ou de supersession.

Une représentation NE DOIT PAS laisser entendre une certification non établie.

REG-ARCH-024 — Artefact dérivé. Un artefact déclaré régénérable DOIT identifier ses sources
versionnées, son générateur et les paramètres nécessaires à sa régénération. Une modification
manuelle non tracée invalide cette déclaration jusqu’à régularisation.



11. Tranche de référence : latence 200 ms

Cette tranche est une fixture illustrative, non une exécution attestée.

L’énoncé « latence inférieure à 200 ms » demeure incomplet tant que ne sont pas définis le
percentile, la population, la charge, l’environnement, la période et la version.

Étape                     Objet                  Décision illustrative        Effet

Confrontation             Hypothèse H-01         Contestation enregistrée     Historique enrichi

Demande de soutien        H-01                   Refus faute d’éléments liés État inchangé

                          Nouvelle propriété     Création acceptée puis       P-01 créée avec lien vers
Formulation
                          P-01                   appliquée                    H-01

                                                 Refus faute d’autorité
Admission                 P-01                                                P-01 non admise
                                                 désignée

Qualification du                                 Refus faute de liaison       Aucune satisfaction
                          Qualification Q-01
benchmark                                        suffisante                   déclarée

La conservation d’un benchmark peut rester autorisée indépendamment du refus de sa qualification
probatoire.

Cette fixture valide la capacité du modèle à exprimer les décisions. Elle ne prouve ni la performance
ni l’existence historique de ces événements.



12. Vérification de conformité

Les tests suivants sont requis ; aucun résultat d’exécution n’est revendiqué ici.

Test                    Comportement attendu                                               Exigences

                                                                                           007, 010,
T-01 — Refus traçable Motif, porte et version présents ; état cible inchangé
                                                                                           012

T-02 — Acceptation
                        Une acceptation sans application ne change pas l’état              011
différée

T-03 — Création
                        Nouvel identifiant et lien causal, sans mutation de type           003, 013
interobjet

T-04 — Autorité
                        Admission refusée ; contrôles indépendants possibles               004, 006
absente

T-05 — Portée de
                        Intégrité vérifiée sans conclusion automatique de satisfaction     014, 017
preuve

T-06 — Clôture de
                        Clôture distincte et liée au refus initial                         010
dossier

T-07 — Concurrence      Décision non appliquée sur version devenue invalide                015

T-08 — Issue inconnue Aucun rejeu aveugle ; réconciliation exigée                          019–021

T-09 — Correction       Événement additionnel ; aucune suppression historique              016

Test                     Comportement attendu                                                 Exigences

T-10 — Perte de
                         Blocage préalable ou incident explicite si effet possible            018
persistance

T-11 — Sortie publique Diffusion refusée si portée ou frontière absente                       023

T-12 — Provenance        Sources et générateur permettent de contrôler la régénération 024

T-13 — Hors              Un objet réel non utilisé pour concevoir le modèle est
                                                                                              002–014
échantillon              représentable sans exception ad hoc

La validation DOIT distinguer :

    1. validité structurelle des données ;

    2. validité sémantique des décisions ;

    3. conformité de l’implémentation ;

    4. portée probatoire des résultats obtenus.

Un schéma JSON valide ne suffit pas à établir les trois derniers points.



13. Déploiement progressif

Étape          Fonctionnement                                  Condition de sortie

               Inventorier objets, décisions, portes et        Identités, responsabilités et références
Visibilité
               frontières sans modifier les verdicts existants suffisamment définies

               Évaluer les portes et produire les traces sans Divergences analysées ; tests négatifs
Shadow
               déclencher leurs effets                        satisfaits

               Appliquer les refus et autorisations dans le    Autorités désignées, journal durable,
Enforcement
               périmètre explicitement activé                  procédures de récupération validées

L’ordre de travail recommandé est : registre d’extériorité et contrat commun, fixture latence, objet
réel documenté, cas hors échantillon, puis activation progressive.

Aucune porte d’admission ne doit être activée sans autorité désignée. Cette restriction ne bloque pas
les travaux techniques indépendants.



14. Décisions ouvertes

Référence Décision à prendre                                               Artefact attendu

                                                                           Politique d’autorité
D-01         Qui octroie et contrôle le mandat d’admission ?
                                                                           approuvée

             Quels états et transitions sont canoniques pour chaque
D-02                                                                       Machines versionnées
             cycle ?

Référence Décision à prendre                                                Artefact attendu

                                                                            Contrats référencés et
D-03        Quelles sont les définitions exactes des règles du guichet ?
                                                                            versionnés

D-04        Quelle assertion précise porte la mesure de latence ?           Spécification de propriété

D-05        Comment sont validées les approbations humaines ?               Contrat d’interface ambre

            Quels mécanismes assurent persistance, concurrence et
D-06                                                                        Spécification technique
            récupération ?

            Quelles politiques de rétention, d’accès et de protection       Politique de journal et de
D-07
            s’appliquent ?                                                  preuve

            Quel modèle de confiance couvre signatures, horloges et         Modèle de menace et
D-08
            ancrages ?                                                      vérification

                                                                            Dossier de validation
D-09        Quelles pièces réelles constituent la première validation ?
                                                                            accessible

15. Critère final d’acceptation

L’architecture sera considérée comme validée dans un périmètre donné lorsque :

Pour chaque décision de ce périmètre, un lecteur autorisé pourra retrouver la demande, l’acteur
habilité, la porte et ses règles, les versions évaluées, les motifs, l’application effective ou sa non-
réalisation, les éléments justificatifs et les limites de la conclusion.

La garantie visée est la traçabilité d’une décision gouvernée. Elle n’est ni une garantie universelle
de vérité, ni une certification, ni une preuve automatique d’effet externe.
````
