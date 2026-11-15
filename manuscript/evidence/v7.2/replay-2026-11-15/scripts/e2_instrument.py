"""Instrumented replica of the BFS loop in e2_explore.py (same events, key, checks).
Adds: per-event exception census, reachability of FAILED / second admission / world effects.
Usage: python e2_instrument.py <path/to/e2_explore.py> <world> <depth>"""
import sys, copy, json, importlib.util, collections
from collections import deque

path, world, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
spec = importlib.util.spec_from_file_location("e2x", path)
X = importlib.util.module_from_spec(spec); spec.loader.exec_module(X)
from tenir_conformance.membrane import AttemptState, FakeClock, Membrane
from tenir_conformance.membrane.kernel_bridge import KernelBridge

events = X.build_events(world)
bridge = KernelBridge()
m0 = Membrane(bridge, clock=FakeClock(now_ms=X.T0), tau_k_ms=X.TAU,
              conflict_sensitive_properties={"exposure"},
              quarantine_release_authorizer=lambda p, l: True)
w0 = X.World()
seen = {hash(X.key(m0, w0)): 0}
q = deque([(m0, w0, ())])
transitions = 0
viol = collections.Counter(); first = {}; by_depth = collections.Counter({0: 1})
exc = collections.defaultdict(collections.Counter)     # event class -> exception repr -> n
applied = collections.Counter(); attempted = collections.Counter()
reach = collections.Counter()
max_world = 0
def cls(label):
    import re
    return re.sub(r"A[12]", "A*", label)
while q:
    m, w, trace = q.popleft()
    if len(trace) >= depth:
        continue
    for label, fn in events:
        if label.startswith("advance") and w.advances >= X.MAX_ADVANCES:
            continue
        m2 = copy.deepcopy(m, memo={id(bridge): bridge}); m2.events = []
        w2 = copy.deepcopy(w)
        before = X.snapshot(m2, w2)
        c = cls(label); attempted[c] += 1
        try:
            dispatch = fn(m2, w2); applied[c] += 1
        except Exception as e:
            exc[c][f"{type(e).__name__}: {str(e)[:60]}"] += 1
            dispatch = label.startswith(("process", "admit", "retry"))
        transitions += 1
        for inv, msg in X.check(label, dispatch, m2, w2, before):
            viol[inv] += 1
            first.setdefault(inv, (list(trace + (label,)), msg))
        k = hash(X.key(m2, w2))
        if k not in seen:
            seen[k] = len(trace) + 1; by_depth[len(trace) + 1] += 1
            q.append((m2, w2, trace + (label,)))
            states = [a.state for a in m2.attempts.values()]
            if AttemptState.FAILED in states: reach["states_with_a_FAILED_attempt"] += 1
            if AttemptState.RESOLVED in states: reach["states_with_a_RESOLVED_attempt"] += 1
            if len(m2.attempts) >= 2: reach["states_with_two_admitted_attempts"] += 1
            if len(m2.sink.effects) >= 1: reach["states_with_observed_effect"] += 1
            max_world = max(max_world, w2.total())
out = {
    "world": world, "depth": depth, "distinct_states": len(seen), "transitions_checked": transitions,
    "violations": dict(viol), "shortest_counterexamples": {k: {"trace": v[0], "msg": v[1]} for k, v in first.items()}, "new_states_by_depth": dict(by_depth), "max_world_effects_for_LEI": max_world, "reachability": dict(reach),
    "event_census": {c: {"attempted": attempted[c], "returned_normally": applied[c],
                          "raised": {k: v for k, v in exc[c].items()}} for c in attempted},
}
print(json.dumps(out, indent=1))
