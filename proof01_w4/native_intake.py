"""Opaque native-evidence intake: captured bytes, inventory and subject drift.

Does not infer native field mappings, re-sign events or replace native readers.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from .auditor import _capture, MAX_FILE_BYTES
from .verifier import parse_json, verify_snapshot

REQUIRED = ("provider-bundle.json", "local-state.json", "witness-events.json")
SUBJECT = ("integration_sha", "deployment_manifest_sha256", "topology_id")


def result(outcome, code, **details):
    return {"adapter_profile": "proof01-native-intake/0.1",
            "outcome": outcome, "code": code,
            "native_semantics": "NOT_EVALUATED", "integration_lock": "HOLD",
            "production": "HOLD", **details}


def _valid_subject(value):
    return (isinstance(value, dict)
            and isinstance(value.get("integration_sha"), str)
            and re.fullmatch("[0-9a-f]{40}", value["integration_sha"]) is not None
            and isinstance(value.get("deployment_manifest_sha256"), str)
            and re.fullmatch("[0-9a-f]{64}", value["deployment_manifest_sha256"]) is not None
            and isinstance(value.get("topology_id"), str) and bool(value["topology_id"].strip()))


def inspect_native_snapshot(entries, pins_bytes=None, expected_subject=None, claim="lab-repair-consistency"):
    inventory = verify_snapshot(entries, claim)
    if inventory["code"] != "SEMANTIC_PROOF_NOT_ESTABLISHED":
        return result(inventory["outcome"], inventory["code"], inventory=inventory)
    checked = set(inventory["integrity_verified"])
    missing = [name for name in REQUIRED if name not in entries]
    if missing:
        return result("INDETERMINATE", "NATIVE_ARTIFACTS_MISSING", missing=missing)
    if any(name not in checked for name in REQUIRED):
        return result("REFUTED", "NATIVE_ARTIFACT_NOT_INVENTORIED")
    try:
        for name in REQUIRED:
            # Shape only. The legacy kit's exact envelope/codec is deliberately
            # not reconstructed or guessed from README descriptions.
            if not isinstance(parse_json(entries[name]), (dict, list)):
                raise ValueError("Expected native JSON object/array")
    except (ValueError, UnicodeError):
        return result("REFUTED", "NATIVE_JSON_INVALID")
    subject_check = "NOT_EVALUATED"
    if expected_subject is not None:
        if not _valid_subject(expected_subject):
            return result("INDETERMINATE", "EXPECTED_SUBJECT_INVALID")
        needed = ("convergence.json", "deployment-manifest.json")
        if any(name not in checked for name in needed):
            return result("INDETERMINATE", "SUBJECT_EVIDENCE_MISSING")
        try:
            subject = parse_json(entries["convergence.json"])
        except (ValueError, UnicodeError):
            return result("REFUTED", "SUBJECT_JSON_INVALID")
        if not _valid_subject(subject):
            return result("REFUTED", "SUBJECT_FIELDS_INVALID")
        mismatches = [name for name in SUBJECT if subject[name] != expected_subject[name]]
        actual = hashlib.sha256(entries["deployment-manifest.json"]).hexdigest()
        if actual != subject["deployment_manifest_sha256"]:
            mismatches.append("deployment_manifest_bytes")
        if mismatches:
            return result("INDETERMINATE", "SUBJECT_BINDING_STALE",
                          evidence_status="STALE", mismatches=mismatches,
                          affected_guarantees="NOT_COMPUTED")
        subject_check = "MATCHES_CALLER_REFERENCE_ONLY"
    if pins_bytes is None:
        return result("INDETERMINATE", "EXTERNAL_PINS_REQUIRED", subject_check=subject_check)
    try:
        pins = parse_json(pins_bytes)
        if not isinstance(pins, dict) or not pins:
            raise ValueError("Empty/non-object pins")
    except (ValueError, UnicodeError):
        return result("INDETERMINATE", "EXTERNAL_PINS_INVALID")
    return result(
        "INDETERMINATE", "NATIVE_READERS_REQUIRED",
        documentary_intake="READY_FOR_NATIVE_READERS", subject_check=subject_check,
        native_artifact_sha256={name: hashlib.sha256(entries[name]).hexdigest() for name in REQUIRED},
        pins_sha256=hashlib.sha256(pins_bytes).hexdigest(),
        pins_status="PRESENT_NOT_AUTHENTICATED",
        remaining_checks=["native envelope/version and signed-message codec", "receipt and checkpoint signatures",
                          "Merkle inclusion", "witness chain and pin validation",
                          "RC-01/I8 replay", "independent differential agreement"])


def _external_bytes(path, root):
    path = Path(path)
    if path.resolve(strict=True).is_relative_to(root):
        raise ValueError("External reference must be outside evidence bundle")
    with path.open("rb") as source:
        body = source.read(MAX_FILE_BYTES + 1)
    if len(body) > MAX_FILE_BYTES:
        raise ValueError("Oversized external reference")
    return body


def inspect_native_bundle(bundle, pins=None, expected_subject=None, claim="lab-repair-consistency"):
    try:
        root, entries = _capture(bundle)
        pins_bytes = _external_bytes(pins, root) if pins is not None else None
        subject = parse_json(_external_bytes(expected_subject, root)) if expected_subject is not None else None
        return inspect_native_snapshot(entries, pins_bytes, subject, claim)
    except (OSError, ValueError, UnicodeError) as exc:
        return result("INDETERMINATE", "CAPTURE_OR_REFERENCE_INVALID", detail=str(exc))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("bundle", type=Path)
    p.add_argument("--pins", type=Path)
    p.add_argument("--expected-subject", type=Path)
    p.add_argument("--claim", default="lab-repair-consistency")
    args = p.parse_args()
    report = inspect_native_bundle(args.bundle, args.pins, args.expected_subject, args.claim)
    print(json.dumps(report, indent=2))
    # Intake success is intentionally not native semantic verification.
    return 1 if report["outcome"] == "REFUTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
