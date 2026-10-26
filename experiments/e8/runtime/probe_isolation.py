"""Seven bounded container deployment probes; NOT R-01/Q6 conformance.

Run inside unprivileged runtime. Emits JSONL for evidence intake and exits 0
only if all seven probes pass. The witness signing/private engine keys are not
mounted into the runtime container.
"""
import errno
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

RUNTIME_VOLUME = Path("/var/lib/tenir/runtime")
WITNESS_VOLUME = Path("/var/lib/tenir/witness")
WITNESS_VOLUME_NAME = "tenir_witness_strict_volume"
PIN = Path(os.getenv("WITNESS_PINNED_PUBKEY",
                     "/etc/tenir-witness/witness_pub.pem"))
WITNESS_URL = os.getenv("WITNESS_URL", "http://witness:8443")
results = []


def record(case_id, result, **details):
    entry = {"id": case_id, "status": "PASS" if result else "FAIL",
             "details": details, "assurance": "CONTAINER_ONLY"}
    results.append(entry)
    print(json.dumps(entry, sort_keys=True), flush=True)


def writable_runtime():
    try:
        if os.geteuid() != 1000 or os.getegid() != 1000:
            raise ValueError("effective UID/GID mismatch")
        fd, p = tempfile.mkstemp(dir=RUNTIME_VOLUME, prefix=".e8probe-")
        try:
            os.write(fd, b"runtime-only")
            os.fsync(fd)
        finally:
            os.close(fd)
            os.unlink(p)
        record("FS-POS-1", True, uid=os.geteuid(), gid=os.getegid())
    except Exception as exc:
        record("FS-POS-1", False, error=repr(exc))


def missing_witness_path():
    try:
        os.stat(WITNESS_VOLUME)
        record("FS-NEG-1", False, reason="witness path exists")
    except FileNotFoundError:
        record("FS-NEG-1", True, reason="ENOENT")
    except OSError as exc:
        record("FS-NEG-1", False, errno=exc.errno)


def no_cross_mount():
    try:
        text = Path("/proc/self/mountinfo").read_text()
        # Docker volume name is not always present in mountinfo: supplement
        # both target-path and declared-name checks with docker inspect.
        mounted = any(
            " /var/lib/tenir/witness " in line
            for line in text.splitlines()
        )
        record("FS-NEG-2", not mounted and WITNESS_VOLUME_NAME not in text,
               target_mount_present=mounted,
               volume_name_present=WITNESS_VOLUME_NAME in text)
    except OSError as exc:
        record("FS-NEG-2", False, error=repr(exc))


def blocked_witness_write():
    probe = WITNESS_VOLUME / ".e8-unauthorized-write"
    try:
        with open(probe, "xb") as f:
            f.write(b"UNAUTHORIZED")
        probe.unlink(missing_ok=True)
        record("FS-NEG-3", False, reason="unauthorized write unexpectedly worked")
    except OSError as exc:
        allowed = exc.errno in (errno.ENOENT, errno.EACCES, errno.EPERM,
                                 errno.EROFS)
        record("FS-NEG-3", allowed, errno=exc.errno,
               note="ENOENT is absent path, not a kernel permission denial")
    except Exception as exc:
        record("FS-NEG-3", False, error=repr(exc))


def health_reachable():
    try:
        with urllib.request.urlopen(WITNESS_URL + "/health", timeout=4) as r:
            obj = json.loads(r.read(4096))
            record("NET-POS-1", r.status == 200 and obj.get("status") == "ok",
                   http_status=r.status,
                   note="reachability ONLY; HTTP does not provide TLS/mTLS")
    except Exception as exc:
        record("NET-POS-1", False, error=repr(exc))


def key_file_readonly():
    try:
        raw = PIN.read_bytes()
        if not raw:
            raise ValueError("empty witness public key")
        # Check mount flags, not merely owner permissions.
        lines = Path("/proc/self/mountinfo").read_text().splitlines()
        exact = [
            x.split(" - ", 1)[0].split(" ")
            for x in lines if " - " in x
            and x.split(" - ", 1)[0].split(" ")[4] == str(PIN)
        ]
        ro = any("ro" in items[5].split(",") for items in exact if len(items) > 5)
        record("KEY-POS-1", ro, mounted_read_only=ro,
               file_present=True, public_key_length=len(raw))
    except Exception as exc:
        record("KEY-POS-1", False, error=repr(exc))


def key_is_ed25519():
    try:
        data = PIN.read_bytes()
        key = serialization.load_pem_public_key(data)
        if not isinstance(key, Ed25519PublicKey):
            raise ValueError("not Ed25519 public key")
        record("KEY-POS-1b", True,
               fingerprint_sha256=hashlib.sha256(data).hexdigest(),
               note="valid PEM != independently authenticated witness identity")
    except Exception as exc:
        record("KEY-POS-1b", False, error=repr(exc))


def main():
    writable_runtime()
    missing_witness_path()
    no_cross_mount()
    blocked_witness_write()
    health_reachable()
    key_file_readonly()
    key_is_ed25519()
    print(json.dumps({
        "summary": {
            "passed": sum(x["status"] == "PASS" for x in results),
            "total": len(results),
            "failed": [x["id"] for x in results if x["status"] != "PASS"],
            "qualification": "CONTAINER_ONLY_NOT_E8_P0",
        },
    }, sort_keys=True), flush=True)
    return 0 if len(results) == 7 and all(
        r["status"] == "PASS" for r in results
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
