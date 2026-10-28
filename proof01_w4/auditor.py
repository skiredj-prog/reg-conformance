"""W4 packaging from one captured byte set, with final ZIP replay.

POSIX descriptor-relative capture refuses links and special files. Verification
and serialization consume the same immutable bytes, never producer rereads.
This is not a filesystem-wide atomic snapshot or proof of native effects.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import stat
from types import MappingProxyType
import zipfile

from .verifier import parse_json, safe_name, verify_snapshot

MANIFEST = "proof-manifest-v1.json"
REPORT = "reports/audit-report.json"
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_MEMBERS = 1024


def canonical(value):
    # Stable report serialization; NOT a claim of RFC 8785/JCS compliance.
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _paths(manifest_bytes):
    manifest = parse_json(manifest_bytes)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("artifacts"), list):
        raise ValueError("Bad inventory")
    paths = [MANIFEST]
    for row in manifest["artifacts"]:
        if not isinstance(row, dict) or not safe_name(row.get("path")):
            raise ValueError("Untrusted artifact path")
        name = row["path"]
        if name in paths:
            raise ValueError("Duplicate/self-referential artifact")
        paths.append(name)
    if len(paths) + 1 > MAX_MEMBERS:
        raise ValueError("Too many archive members")
    return paths


def _read_at(root_fd, name):
    """Anchor every component to open directory descriptors; do not follow links."""
    if not safe_name(name):
        raise ValueError("Untrusted path")
    fd = os.dup(root_fd)
    try:
        parts = name.split("/")
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(leaf, "rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise ValueError("Non-regular evidence file")
            body = source.read(MAX_FILE_BYTES + 1)
            if len(body) > MAX_FILE_BYTES:
                raise ValueError("Oversized evidence file")
            return body
    finally:
        os.close(fd)


def _capture(bundle):
    if os.name != "posix" or os.open not in os.supports_dir_fd:
        raise ValueError("POSIX_CAPTURE_REQUIRED: use Linux; ZIP replay is portable")
    path = Path(bundle).absolute()
    if path.is_symlink():
        raise ValueError("Linked evidence root")
    root = path.resolve(strict=True)
    try:
        root_fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            content = {MANIFEST: _read_at(root_fd, MANIFEST)}
            total = len(content[MANIFEST])
            for name in _paths(content[MANIFEST])[1:]:
                body = _read_at(root_fd, name)
                total += len(body)
                if total > MAX_TOTAL_BYTES:
                    raise ValueError("Evidence exceeds byte limit")
                content[name] = body
        finally:
            os.close(root_fd)
    except OSError as exc:
        raise ValueError("Evidence capture failed: " + str(exc)) from exc
    return root, MappingProxyType(content)


def _report_snapshot(entries, claim=None):
    return {
        "report_version": "proof01-w4-audit/1",
        "inventory_result": verify_snapshot(entries, claim),
        "assurance_level": "documentary-inventory-only",
        "operational_assurance": "NOT_ESTABLISHED",
        "source_provenance": "UNVERIFIED",
        "independent_witness": "UNVERIFIED",
        "integration_lock": "NOT_EVALUATED",
        "limitations": [
            "No inspection of live producer side effects",
            "No signature or external independent witness evaluation",
            "No completeness guarantee for external effects",
            "A matching hash does not attest content truth",
        ],
    }


def report(bundle, claim=None):
    _, entries = _capture(bundle)
    return _report_snapshot(entries, claim)


def _require_inventory(summary):
    if summary["inventory_result"]["code"] != "SEMANTIC_PROOF_NOT_ESTABLISHED":
        raise ValueError("Bundle fails W4 inventory gate: " + summary["inventory_result"]["code"])


def _zip(entries, summary):
    data = {"evidence/" + name: body for name, body in entries.items()}
    data[REPORT] = canonical(summary)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, body in sorted(data.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, body)
    return buf.getvalue()


def verify_archive(raw, claim=None):
    """Recompute inventory and report from ZIP bytes; never extract or execute."""
    if len(raw) > MAX_TOTAL_BYTES + 1024 * 1024:
        raise ValueError("Oversized ZIP")
    entries = {}
    archived_report = None
    names = set()
    total = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if len(archive.infolist()) > MAX_MEMBERS:
            raise ValueError("Too many ZIP members")
        for info in archive.infolist():
            name = info.filename
            if (not safe_name(name) or info.orig_filename != name or name in names or info.is_dir()
                    or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG)):
                raise ValueError("Unsafe/duplicate ZIP member")
            names.add(name)
            total += info.file_size
            if info.file_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                raise ValueError("ZIP decompression limit")
            if info.flag_bits & 1:
                raise ValueError("Encrypted ZIP member")
            with archive.open(info) as stream:
                body = stream.read(MAX_FILE_BYTES + 1)
            if len(body) != info.file_size:
                raise ValueError("ZIP member length mismatch")
            if name == REPORT:
                archived_report = parse_json(body)
            elif name.startswith("evidence/"):
                entries[name[len("evidence/"):]] = body
            else:
                raise ValueError("Unexpected ZIP member")
    if MANIFEST not in entries or set(entries) != set(_paths(entries[MANIFEST])):
        raise ValueError("Archive inventory mismatch")
    computed = _report_snapshot(MappingProxyType(entries), claim)
    _require_inventory(computed)
    if archived_report != computed:
        raise ValueError("Archived report does not match archived evidence")
    return computed


def package(bundle, output, claim=None):
    root, entries = _capture(bundle)
    out = Path(output)
    if out.resolve().is_relative_to(root):
        raise ValueError("Output must be outside evidence bundle")
    summary = _report_snapshot(entries, claim)
    _require_inventory(summary)
    raw = _zip(entries, summary)
    verify_archive(raw, claim)
    # Exclusive creation. Reviewer controls the destination directory.
    try:
        with out.open("xb") as target:
            target.write(raw)
    except FileExistsError as exc:
        raise ValueError("Refuse to overwrite existing audit artifact") from exc
    with out.open("rb") as final:
        published = final.read(MAX_TOTAL_BYTES + 1024 * 1024 + 1)
    if published != raw:
        raise ValueError("Output changed after publication")
    verify_archive(published, claim)
    return {"archive": str(out), "sha256": hashlib.sha256(published).hexdigest(),
            "inventory": summary["inventory_result"]["code"],
            "archive_replay": "MATCHED_CAPTURED_BYTES",
            "operational_assurance": "NOT_ESTABLISHED"}


def main():
    p = argparse.ArgumentParser(description="W4 documentary snapshot / offline ZIP replay")
    p.add_argument("bundle", type=Path, nargs="?")
    p.add_argument("--output", type=Path)
    p.add_argument("--verify-archive", type=Path)
    p.add_argument("--claim")
    args = p.parse_args()
    try:
        if args.verify_archive:
            if args.bundle or args.output:
                p.error("--verify-archive cannot be combined with bundle/output")
            with args.verify_archive.open("rb") as source:
                raw = source.read(MAX_TOTAL_BYTES + 1024 * 1024 + 1)
            result = verify_archive(raw, args.claim)
        else:
            if not args.bundle or not args.output:
                p.error("bundle and --output are required")
            result = package(args.bundle, args.output, args.claim)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as error:
        p.exit(2, f"W4 fail-closed: {error}\n")


if __name__ == "__main__":
    main()
