import json, sys
def load(p):
    t = open(p).read().replace('\r', '')
    j, end = json.JSONDecoder().raw_decode(t)
    return j, t[end:].strip()
a, ta = load(sys.argv[1]); b, tb = load(sys.argv[2])
keys = ["duplicate_effects","exactly_one_effect","zero_effects","client_confirmed_success",
        "correct_no_effect_sequences","correct_single_effect_sequences",
        "blocked_retry_attempts","sequences_with_at_least_one_block"]
print(f"{'system':46} {'metric':34} {'committed':>9} {'re-run':>7}")
for x, y in zip(a, b):
    for k in keys:
        flag = "" if x.get(k) == y.get(k) else "   <-- differs"
        print(f"{x['system'][:46]:46} {k:34} {str(x.get(k)):>9} {str(y.get(k)):>7}{flag}")
print("tail committed:", ta[:200]); print("tail re-run   :", tb[:200])
