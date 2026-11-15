import json, sys
exp_dir, act_dir = sys.argv[1], sys.argv[2]
ok = True
for name in ("r6_adversarial", "r6_false_attest", "r8_honest", "r8_hidden_honest"):
    try:
        e = json.load(open(f"{exp_dir}/{name}.json")); a = json.load(open(f"{act_dir}/{name}.json"))
    except FileNotFoundError:
        print(f"{name:18} (not finished yet)"); ok = False; continue
    se, sa = e.pop("seconds", None), a.pop("seconds", None)
    same = e == a
    ok &= same
    print(f"{name:18} {'IDENTICAL (all fields except seconds)' if same else 'DIFFERS'}  "
          f"states={a['distinct_states']:,} transitions={a['transitions_checked']:,} "
          f"violations={a['violations']} shortest={ {k:v['trace'] for k,v in a['shortest_counterexamples'].items()} }  "
          f"[{sa}s here vs {se}s committed]")
    if not same:
        for k in e:
            if e[k] != a.get(k): print("    field", k, ": committed", e[k], "| re-run", a.get(k))
print("ALL MATCH" if ok else "INCOMPLETE OR MISMATCH")
