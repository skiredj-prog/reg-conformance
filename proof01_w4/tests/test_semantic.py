import base64,hashlib,json,tempfile,unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from proof01_w4.semantic import check,canon,hashobj

class TestW42(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.parent=Path(self.temp.name);self.root=self.parent/"bundle";self.root.mkdir()
        self.keys={x:Ed25519PrivateKey.generate() for x in ("runtime","provider","witness")}
        self.trust=self.parent/"trust.json"
        self.trust.write_text(json.dumps({"trust_version":"w4/1","keys":{k:{"role":k,"public_key_b64":base64.b64encode(v.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)).decode()} for k,v in self.keys.items()}}))
        self.scope={"system":"fixture","deployment":"single-host simulated","time_window":"fixed","fault_model":"crash-only"}
        self.make()
    def sign(self,x,role):
        return {**x,"signature":{"alg":"Ed25519","key_id":role,"value_b64":base64.b64encode(self.keys[role].sign(canon(x))).decode()}}
    def make(self,amount=4,kinds=None):
        self.events=[];prev=None
        for i,kind in enumerate(kinds or ("RESERVED","DISPATCHING","PROVIDER_EXECUTED","REPAIR","COMMITTED"),1):
            ev={"seq":i,"kind":kind,"previous_hash":prev,"attempt_id":"a1","resource_id":"r1","amount":amount,"capacity":5}
            if kind=="PROVIDER_EXECUTED":ev["effect_id"]="external-receipt-e1"
            envelope=self.sign(ev,"provider" if kind=="PROVIDER_EXECUTED" else "runtime")
            self.events.append(envelope);prev=hashobj(envelope)
        self.write()
    def write(self):
        cp=self.sign({"event_count":len(self.events),"last_event_hash":hashobj(self.events[-1]),"manifest_scope_digest":hashobj(self.scope)},"witness")
        artifacts=[]
        for name,content in (("events.json",self.events),("checkpoint.json",cp)):
            data=canon(content);(self.root/name).write_bytes(data)
            artifacts.append({"path":name,"sha256":hashlib.sha256(data).hexdigest()})
        m={"schema_version":"proof01-w4/1","scope":self.scope,"claims":["signed-trace-integrity","no-unobserved-effects"],"wire_contract":"proof01-signed-events/1","sequence_file":"events.json","checkpoint_file":"checkpoint.json","artifacts":artifacts}
        (self.root/"proof-manifest-v1.json").write_text(json.dumps(m))
    def test_bounded_verified(self):
        x=check(self.root,self.trust)
        self.assertEqual((x["outcome"],x["code"]),("VERIFIED","SIGNED_TRACE_VALID"))
        self.assertEqual(x["balances"]["r1"]["committed"],4)
    def test_global_absence_never_verified(self):
        self.assertEqual(check(self.root,self.trust,"no-unobserved-effects")["outcome"],"INDETERMINATE")
    def test_budget_violation(self):
        self.make(amount=7);self.assertEqual(check(self.root,self.trust)["code"],"I8_VIOLATION")
    def test_signature_tampering(self):
        self.events[2]["signature"]["value_b64"]=base64.b64encode(b"0"*64).decode()
        self.write();self.assertEqual(check(self.root,self.trust)["code"],"INVALID_EVIDENCE")
    def test_wrong_signer_role(self):
        old={k:v for k,v in self.events[2].items() if k!="signature"}
        self.events[2]=self.sign(old,"runtime")
        self.write();self.assertEqual(check(self.root,self.trust)["code"],"INVALID_EVIDENCE")
    def test_bad_transition(self):
        self.make(kinds=("RESERVED","COMMITTED"))
        self.assertEqual(check(self.root,self.trust)["code"],"INVALID_TRANSITION")
    def test_undeclared_claim(self):
        self.assertEqual(check(self.root,self.trust,"production-certification")["outcome"],"OUT_OF_SCOPE")
    def test_trust_store_inside_evidence(self):
        inside=self.root/"trust.json";inside.write_bytes(self.trust.read_bytes())
        self.assertEqual(check(self.root,inside)["code"],"TRUST_INSIDE_BUNDLE")
if __name__=="__main__":unittest.main()
