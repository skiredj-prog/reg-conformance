# REG — Extériorité E8 : témoin externe monotone (v0.2)
**REG-ARCH-022 · Spécifié, non implémenté · 2026-10-25**
**Alignement normatif : TENIR CB-05. P0 R-01, Q1/Q6, C1/C2 ouverts. PRODUCTION HOLD.**

## Objet et frontière
Le témoin est un service sur un **hôte et domaine d'administration distincts**, avec identité cryptographique et persistance indépendantes. Il conserve une tête attestée, non les données métier. Un stockage secondaire sous le même UID, une base locale, un fichier partagé modifiable par le runtime ou une variable d'environnement ne sont pas un témoin E8.

Le runtime ne revendique que les transitions dont la continuité et la fraîcheur ont été vérifiées auprès du témoin. La preuve d'un effet chez un fournisseur externe reste hors E8 (E1).

## Tête attestée
```python
@dataclass(frozen=True)
class AttestedHead:
    realm_id: str
    store_id: str
    epoch: int
    sequence: int
    state_digest: str
    key_digest: str
    quarantine_digest: str
    previous_head_digest: str
```
Le digest canonique de la tête est lié au domaine `REG-E8-HEAD-v1`. Le témoin vérifie l'identité du client autorisé, l'intégrité des champs, la signature et l'état attendu avant tout avancement. L'état du témoin est durable et linéarisable. La configuration initiale, la rotation de clés, les changements d'epoch et le retrait d'un store exigent des cérémonies explicites authentifiées.

## Interface normative
```python
class ExternalWitness(Protocol):
    def get_head(self, realm_id: str, store_id: str) -> AttestedHead | None: ...
    def compare_and_advance(self, expected_head_digest: str, new_head: AttestedHead, authorization: bytes) -> AttestedHead: ...
    def health(self) -> bool: ...
```
`compare_and_advance` est **atomique** : il compare la tête courante à `expected_head_digest`, vérifie `previous_head_digest`, la progression de séquence, l'epoch, l'autorisation et la liaison à la transition, puis persiste et atteste la nouvelle tête. Une réponse perdue exige une lecture de réconciliation ; le client ne présume ni succès ni échec. Une même séquence avec un digest divergent est refusée.

## Boot gate
Avant toute admission, le runtime récupère une tête fraîche et authentifiée. Il refuse ENFORCE si témoin absent, non authentifié, stale, ou si les digests de l'état, des clés ou de la quarantaine divergent. Une tête locale de séquence **supérieure** n'est pas automatiquement acceptable : elle exige la réconciliation d'une chaîne authentifiée avec la tête actuelle du témoin. Une tête locale inférieure est une régression. Un état local `sequence=0` face à un témoin non initial est ambigu. `SHADOW_OBSERVE` peut rester strictement sans écriture ni admission.

## Transition gate
La lecture de `get_head` seule ne ferme pas la course entre vérification et admission. Les admissions critiques doivent être liées à un **compare-and-advance** linéarisable et à une vérification cohérente de l'autorité locale, des grants, de la quarantaine et de l'epoch. Les modifications de quarantaine doivent également être ancrées. La coordination des transactions locales et de l'ACK du témoin doit être conçue pour ne jamais autoriser un effet externe sur une admission non attestée. Tout doute : HOLD_GLOBAL.

## Commit gate et ambiguïté
- `CONFIRMED` : commit local durable et tête témoin vérifiée ; ne prouve pas l'effet fournisseur.
- `LOCAL_COMMITTED_WITNESS_PENDING` : commit local confirmé, attestation témoin non confirmée ; **pas un succès opérationnel**, aucune nouvelle admission dépendante, réconciliation obligatoire.
- `OUTCOME_UNKNOWN` : issue du commit local inconnue ; aucune répétition d'effet sans résolution.
Un timeout témoin peut cacher un avancement réussi ; résoudre par `get_head` avant tout nouvel avancement. La transition de récupération est signée et journalisée, jamais silencieuse.

## Ce qui n'est pas garanti
Aucune inviolabilité si l'attaquant contrôle aussi le témoin, aucune reconstruction automatique d'un état perdu, aucune prévention de l'écriture directe par un acteur local privilégié (G1 reste nécessaire), aucune preuve d'effet fournisseur. Une simple vérification au démarrage détecterait seulement certaines altérations différées ; E8 exige une participation aux transitions critiques.

## Conformité et preuves minimales
Tester : restauration à séquence inférieure et **égale**, remplacement complet de fichier d'autorité, substitution de racines/clé de reçu, suppression/restauration de quarantaine, tête locale artificiellement supérieure, race lecture/admission, concurrence CAS, réponse CAS perdue, partition, crash entre SQLite COMMIT et témoin, rotation et récupération hors bande. Chaque résultat doit porter le SHA du SUT, la provenance, les logs et la preuve du domaine de confiance indépendant.

**Statut : architecture spécifiée, aucun témoin connecté à TENIR-Gov v5.7.0, aucun test d'intégration E8 officiel. P0 ouverts.**
