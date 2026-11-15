"""Replay of the three-transition trace on a given checkout, with caller nonces and
attestations built by the repository's own test signer (tests/s7_helpers.py, lab key K1).
Ground truth is kept outside the membrane, exactly as in experiments/e1_e2/e2_explore.py:
a HIDDEN effect is counted when the attempt is admitted and its permit consumed while
apply_effect=False (the world applied it; the membrane did not observe it).
Usage: python e3_trace.py <repo_root>"""
import sys, json
from dataclasses import replace
root = sys.argv[1]
sys.path.insert(0, root + "/tests")
from tenir_conformance.membrane import AttemptState, FakeClock, Membrane
from tenir_conformance.membrane.kernel_bridge import KernelBridge
from s7_helpers import sign_attestation

OK = {"P": 0.5, "V": 0.5, "K": 1.0, "option_space": 1.0}
L = "L"

def run(name, *, hidden, step2):
    m = Membrane(KernelBridge(), clock=FakeClock(now_ms=1_000_000), tau_k_ms=5_000)
    world = {"A1": 0, "A2": 0}
    log = []
    # 1. admit_await(A1): effect produced in the world; observed or hidden
    n_sink = len(m.sink.effects)
    r1 = m.admit_and_await_qualification(lei=L, attempt_id="A1", payload=OK,
                                         apply_effect=not hidden, nonce="nA1")
    if hidden:
        if "A1" in m.attempts and m.permits["A1"].consumed: world["A1"] += 1
    elif len(m.sink.effects) > n_sink: world["A1"] += 1
    log.append(("1 admit_await(A1," + ("HIDDEN_effect" if hidden else "effect=True") + ")",
                m.attempts["A1"].state.value, f"effect_observed={m.attempts['A1'].effect_observed}"))
    # 2. declare_failed(A1, ...)
    if step2 == "signed_false":
        att = sign_attestation(attestation_id="ATT-1", attempt_id="A1", lei=L, nonce="nA1")
        r2 = m.declare_failed(attempt_id="A1", attestation=att)
    elif step2 == "unsigned_flag":           # what the committed explorer sends
        r2 = m.declare_failed(attempt_id="A1", evidence_qualified=True)
    elif step2 == "bad_signature":
        att = sign_attestation(attestation_id="ATT-1", attempt_id="A1", lei=L, nonce="nA1")
        att = replace(att, signature="00" * 64)
        r2 = m.declare_failed(attempt_id="A1", attestation=att)
    last = [e for e in m.events if e["event"].startswith(("T7", "NON_EXECUTION", "LEI_", "Attempt"))]
    log.append((f"2 declare_failed(A1,{step2})", m.attempts["A1"].state.value,
                (last[-1]["event"] if last else r2.disposition.value)))
    # 3. process(A2, ok) with a caller nonce
    n_sink = len(m.sink.effects)
    try:
        r3 = m.process_transaction(lei=L, attempt_id="A2", payload=OK, nonce="nA2")
        outcome = f"{r3.disposition.value}/{r3.client_state}"
    except Exception as e:
        outcome = f"raised {type(e).__name__}: {e}"
    if len(m.sink.effects) > n_sink: world["A2"] += 1
    log.append(("3 process(A2,ok,nonce)", m.attempts["A2"].state.value if "A2" in m.attempts else "not admitted", outcome))
    total = sum(world.values())
    print(f"\n[{name}]")
    for step, state, note in log: print(f"   {step:44} -> {state:22} {note}")
    print(f"   world effects for LEI = {total}   membrane-observed effects = {len(m.sink.effects)}"
          f"   =>  I1 {'VIOLATED' if total > 1 else 'holds'}")
    return total

res = {}
res["adversarial: hidden effect + signed false attestation (not O, not A)"] = run(
    "adversarial: hidden effect + false attestation signed by trusted key K1", hidden=True, step2="signed_false")
res["as committed explorer: hidden effect + unsigned qualified flag"] = run(
    "as the committed explorer sends it: hidden effect + evidence_qualified=True, no attestation", hidden=True, step2="unsigned_flag")
res["hidden effect + invalid signature"] = run(
    "hidden effect + attestation with invalid signature", hidden=True, step2="bad_signature")
res["false_attest: observed effect + signed false attestation (O, not A)"] = run(
    "false_attest: observed effect + false attestation signed by K1", hidden=False, step2="signed_false")
print("\nSUMMARY", json.dumps(res, indent=1))
