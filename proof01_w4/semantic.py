"""Independent PROOF-01 W4.2: authenticated synthetic-trace verification, not runtime assurance."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from .verifier import verify

def canon(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
def hashobj(x):
    return hashlib.sha256(canon(x)).hexdigest()
def verdict(outcome,code,**data):
    return dict(outcome=outcome,code=code,**data)
def read(path):
    if path.is_symlink() or not path.is_file(): raise ValueError("Missing or symlink")
    return json.loads(path.read_text(encoding="utf8"))
def trusted(path):
    t=read(path)
    if t.get("trust_version")!="w4/1" or not isinstance(t.get("keys"),dict) or not t["keys"]: raise ValueError("Missing external trust anchors")
    result={}
    for kid, entry in t["keys"].items():
        role=entry["role"]
        if role not in ("runtime","provider","witness"): raise ValueError("Bad signer role")
        key=base64.b64decode(entry["public_key_b64"],validate=True)
        if len(key)!=32: raise ValueError("Bad public key")
        result[kid]=(role,Ed25519PublicKey.from_public_bytes(key))
    return result
def auth(envelope, trust, role):
    sig=envelope["signature"]
    kid=sig["key_id"]
    if kid not in trust or trust[kid][0]!=role or sig["alg"]!="Ed25519": raise ValueError("Untrusted role/key")
    payload={k:v for k,v in envelope.items() if k!="signature"}
    trust[kid][1].verify(base64.b64decode(sig["value_b64"],validate=True),canon(payload))
    return payload

def check(bundle,trust_store,claim="signed-trace-integrity"):
    try:
        root=Path(bundle).resolve(strict=True)
        if Path(trust_store).resolve(strict=True).is_relative_to(root):
            return verdict("REFUTED","TRUST_INSIDE_BUNDLE")
        inv=verify(root,claim)
        if inv.get("code")!="SEMANTIC_PROOF_NOT_ESTABLISHED": return inv
        m=read(root/"proof-manifest-v1.json")
        if m.get("wire_contract")!="proof01-signed-events/1":
            return verdict("INDETERMINATE","WIRE_CONTRACT_MISSING")
        files={a["path"] for a in m["artifacts"]}
        events_file=m.get("sequence_file","events.json")
        checkpoint_file=m.get("checkpoint_file","checkpoint.json")
        if not {events_file,checkpoint_file}.issubset(files):return verdict("INDETERMINATE","ARTIFACTS_UNDECLARED")
        events=read(root/events_file); cp=read(root/checkpoint_file)
        if not isinstance(events,list) or not events:return verdict("INDETERMINATE","EMPTY_TRACE")
        trust=trusted(Path(trust_store))
        previous=None; state={}; bindings={}; balances={}; effects=set()
        allowed={"RESERVED":(None,),"DISPATCHING":("RESERVED",),"PROVIDER_EXECUTED":("DISPATCHING",),"REPAIR":("PROVIDER_EXECUTED",),"COMMITTED":("PROVIDER_EXECUTED","REPAIR")}
        for index,envelope in enumerate(events,1):
            kind=envelope.get("kind")
            ev=auth(envelope,trust,"provider" if kind=="PROVIDER_EXECUTED" else "runtime")
            if ev.get("seq")!=index or ev.get("previous_hash")!=previous:return verdict("REFUTED","CHAIN_BROKEN",index=index)
            previous=hashobj(envelope)
            aid=ev["attempt_id"]; rid=ev["resource_id"]; amount=ev["amount"]; cap=ev["capacity"]
            if not isinstance(aid,str) or not aid or not isinstance(rid,str) or not rid or type(amount)!=int or amount<=0 or type(cap)!=int or cap<0:
                return verdict("REFUTED","INVALID_FIELDS")
            old=state.get(aid)
            if kind not in allowed or old not in allowed[kind]:return verdict("REFUTED","INVALID_TRANSITION",previous=old,next=kind)
            bound=(rid,amount,cap)
            if old is not None and bindings[aid]!=bound:return verdict("REFUTED","BINDING_DRIFT")
            bindings.setdefault(aid,bound)
            b=balances.setdefault(rid,dict(capacity=cap,reserved=0,committed=0))
            if b["capacity"]!=cap:return verdict("REFUTED","CAPACITY_DRIFT")
            if kind=="RESERVED":b["reserved"]+=amount
            if kind=="COMMITTED":b["reserved"]-=amount;b["committed"]+=amount
            if b["reserved"]<0 or b["committed"]<0 or b["reserved"]+b["committed"]>cap:
                return verdict("REFUTED","I8_VIOLATION",resource_id=rid,index=index)
            if kind=="PROVIDER_EXECUTED":
                eid=ev.get("effect_id")
                if not isinstance(eid,str) or not eid or eid in effects:return verdict("REFUTED","DUPLICATE_EFFECT_ID")
                effects.add(eid)
            state[aid]=kind
        signed_cp=auth(cp,trust,"witness")
        if signed_cp.get("event_count")!=len(events) or signed_cp.get("last_event_hash")!=previous or signed_cp.get("manifest_scope_digest")!=hashobj(m["scope"]):
            return verdict("REFUTED","CHECKPOINT_MISMATCH")
        if claim!="signed-trace-integrity":
            return verdict("INDETERMINATE","EXTERNAL_COMPLETENESS_UNKNOWN")
        return verdict("VERIFIED","SIGNED_TRACE_VALID",events=len(events),final_states=state,balances=balances,limits="synthetic declared trace only; NOT external effect completeness or production behavior")
    except (ValueError,KeyError,TypeError,OSError,AttributeError) as ex:
        return verdict("REFUTED","INVALID_EVIDENCE",detail=type(ex).__name__+": "+str(ex))

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("bundle",type=Path);p.add_argument("--trust-store",required=True,type=Path)
    p.add_argument("--claim",default="signed-trace-integrity")
    a=p.parse_args()
    print(json.dumps(check(a.bundle,a.trust_store,a.claim),indent=2,sort_keys=True))
if __name__=="__main__":main()
