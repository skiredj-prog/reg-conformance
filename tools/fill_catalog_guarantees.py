#!/usr/bin/env python3
"""Remplit effective_guarantee_demonstrated des 42 configurations admissibles
à partir du registre de capacités. --check : détection de dérive pour la CI."""
import json, sys, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT_IN = ROOT / "catalog" / "valid-configurations-v1.json"
CAT_OUT = ROOT / "catalog" / "valid-configurations-v1.1.0.json"
CAP_DIR = ROOT / "capabilities" / "v1.0.0"

def load_caps():
    return {json.loads(p.read_text())["capability_id"]: json.loads(p.read_text())
            for p in CAP_DIR.glob("*.json")}

def match(cfg):
    h, c, d = cfg["HOST_SCOPE"], cfg["CONCURRENCY"], cfg["DEDUP_LAYER"]
    refs = []
    if h == "mono-process" and c == "thread-lock": refs.append("cap-i8-budget-inproc")
    if h == "mono-host" and c == "file-lock": refs.append("cap-i8-budget-crossproc")
    if c == "distributed-consensus": refs += ["cap-i8-budget-raft", "cap-deterministic-replication"]
    if c == "distributed-transaction": refs.append("cap-i8-budget-disttx")
    if d == "local-registry": refs.append("cap-dedup-local-registry")
    if d == "provider-idempotency-key": refs.append("cap-dedup-provider-key")
    if d == "distributed-consensus-registry": refs.append("cap-dedup-consensus-registry")
    return refs

def status(refs, caps):
    sts = [caps[r]["validation"]["effective_guarantee_demonstrated"] for r in refs]
    scopes = [caps[r].get("demonstration_scope") for r in refs]
    if any(s is False for s in sts): return "false", None
    if any(s is None for s in sts): return "null", None
    if any(sc == "loopback-test-only" for sc in scopes): return "partial", "loopback-test-only"
    return "true", "production-equivalent"

def compute(caps):
    src = json.loads(CAT_IN.read_text())
    entries = src["configurations"] if isinstance(src, dict) else src
    out, counts = [], {"true": 0, "partial": 0, "null": 0, "false": 0}
    for e in entries:
        e = dict(e)
        if e.get("admissible_structural"):
            refs = match(e["config"])
            st, scope = status(refs, caps)
            e["capability_refs"] = refs
            e["demonstration_scope"] = scope
            e["effective_guarantee_demonstrated"] = {"true": True, "false": False, "null": None, "partial": "partial"}[st]
            counts[st] += 1
        out.append(e)
    return out, counts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    caps = load_caps()
    entries, counts = compute(caps)

    if args.check:
        if not CAT_OUT.exists():
            print("MISSING: valid-configurations-v1.1.0.json")
            sys.exit(1)
        cur = json.loads(CAT_OUT.read_text())
        cur = cur["configurations"] if isinstance(cur, dict) else cur
        if cur != entries:
            print("DRIFT: catalogue v1.1.0 != registre de capacités")
            sys.exit(1)
        print("CATALOG IN SYNC")
        sys.exit(0)

    payload = {
        "catalog_version": "1.1.0",
        "rules_version": "2.0.0",
        "generated_from": "capabilities/v1.0.0 + valid-configurations-v1.json",
        "guarantee_summary": counts,
        "note": "true = démontré production-equivalent ; partial = démontré loopback-test-only ; "
                "null = non évalué ; false = réfuté. admissible_structural != garantie effective.",
        "configurations": entries,
    }
    CAT_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"catalog v1.1.0 written: {counts}")

if __name__ == "__main__":
    main()
