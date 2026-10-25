# Audit contradictoire REG-ARCH v0.4

Le document principal audité est `C:\Users\hp\Downloads\REG-ARCH_v0_4 (1).pdf`, corroboré par `C:\Users\hp\Downloads\REG-ARCH_v0_4.docx`.

Propriétés vérifiées pour la baseline v0.4 :

- version déclarée : 0.4 ;
- date déclarée dans le document : 25 octobre 2026 ;
- statut déclaré : proposition normative, document autonome ;
- SHA-256 : `46752A0E1CD7AAE430742878C14C6B5C28FE1DA8167C9A81D78B23D9BAA7D3C2` ;
- PDF canonique fourni : 11 pages A4, SHA-256 `4BE9D68CA8DCE3557655905467C0975758E82AB2888F974B0B9439D59620B939` ;
- 355 paragraphes et 18 tableaux extraits ;
- 25 obligations présentes : REG-ARCH-001 à 024 et REG-ARCH-010bis ;
- métadonnées DOCX : création 2026-10-24 23:14 UTC, modification 2026-10-25 05:00 UTC.

Le PDF est l’artefact primaire audité pour la baseline v0.4. Le DOCX confirme la version et les tableaux. Le rendu des 11 pages PDF a été contrôlé ; les pages sont lisibles, sans clipping ni chevauchement observé. L’autorité d’approbation reste « à désigner », donc la vérification de l’artefact n’équivaut pas à une ratification normative.

Le rapport distingue le contenu normatif du DOCX, son appendice de méthode, les décisions ouvertes et les propositions de correction. Il ne traite pas les implémentations comme sources normatives.

La candidate de correction v0.4.1, ses copies de source, sa matrice, ses scénarios, ses oracles abstraits et le rapport de relecture sont dans `audits/reg-arch-v0.4.1/`. Hash SHA-256 DOCX candidate : `2C86C2CF275CF2C4028C0F2437DE332D3BC1C5B99C4967EB68C8AEF0DB1532C4`; PDF candidate : `6BE9328006812EF6ED98E7D07AE89FCF68ED08FF8A1C4E5694C4E08AAD0F62BC`. Les livrables candidate sont locaux et non ratifiés. La source v0.4 ci-dessus demeure l’objet audité ; la candidate n’est pas présentée comme norme adoptée.

Vérification locale de la génération courante : 20 oracles de modèle passent, le vérificateur d’artefacts confirme les deux hash sources, la parité du schéma de trace JSON/YAML, 16 scénarios adversariaux et la présence des obligations / décisions ouvertes. Ces contrôles ne sont pas des preuves de conformité d’un déploiement.

Statut de revue : **REG-ARCH v0.4.1 — NORMATIVE REVIEW PASS / DEPLOYMENT CONDITIONAL / RATIFICATION HOLD.** Les fichiers PNG de rendu et le cache Python sont exclus de la PR de revue; sources, DOCX/PDF candidats, schéma, scénarios, tests et outils reproductibles sont conservés.

Le paquet inclut aussi un protocole candidat d’établissement des preuves d’exhaustivité PREPARE/PREVENT, un validateur indépendant JSON Schema/JCS et un workflow CI. Le validateur standard dépend de bibliothèques installées par le workflow et n’a pas pu être lancé dans l’environnement local (module `jcs` absent); le résultat CI reste à vérifier après le push.
