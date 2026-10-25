# CAPTURE_BOUNDARY_SPEC_v0.1 — REG-ARCH

**Statut:** DRAFT — exigences de conception, non démontrées en production.  
**Rattachement:** REG-ARCH issue #51 ; interface expérimentale TENIR-Gov G4-A.  
**Portée:** Banque × Assurance ; aucun constat de conformité sectorielle.

## 0. Limites
- DORA : l'applicabilité dépend de l'entité visée par l'article 2 et du périmètre pertinent, non de la seule criticité d'un service TIC.
- Les preuves cryptographiques locales ne démontrent ni la complétude des événements non observés, ni la vérité des effets externes.
- La validation de primitives cryptographiques ne vaut pas validation de leur intégration sectorielle.

## 1. Frontière
```text
Agent / source (intention, identité, opération)
  -> TENIR interception avant décision/effet
  -> transaction durable (état, epoch, événement, séquence)
  -> reçu / checkpoint (hash, signature, chaînage)
  -> vérification indépendante
```

**Hypothèses à expliciter avant test:** ensemble des writers et points d'entrée, frontière d'autorité, mécanisme d'admission des effets, stockage transactionnel, source indépendante d'inventaire, modèle de confiance des clés, source de vérité des effets externes. Un writer extérieur non contrôlé invalide toute revendication de capture globale.

## 2. Propriétés candidates
| ID | Priorité | Critère d'acceptation borné |
|---|---|---|
| CB-01 | P0 | Aucun chemin d'exécution **autorisé dans le périmètre défini** ne contourne la capture; inventorier et tester les chemins non instrumentés. |
| CB-02 | P0 | État, epoch, événement et numéro de séquence sont persistés atomiquement; aucun état partiellement committé après crash. |
| CB-03 | P1 | Les ruptures **observables** de séquence sont détectées; omission avant capture indétectable sans témoin indépendant. |
| CB-04 | P1 | Reçu lié à opération, tentative, epoch, identité, génération de confiance et validité de clé; révocation documentée. |
| CB-05 | P1 | Un vérificateur indépendant détecte altération, rupture observable et rejeu relativement à un checkpoint ancré; aucune garantie absolue d'exhaustivité. |

## 3. Tests négatifs (RED-first)
| Test | Injection | Oracle | Limite |
|---|---|---|---|
| CB-T01 | Événement omis, avec/sans témoin indépendant | Avec témoin: divergence détectée et HOLD; sans témoin: INCONCLUSIVE, jamais PASS d'exhaustivité | CB-03 |
| CB-T02 | Crash avant/après commit de l'état + journal | Aucun état/journal divergent, reprise idempotente | CB-02 |
| CB-T03 | Rejeu d'un reçu valide mais ancien | Refus sur epoch/checkpoint/génération de confiance non courants | CB-04/05 |
| CB-T04 | Writer tiers non instrumenté tente un effet | Refus seulement si frontière d'autorité effectivement imposée; sinon contre-exemple CB-01 | CB-01 |

## 4. Articulation
G4-A **vise à démontrer**, dans son périmètre expérimental, l'atomicité et la reprise; son implémentation et ses tests ne sont pas qualifiés ici. REG-ARCH définit les obligations de preuve nécessaires pour toute extension de revendication. Les tests de modèle ne constituent pas une preuve d'intégration réelle.

## 5. Verdicts
- **Juridique:** APPLICABILITY CONDITIONAL / UNDETERMINED selon entité et système.
- **Architectural:** DRAFT.
- **Technique sectoriel:** SECTOR EVIDENCE NOT DEMONSTRATED.

**HOLD:** aucune ratification, fusion, promotion production, ni attestation de vérité d'effet externe.
