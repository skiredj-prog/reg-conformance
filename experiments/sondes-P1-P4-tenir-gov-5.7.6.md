# Sondes P1–P5 sur TENIR-Gov 5.7.6, avec 5.7.0 en contrôle

**Statut : preuve expérimentale historique.** Ce n'est pas un passage du harnais REG, ni une qualification, ni une conformité. Fournisseur simulé, un seul processus, aucun effet externe indépendant vérifié.

| Élément | Valeur |
| --- | --- |
| Date d'exécution (UTC) | 2026-11-23T09:13:53Z |
| Exécutant | Claude (assistant de l'auteur), conteneur Linux (Linux 6.18.44-fc-v726) |
| Python | 3.13.18, pip 26.2.2, un environnement virtuel isolé par version |
| Sujet | `skiredj-prog/tenir_governance`, tag `v5.7.6` (`1881c90bb33a0cf1218df5381698c4e3c8dd4df2`) |
| Contrôle | même dépôt, tag `v5.7.0` (`47ef67e3efc5f3008896a7d88bebf929fa0a98f0`) |
| Installation | `pip install <checkout du tag>` (non éditable), import vérifié depuis un dossier neutre avec `python -I`. Les paquets publiés sur PyPI n'ont pas été utilisés |
| Effets | `MockProvider` : un appel compté = un effet |
| Registre | en mémoire, un processus |

## Ce que chaque sonde demande

| Sonde | Question | Entrées |
| --- | --- | --- |
| P1a | Avec des entrées idéales et la politique par défaut, un PASS émerge-t-il ? Un FLAG est-il admis ? | pression et vélocité 0, les cinq autres axes à 1 |
| P1b | Avec des conditions de FLAG déclarées, la répartition exige-t-elle leur acquittement exact ? | idem, `flag_conditions=("ops supervision",)` |
| P2 | `option_space` absent : admission ou HOLD ? | entrées favorables, `option_space=None` |
| P3 | Délégation retirée entre l'admission et la répartition : refus ? | délégation alice → bob admise, puis alice ré-enregistrée sans délégué |
| P4 | HOLD borné par τ_K = 60 s, résolution 120 s plus tard : refus ? | HOLD obtenu par `option_space=None`, horloge du gouverneur avancée par remplacement de `_utc_now_epoch` |
| P5 | `irreversibility_materiality` absente : traitée comment, et déclarée non mesurée ? | entrées favorables ; absente, puis 0.0, 0.6 et 1.0 |

## Premier essai, invalide

La première version du script ne passait pas à la répartition la charge utile autorisée à l'admission. Les répartitions qui auraient dû réussir étaient donc refusées, sur les deux versions ; le motif, vérifié sur P1b avec l'acquittement exact, était « Dispatch payload does not match the payload authorized at adjudication ». Sans aucune répartition réussie, l'essai n'avait pas de témoin positif : il ne distinguait pas un refus du runtime d'un refus causé par le script. Ce script n'affichait pas les motifs. Il a été rejoué à l'identique le jour du dépôt ; sorties :

```
== TENIR-Gov 5.7.6 ==

P1a  entrées idéales, politique par défaut
      {'scoring_decision': 'FLAG', 'membrane_decision': 'PASS', 'composed_decision': 'HOLD', 'operation_state': 'hold'} | 
P1b  entrées idéales, conditions déclarées ('ops supervision',)
      {'scoring_decision': 'FLAG', 'membrane_decision': 'PASS', 'composed_decision': 'FLAG', 'operation_state': 'reserved'} | 
      sans acquittement      : {'dispatched': False, 'operation_state': 'reserved'} | effets : 0
      acquittement inexact   : {'dispatched': False, 'operation_state': 'reserved'} | effets : 0
      acquittement exact     : {'dispatched': False, 'operation_state': 'reserved'} | effets : 0
P2   option_space absent
      {'scoring_decision': 'HOLD', 'membrane_decision': 'PASS', 'composed_decision': 'HOLD', 'operation_state': 'hold'} | 
P3   délégation alice → bob retirée après l'admission
      admission : {'scoring_decision': 'FLAG', 'membrane_decision': 'PASS', 'composed_decision': 'FLAG', 'operation_state': 'reserved'} | 
      répartition après retrait : {'dispatched': False, 'operation_state': 'failed', 'execution_record': 'CONFIRMED_NONEXECUTION'} | effets : 0
P4   HOLD borné par τ_K = 60 s, résolution 120 s plus tard
      entrée : {'scoring_decision': 'HOLD', 'membrane_decision': 'PASS', 'composed_decision': 'HOLD', 'operation_state': 'hold'} | 
      résolution tardive : {'composed_decision': 'HARD_VETO', 'operation_state': 'failed'} | 
      répartition : {'dispatched': False, 'operation_state': 'failed'} | effets : 0

== TENIR-Gov 5.7.0 ==

P1a  entrées idéales, politique par défaut
      {'scoring_decision': 'FLAG', 'membrane_decision': 'PASS', 'composed_decision': 'FLAG', 'operation_state': 'reserved'} | 
      répartition sans acquittement : {'dispatched': False, 'operation_state': 'reserved'} | effets : 0
P1b  entrées idéales, conditions déclarées ('ops supervision',)
      n/a sur 5.7.0 (CompositionPolicy.__init__() got an unexpected keyword argument 'flag_conditions')
P2   option_space absent
      {'scoring_decision': 'FLAG', 'membrane_decision': 'PASS', 'composed_decision': 'FLAG', 'operation_state': 'reserved'} | 
      répartition : {'dispatched': False, 'operation_state': 'reserved'} | effets : 0
P3   délégation alice → bob retirée après l'admission
      admission : {'scoring_decision': 'FLAG', 'membrane_decision': 'PASS', 'composed_decision': 'FLAG', 'operation_state': 'reserved'} | 
      répartition après retrait : {'dispatched': False, 'operation_state': 'reserved'} | effets : 0
P4   HOLD borné par τ_K = 60 s, résolution 120 s plus tard
      n/a sur 5.7.0 (CompositionPolicy.__init__() got an unexpected keyword argument 'flag_conditions')
```

Correction : `dispatch_and_execute(key, "b", 10.0, metadata=PAYLOAD, ...)`, et affichage du motif de refus. Le témoin positif de P1b (une répartition réussie avec l'acquittement exact) montre que l'essai corrigé distingue un refus d'un succès.

## Essai corrigé, P1 à P4

```
== TENIR-Gov 5.7.6 ==

P1a  entrées idéales, politique par défaut
      {'scoring_decision': 'FLAG', 'membrane_decision': 'PASS', 'composed_decision': 'HOLD', 'operation_state': 'hold'} | 
P1b  entrées idéales, conditions déclarées ('ops supervision',)
      {'scoring_decision': 'FLAG', 'membrane_decision': 'PASS', 'composed_decision': 'FLAG', 'operation_state': 'reserved'} | 
      sans acquittement      : {'dispatched': False, 'operation_state': 'reserved', 'motif': 'FLAG conditions not acknowledged: the dispatch of a FLAG-admitted operation requires flag_'} | effets : 0
      acquittement inexact   : {'dispatched': False, 'operation_state': 'reserved', 'motif': 'FLAG condition acknowledgement refused: it must cover exactly the declared conditions (ops'} | effets : 0
      acquittement exact     : {'dispatched': True, 'operation_state': 'confirmed'} | effets : 1
P2   option_space absent
      {'scoring_decision': 'HOLD', 'membrane_decision': 'PASS', 'composed_decision': 'HOLD', 'operation_state': 'hold'} | 
P3   délégation alice → bob retirée après l'admission
      admission : {'scoring_decision': 'FLAG', 'membrane_decision': 'PASS', 'composed_decision': 'FLAG', 'operation_state': 'reserved'} | 
      répartition après retrait : {'dispatched': False, 'operation_state': 'failed', 'execution_record': 'CONFIRMED_NONEXECUTION', 'motif': "MANDATE_REVALIDATION_FAILED at dispatch (delegation from 'alice' to 'bob' is withdrawn): F"} | effets : 0
P4   HOLD borné par τ_K = 60 s, résolution 120 s plus tard
      entrée : {'scoring_decision': 'HOLD', 'membrane_decision': 'PASS', 'composed_decision': 'HOLD', 'operation_state': 'hold'} | 
      résolution tardive : {'composed_decision': 'HARD_VETO', 'operation_state': 'failed'} | 
      répartition : {'dispatched': False, 'operation_state': 'failed', 'motif': 'Cannot dispatch — operation is in state failed.'} | effets : 0

== TENIR-Gov 5.7.0 ==

P1a  entrées idéales, politique par défaut
      {'scoring_decision': 'FLAG', 'membrane_decision': 'PASS', 'composed_decision': 'FLAG', 'operation_state': 'reserved'} | 
      répartition sans acquittement : {'dispatched': True, 'operation_state': 'confirmed'} | effets : 1
P1b  entrées idéales, conditions déclarées ('ops supervision',)
      n/a sur 5.7.0 (CompositionPolicy.__init__() got an unexpected keyword argument 'flag_conditions')
P2   option_space absent
      {'scoring_decision': 'FLAG', 'membrane_decision': 'PASS', 'composed_decision': 'FLAG', 'operation_state': 'reserved'} | 
      répartition : {'dispatched': True, 'operation_state': 'confirmed'} | effets : 1
P3   délégation alice → bob retirée après l'admission
      admission : {'scoring_decision': 'FLAG', 'membrane_decision': 'PASS', 'composed_decision': 'FLAG', 'operation_state': 'reserved'} | 
      répartition après retrait : {'dispatched': True, 'operation_state': 'confirmed'} | effets : 1
P4   HOLD borné par τ_K = 60 s, résolution 120 s plus tard
      n/a sur 5.7.0 (CompositionPolicy.__init__() got an unexpected keyword argument 'flag_conditions')
```

## P5, matérialité d'irréversibilité

```
5.7.6
absente     : ('FLAG', 'FLAG', 'reserved', ['cooperative_control_score', 'trajectory_risk_score', 'manipulation_risk', 'drift'])
0.0 fournie : ('FLAG', 'FLAG', 'reserved', ['cooperative_control_score', 'trajectory_risk_score', 'manipulation_risk', 'drift'])
0.6 fournie : ('FLAG', 'FLAG', 'reserved', ['cooperative_control_score', 'trajectory_risk_score', 'manipulation_risk', 'drift'])
1.0 fournie : ('FLAG', 'FLAG', 'reserved', ['cooperative_control_score', 'trajectory_risk_score', 'manipulation_risk', 'drift'])
```

Sur 5.7.0, le script s'arrête à la construction de la politique (`flag_conditions` n'existe pas dans cette version) ; P5 ne porte que sur 5.7.6.

## Lecture

| Sonde | 5.7.0 | 5.7.6 |
| --- | --- | --- |
| P1a | FLAG admis sans condition, 1 effet | HOLD : un FLAG sans condition déclarée n'est pas admis. Le noyau de score rend FLAG, pas PASS, même sur ces entrées idéales |
| P1b | sans objet | Refus sans acquittement ; refus si l'acquittement ne couvre pas exactement les conditions ; 1 effet avec l'acquittement exact |
| P2 | Admis, 1 effet | HOLD |
| P3 | Répartie, 1 effet | Refus, `FAILED` / `CONFIRMED_NONEXECUTION`, 0 effet |
| P4 | sans objet | Résolution tardive refusée (`HARD_VETO`, `FAILED`), 0 effet |
| P5 | sans objet | Absente se comporte comme 0.0 et n'apparaît pas dans `declared_unmeasured`, qui liste quatre axes. De 0.0 à 1.0, la décision reste FLAG admis |

## Ce que ces sondes n'établissent pas

- Que la condition acquittée a été remplie : le runtime enregistre l'acquittement, il ne vérifie pas la condition (`CONDITION_ACKNOWLEDGED` n'est pas `CONDITION_VERIFIED`).
- Que l'absence de `irreversibility_materiality` produise une admission indue ou contourne un veto : sur ces entrées, la valeur ne change pas la décision. Le défaut établi est un défaut de représentation de l'absence.
- Un comportement multi-processus, persistant, ou face à un fournisseur réel.
- Une conformité REG : le harnais n'a pas été rejoué sur 5.7.6, et la cible épinglée reste 5.7.0.
- Une relecture indépendante : ces traces ont été produites et lues par la même session.

## Scripts

Empreintes SHA-256 : `probe_p1_p4_v1_invalide.py` 64833ec101380babfbe462845c05e9ffe63723a07dd59ee859574d0343dbdb3f ; `probe_p1_p4_v2.py` 4b35dc6d3e406e07bdef57f0c7665ddd0a738b650adc223535a3962cc29b7ba1 ; `probe_p5_materialite.py` cbf3db4587ca9ba6df45ada876103b682d5dab736b929882cd3093f9f4eb724d.

### Essai corrigé (`probe_p1_p4_v2.py`)

```python
"""Sondes P1 à P4 sur le gouverneur TENIR-Gov installé (5.7.0 ou 5.7.6).

P1  Entrées idéales : PASS émerge-t-il ? Sous la politique par défaut, un FLAG est-il admis ?
    Avec des conditions déclarées : la répartition exige-t-elle leur acquittement ?
P2  option_space absent : admission, ou HOLD ?
P3  Délégation retirée après l'admission, avant la répartition : refus ?
P4  HOLD borné par τ_K : une résolution arrivée après la borne est-elle refusée ?

Chaque sonde compte les appels au fournisseur simulé : un appel = un effet.
Usage : python -I probe_p1_p4.py
"""
from datetime import datetime, timezone

import tenir_governance
from tenir_governance.composition import DualKernelGovernor, ScoringKernelAdapter
from tenir_governance.composition import governor as gm
from tenir_governance.composition.policy import CompositionPolicy
from tenir_governance.membrane import MembraneState, TransitionMembrane
from tenir_governance.objects import Agent, Delegation, Passage, Resource
from tenir_governance.operations import MockProvider
from tenir_kernel.kernel import TenirKernel

V = tenir_governance.__version__
IDEAL = dict(pressure=0.0, velocity=0.0, capacity=1.0, authority=1.0,
             context_fit=1.0, evidence_quality=1.0, option_space=1.0)
GOOD = dict(pressure=0.2, velocity=0.2, capacity=0.9, authority=0.9,
            context_fit=1.0, evidence_quality=1.0, option_space=0.9)
COND = ("ops supervision",)
ACK = {"ops supervision": "ops rota, probe"}
PAYLOAD = {"action_type": "payment"}


def policy(**kw):
    try:
        return CompositionPolicy(**kw), None
    except TypeError as exc:
        return None, f"n/a sur {V} ({exc})"


def governor(pol, *, delegate=False):
    state = MembraneState()
    state.register_resource(Resource(resource_id="b", capacity=100.0))
    state.register_agent(Agent(agent_id="alice", authority_score=0.9,
                               trusted_delegates=frozenset({"bob"}) if delegate else frozenset()))
    if delegate:
        state.register_agent(Agent(agent_id="bob", authority_score=0.8))
    provider = MockProvider()
    gov = DualKernelGovernor(ScoringKernelAdapter(TenirKernel()), TransitionMembrane(state),
                             policy=pol, provider=provider)
    return gov, state, provider


def short(adj):
    keep = ("scoring_decision", "membrane_decision", "composed_decision", "operation_state")
    out = {k: adj.get(k) for k in keep if k in adj}
    why = str(adj.get("rationale") or adj.get("composition_rationale") or "")
    return f"{out} | {why[:110]}"


def dispatch(gov, key, **kw):
    try:
        out = gov.dispatch_and_execute(key, "b", 10.0, metadata=PAYLOAD, **kw)
    except TypeError as exc:
        return f"TypeError: {exc}"
    res = {k: out.get(k) for k in ("dispatched", "operation_state", "execution_record") if k in out}
    if out.get("reason") or out.get("error"):
        res["motif"] = str(out.get("reason") or out.get("error"))[:90]
    return res


def admit(gov, **inputs):
    p = Passage(agent_id="alice", action_type=inputs.pop("action_type", "payment"), amount=10.0,
                recipient_id=inputs.pop("recipient_id", None))
    adj = gov.adjudicate(p, resource_id="b", amount=10.0, payload=PAYLOAD, **inputs)
    return p, adj


print(f"== TENIR-Gov {V} ==")

print("\nP1a  entrées idéales, politique par défaut")
pol, _ = policy()
gov, _, prov = governor(pol)
p, adj = admit(gov, **IDEAL)
print("     ", short(adj))
if adj.get("operation_state") == "reserved":
    print("      répartition sans acquittement :", dispatch(gov, p.idempotency_key), "| effets :", len(prov.calls))

print("P1b  entrées idéales, conditions déclarées", COND)
pol, na = policy(flag_conditions=COND)
if na:
    print("     ", na)
else:
    gov, _, prov = governor(pol)
    p, adj = admit(gov, **IDEAL)
    print("     ", short(adj))
    print("      sans acquittement      :", dispatch(gov, p.idempotency_key), "| effets :", len(prov.calls))
    print("      acquittement inexact   :", dispatch(gov, p.idempotency_key, flag_conditions_met={"autre": "x"}),
          "| effets :", len(prov.calls))
    print("      acquittement exact     :", dispatch(gov, p.idempotency_key, flag_conditions_met=ACK),
          "| effets :", len(prov.calls))

print("P2   option_space absent")
pol, na = policy(flag_conditions=COND)
pol = pol or policy()[0]
gov, _, prov = governor(pol)
p, adj = admit(gov, **{**GOOD, "option_space": None})
print("     ", short(adj))
if adj.get("operation_state") == "reserved":
    kw = {} if na else {"flag_conditions_met": ACK}
    print("      répartition :", dispatch(gov, p.idempotency_key, **kw), "| effets :", len(prov.calls))

print("P3   délégation alice → bob retirée après l'admission")
gov, state, prov = governor(pol, delegate=True)
p, adj = admit(gov, **GOOD, action_type="delegation", recipient_id="bob",
               delegation=Delegation(delegating_agent_id="alice", delegatee_agent_id="bob"))
print("      admission :", short(adj))
if adj.get("operation_state") == "reserved":
    state.register_agent(Agent(agent_id="alice", authority_score=0.9, trusted_delegates=frozenset()))
    kw = {} if na else {"flag_conditions_met": ACK}
    print("      répartition après retrait :", dispatch(gov, p.idempotency_key, **kw), "| effets :", len(prov.calls))

print("P4   HOLD borné par τ_K = 60 s, résolution 120 s plus tard")
pol4, na4 = policy(flag_conditions=COND, hold_tau_k_seconds=60.0, hold_tau_k_source="probe SLA")
if na4:
    print("     ", na4)
else:
    gov, _, prov = governor(pol4)
    p, adj = admit(gov, **{**GOOD, "option_space": None})
    print("      entrée :", short(adj))
    real = gm._utc_now_epoch
    gm._utc_now_epoch = lambda: real() + 120.0
    gm._utc_now_iso = lambda: datetime.fromtimestamp(real() + 120.0, timezone.utc).isoformat()
    res = gov.resolve_hold(p.idempotency_key, passage=p, payload=PAYLOAD, resource_id="b", amount=10.0, **GOOD)
    print("      résolution tardive :", short(res))
    print("      répartition :", dispatch(gov, p.idempotency_key, flag_conditions_met=ACK), "| effets :", len(prov.calls))
```

### Différence avec le premier essai

```diff
@@ -59,10 +59,13 @@
 
 def dispatch(gov, key, **kw):
     try:
-        out = gov.dispatch_and_execute(key, "b", 10.0, **kw)
+        out = gov.dispatch_and_execute(key, "b", 10.0, metadata=PAYLOAD, **kw)
     except TypeError as exc:
         return f"TypeError: {exc}"
-    return {k: out.get(k) for k in ("dispatched", "operation_state", "execution_record", "error") if k in out}
+    res = {k: out.get(k) for k in ("dispatched", "operation_state", "execution_record") if k in out}
+    if out.get("reason") or out.get("error"):
+        res["motif"] = str(out.get("reason") or out.get("error"))[:90]
+    return res
 
 
 def admit(gov, **inputs):
```

### P5 (`probe_p5_materialite.py`)

```python
"""Sonde P5 : `irreversibility_materiality` absente, comparée à 0.0, 0.6 et 1.0 (TENIR-Gov installé).

Regarde la décision et la liste `declared_unmeasured`. Usage : python -I probe_p5_materialite.py
"""
import tenir_governance
from tenir_governance.composition import DualKernelGovernor, ScoringKernelAdapter
from tenir_governance.composition.policy import CompositionPolicy
from tenir_governance.membrane import MembraneState, TransitionMembrane
from tenir_governance.objects import Agent, Passage, Resource
from tenir_governance.operations import MockProvider
from tenir_kernel.kernel import TenirKernel

GOOD = dict(pressure=0.2, velocity=0.2, capacity=0.9, authority=0.9, context_fit=1.0,
            evidence_quality=1.0, option_space=0.9)


def run(**extra):
    st = MembraneState()
    st.register_resource(Resource(resource_id="b", capacity=100.0))
    st.register_agent(Agent(agent_id="alice", authority_score=0.9))
    g = DualKernelGovernor(ScoringKernelAdapter(TenirKernel()), TransitionMembrane(st),
                           policy=CompositionPolicy(flag_conditions=("ops",)), provider=MockProvider())
    a = g.adjudicate(Passage(agent_id="alice", action_type="payment", amount=10.0),
                     resource_id="b", amount=10.0, payload={"a": 1}, **GOOD, **extra)
    du = a.get("declared_unmeasured") or (a.get("scoring") or {}).get("declared_unmeasured")
    return a.get("scoring_decision"), a.get("composed_decision"), a.get("operation_state"), du


print(tenir_governance.__version__)
print("absente     :", run())
print("0.0 fournie :", run(irreversibility_materiality=0.0))
print("0.6 fournie :", run(irreversibility_materiality=0.6))
print("1.0 fournie :", run(irreversibility_materiality=1.0))
```
