"""Fail-closed, independent manifest/evidence checker.

No import or call into TENIR-Gov. VERIFIED means *only* that the
declared bytes and trust-anchor constraints passed the implemented checks.
It must never be interpreted as operational control-effectiveness assurance.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")
OUTCOMES = ("VERIFIED", "REFUTED", "INDETERMINATE", "OUT_OF_SCOPE")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _reject(code: str, detail: str, outcome: str = "REFUTED") -> dict:
    return {"outcome": outcome, "code": code, "detail": detail}


def verify(bundle_dir: Path, requested_claim: str | None = None) -> dict:
    """Read an untrusted bundle without following symlinks or external paths."""
    root = Path(bundle_dir).resolve(strict=True)
    manifest_path = root / "proof-manifest-v1.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        return _reject("MANIFEST_MISSING", "Manifest absent or symlink", "INDETERMINATE")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return _reject("MANIFEST_INVALID", "Manifest cannot be parsed")
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "proof01-w4/1":
        return _reject("SCHEMA", "Unknown manifest version")
    scope = manifest.get("scope")
    if not isinstance(scope, dict) or not all(
        isinstance(scope.get(k), str) and scope[k].strip()
        for k in ("system", "deployment", "time_window", "fault_model")
    ):
        return _reject("SCOPE", "Explicit system, deployment, time window and fault model required")
    claims = manifest.get("claims")
    if not isinstance(claims, list) or not claims or any(not isinstance(c, str) or not c for c in claims):
        return _reject("CLAIMS", "Nonempty claim list required")
    if len(set(claims)) != len(claims):
        return _reject("CLAIMS_DUPLICATE", "Duplicate claims")
    if requested_claim is not None and requested_claim not in claims:
        return _reject("SCOPE_MISMATCH", "Claim not declared", "OUT_OF_SCOPE")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return _reject("ARTIFACTS", "Evidence inventory required", "INDETERMINATE")
    seen = set()
    checked = []
    for item in artifacts:
        if not isinstance(item, dict):
            return _reject("ENTRY", "Invalid artifact entry")
        path, digest = item.get("path"), item.get("sha256")
        if not isinstance(path, str) or not path or not isinstance(digest, str) or not SHA256.fullmatch(digest):
            return _reject("ENTRY", "Artifact path or digest malformed")
        rel = Path(path)
        if rel.is_absolute() or ".." in rel.parts or "\\" in path or path.startswith("/"):
            return _reject("PATH_ESCAPE", "Absolute or escaping path forbidden")
        if path in seen or path == "proof-manifest-v1.json":
            return _reject("DUPLICATE", "Duplicate or self-referential artifact")
        seen.add(path)
        candidate = root / rel
        if candidate.is_symlink() or not candidate.is_file() or not candidate.resolve().is_relative_to(root):
            return _reject("EVIDENCE_MISSING", f"Missing, linked or escaping evidence: {path}", "INDETERMINATE")
        if sha256(candidate.read_bytes()) != digest:
            return _reject("HASH_MISMATCH", f"Evidence changed: {path}")
        checked.append(path)
    # Integrity is not evidence of truth. An authenticated, trusted external
    # witness + event completeness + independent replay is NOT implemented.
    return {
        "outcome": "INDETERMINATE",
        "code": "SEMANTIC_PROOF_NOT_ESTABLISHED",
        "detail": "Artifact bytes match; external effects, authenticity, completeness and operational claims not independently established",
        "integrity_verified": checked,
        "declared_claims": claims,
        "scope": scope,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Offline W4 verifier: never certifies execution")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--claim")
    args = parser.parse_args()
    try:
        result = verify(args.bundle, args.claim)
    except (OSError, ValueError) as exc:
        result = _reject("IO_ERROR", type(exc).__name__, "INDETERMINATE")
    print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False))
    return 0 if result["outcome"] == "VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
