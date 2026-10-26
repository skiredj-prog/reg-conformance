"""Durable local progress cache. NOT an independent witness trust root.

A same-UID attacker may replace or delete this file. A trusted floor must
ultimately be provisioned out of band; corruption always fails closed.
"""
import json
import os
from dataclasses import dataclass
from pathlib import Path
import tempfile

from witness.protocol import validate_sha256


@dataclass(frozen=True)
class LocalCheckpoint:
    sequence: int
    head_digest: str


def load_checkpoint(path):
    p = Path(path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if (set(data) != {"sequence", "head_digest"}
                or type(data["sequence"]) is not int
                or data["sequence"] < 1):
            raise ValueError("invalid checkpoint")
        validate_sha256(data["head_digest"])
        return LocalCheckpoint(data["sequence"], data["head_digest"])
    except (ValueError, OSError, TypeError, KeyError) as exc:
        raise ValueError("CHECKPOINT_UNTRUSTED: refuse silent reset") from exc


def save_checkpoint(path, checkpoint):
    if (type(checkpoint.sequence) is not int or checkpoint.sequence < 1):
        raise ValueError("invalid checkpoint sequence")
    validate_sha256(checkpoint.head_digest)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".checkpoint-", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({
                "sequence": checkpoint.sequence,
                "head_digest": checkpoint.head_digest,
            }, f, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, target)
        if hasattr(os, "O_DIRECTORY"):
            directory_fd = os.open(str(target.parent), os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
