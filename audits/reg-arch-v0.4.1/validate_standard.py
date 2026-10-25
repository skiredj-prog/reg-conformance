"""Independent candidate schema and RFC 8785 regression gate (not deployment conformance)."""
import hashlib
import json
from pathlib import Path

import jcs
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
schema = json.loads((ROOT / "trace-schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(schema)
validator = Draft202012Validator(schema)

def example(outcome="REFUSED"):
    values = {}
    for name in schema["required"]:
        prop = schema["properties"][name]
        if "const" in prop:
            values[name] = prop["const"]
        elif name == "outcome":
            values[name] = outcome
        elif name == "reason_code":
            values[name] = "REQUEST_CONTEXT_INCOMPLETE"
        elif name == "causation_event_ids":
            values[name] = []
        elif name == "logical_order":
            values[name] = 1
        elif name == "gap_object_id":
            values[name] = None
        elif name in ("source_refusal_event_id", "source_object_id", "source_object_version",
                      "target_object_id", "target_object_version", "refusal_category",
                      "reg_arch_version", "active_manifest_id", "active_manifest_version",
                      "active_manifest_digest", "requester_ref", "controller_principal_ref",
                      "capability_assertion_ref", "trust_binding_ref", "capability_scope_version",
                      "conflicting_prior_event_id", "requested_reason"):
            values[name] = None
        else:
            values[name] = "example"
    return values

refused = example()
validator.validate(refused)
created = example("CREATED")
assert list(validator.iter_errors(created)), "CREATED without required context must fail"
for mutation in (dict(refused, unexpected="x"), dict(refused, outcome="UNRECOGNIZED"),
                 dict(refused, event_type="OTHER"), dict(refused, event_id="")):
    assert list(validator.iter_errors(mutation)), "invalid trace accepted"

# RFC 8785 Appendix B / ECMAScript number serialization sample.
numbers = {"numbers": [333333333.3333333, 1e30, 4.5, 0.002, 1e-27]}
assert jcs.canonicalize(numbers) == b'{"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27]}'
# Unicode property sorting is by UTF-16 code units, not Python codepoint order.
unicode_keys = {"\ue000": 1, "\U00010000": 2}
assert jcs.canonicalize(unicode_keys) == ('{"' + "\U00010000" + '":2,"' + "\ue000" + '":1}').encode("utf-8")
# Escaping and non-ASCII payloads must remain stable across insertion order.
a = {"é": "雪", "a": "line\\nbreak", "z": -0.0}
b = dict(reversed(list(a.items())))
assert jcs.canonicalize(a) == jcs.canonicalize(b)
assert hashlib.sha256(jcs.canonicalize(a)).digest() == hashlib.sha256(jcs.canonicalize(b)).digest()
print("REG-ARCH v0.4.1: standard JSON Schema + JCS edge-vector checks PASS")
