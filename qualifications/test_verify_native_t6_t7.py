"""Adversarial checks for scoped native evidence gate (stdlib only)."""
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from qualifications.verify_native_t6_t7 import VECTOR_TESTS, classify

class TestEvidenceGate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/"junit.xml"
        self.root = ET.Element("testsuite")
        for names in VECTOR_TESTS.values():
            for name in names:
                ET.SubElement(self.root, "testcase", name=name)
    def verify(self):
        ET.ElementTree(self.root).write(self.path, encoding="utf-8")
        return classify(self.path)
    def test_exact_nine_are_scoped_not_normative(self):
        r=self.verify()
        self.assertEqual(r["tests_passed"],9)
        self.assertFalse(r["normative_equivalence"])
        self.assertFalse(r["native_conformant"])
        self.assertEqual(r["CT-R4-013"]["status"],"IMPLEMENTATION_GAP")
    def test_missing_case_fails_closed(self):
        self.root.remove(list(self.root)[0])
        with self.assertRaises(ValueError):
            self.verify()
    def test_extra_case_fails_closed(self):
        ET.SubElement(self.root, "testcase", name="unreviewed_test")
        with self.assertRaises(ValueError):
            self.verify()
    def test_skip_fails_closed(self):
        ET.SubElement(list(self.root)[0], "skipped")
        with self.assertRaises(ValueError):
            self.verify()
    def test_failure_fails_closed(self):
        ET.SubElement(list(self.root)[0], "failure")
        with self.assertRaises(ValueError):
            self.verify()
    def test_duplicate_fails_closed(self):
        ET.SubElement(self.root,"testcase",name=list(self.root)[0].get("name"))
        with self.assertRaises(ValueError):
            self.verify()

if __name__ == "__main__":
    unittest.main()
