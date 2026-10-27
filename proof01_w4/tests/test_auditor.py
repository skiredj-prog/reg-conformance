import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from proof01_w4.auditor import make_kit,auditor_report
from test_semantic import TestW42

class TestAuditorKit(unittest.TestCase):
    def setUp(self):
        self.fx=TestW42("test_bounded_verified");self.fx.setUp();self.addCleanup(self.fx.doCleanups)
        self.out=self.fx.parent/"audit.zip"
        (self.fx.root/"reports").mkdir()
        (self.fx.root/"convergence.json").write_text(json.dumps({"source_lock":"PINNED","integration_sha":None,"deployment_manifest_sha256":None,"topology_id":None}))
        (self.fx.root/"reports/test-results.json").write_text('{"test_pass":true,"security_verdict":"UNKNOWN"}')
        (self.fx.root/"reports/proof-obligations.json").write_text('{"E2E":"OPEN"}')
    def test_deterministic_zip(self):
        a=make_kit(self.fx.root,self.out,self.fx.trust)
        original=self.out.read_bytes()
        b=make_kit(self.fx.root,self.out,self.fx.trust)
        self.assertEqual(original,self.out.read_bytes())
        self.assertEqual(a["zip_sha256"],b["zip_sha256"])
        self.assertEqual(a["report"]["production_gate"],"HOLD")
    def test_checksum_inventory(self):
        make_kit(self.fx.root,self.out)
        with zipfile.ZipFile(self.out) as z:
            lines=z.read("SHA256SUMS.txt").decode().splitlines()
            for line in lines:
                d,name=line.split("  ",1)
                self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),d)
            self.assertEqual(json.loads(z.read("auditor/report.json"))["integration_lock"],"UNVERIFIED")
    def test_missing_references_remain_hold(self):
        (self.fx.root/"convergence.json").unlink()
        a=auditor_report(self.fx.root)
        self.assertIn("INTEGRATION_LOCK_UNESTABLISHED",[p["code"] for p in a["problems"]])
    def test_symlink_rejected(self):
        (self.fx.root/"extra").symlink_to(self.fx.trust)
        with self.assertRaises(ValueError):make_kit(self.fx.root,self.out)
    def test_output_inside_bundle_rejected(self):
        with self.assertRaises(ValueError):make_kit(self.fx.root,self.fx.root/"audit.zip")
    def test_reserved_names_rejected(self):
        (self.fx.root/"auditor").mkdir()
        (self.fx.root/"auditor/report.json").write_text("{}")
        with self.assertRaises(ValueError):make_kit(self.fx.root,self.out)
    def test_forged_positive_cannot_promote(self):
        (self.fx.root/"convergence.json").write_text(json.dumps({
            "integration_sha":"a"*40,"deployment_manifest_sha256":"b"*64,"topology_id":"lab"
        }))
        a=make_kit(self.fx.root,self.out,self.fx.trust)
        self.assertEqual(a["report"]["production_gate"],"HOLD")
        self.assertEqual(a["report"]["integration_lock"],"UNVERIFIED")
if __name__=="__main__":unittest.main()
