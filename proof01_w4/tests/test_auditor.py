import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from proof01_w4.auditor import package

class AuditorKitTest(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.base=Path(self.t.name);self.bundle=self.base/"bundle";self.bundle.mkdir()
        self.evidence=b"no-real-provider-effect"
        (self.bundle/"receipt.bin").write_bytes(self.evidence)
        self.manifest={"schema_version":"proof01-w4/1","scope":{"system":"synthetic","deployment":"local","time_window":"fixed","fault_model":"none"},"claims":["receipt-integrity"],"artifacts":[{"path":"receipt.bin","sha256":hashlib.sha256(self.evidence).hexdigest()}]}
        self.save()
    def save(self):
        (self.bundle/"proof-manifest-v1.json").write_text(json.dumps(self.manifest))
    def test_archives_identical_and_non_certifying(self):
        a=self.base/"a.zip";b=self.base/"b.zip"
        x=package(self.bundle,a);y=package(self.bundle,b)
        self.assertEqual(x["sha256"],y["sha256"])
        with zipfile.ZipFile(a) as z:
            self.assertEqual(z.read("evidence/receipt.bin"),self.evidence)
            result=json.loads(z.read("reports/audit-report.json"))
            self.assertEqual(result["operational_assurance"],"NOT_ESTABLISHED")
            self.assertEqual(result["inventory_result"]["outcome"],"INDETERMINATE")
    def test_tampered_data_rejected(self):
        (self.bundle/"receipt.bin").write_bytes(b"tampered")
        with self.assertRaises(ValueError):package(self.bundle,self.base/"a.zip")
    def test_out_of_scope_rejected(self):
        with self.assertRaises(ValueError):package(self.bundle,self.base/"a.zip","no-second-effect")
    def test_do_not_overwrite(self):
        path=self.base/"a.zip";package(self.bundle,path)
        with self.assertRaises(ValueError):package(self.bundle,path)
    def test_symlink_rejected(self):
        (self.bundle/"linked.bin").symlink_to(self.bundle/"receipt.bin")
        self.manifest["artifacts"][0]["path"]="linked.bin";self.save()
        with self.assertRaises(ValueError):package(self.bundle,self.base/"a.zip")
    def test_output_not_in_bundle(self):
        with self.assertRaises(ValueError):package(self.bundle,self.bundle/"audit.zip")
if __name__=="__main__":unittest.main()
