"""Pinned E8 laboratory client with freshness-challenged signed reads.

No production G1 grants or dispatch integration. An engine signing key is
optional and MUST NOT be installed in the compromised runtime container.
"""
from pathlib import Path
import secrets

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from witness.protocol import (
    ADVANCE_CONTEXT, ADVANCE_RESULT_CONTEXT, GENESIS_DIGEST, HEAD_CONTEXT, HEAD_KEYS, READ_CONTEXT,
    digest, head_digest, sign, verify,
)


class WitnessIntegrityError(Exception):
    pass


class WitnessChainBroken(WitnessIntegrityError):
    pass


class WitnessKeySubstitution(WitnessIntegrityError):
    pass


class WitnessUnavailable(WitnessIntegrityError):
    pass


class PinnedWitnessClient:
    def __init__(self, base_url, pinned_pubkey_path, expected_realm_id,
                 expected_store_id, *, http_client=None, engine_private_key=None):
        key = serialization.load_pem_public_key(
            Path(pinned_pubkey_path).read_bytes()
        )
        if not isinstance(key, Ed25519PublicKey):
            raise WitnessKeySubstitution("not an Ed25519 key")
        self.key = key
        self.base_url = base_url.rstrip("/")
        self.realm, self.store = expected_realm_id, expected_store_id
        self.http = http_client or httpx.Client(timeout=3)
        self.engine_key = engine_private_key

    def _head(self, raw):
        if raw is None:
            return None
        if not isinstance(raw, dict) or set(raw) != HEAD_KEYS | {"signature"}:
            raise WitnessIntegrityError("head schema mismatch")
        payload = {k: raw[k] for k in HEAD_KEYS}
        try:
            verify(self.key, HEAD_CONTEXT, payload, raw["signature"])
        except ValueError as exc:
            raise WitnessKeySubstitution("head signature invalid") from exc
        if payload["realm_id"] != self.realm or payload["store_id"] != self.store:
            raise WitnessIntegrityError("head scope mismatch")
        return raw

    def get_head(self):
        nonce = secrets.token_hex(16)
        try:
            r = self.http.get(
                self.base_url + "/head", params={"nonce": nonce}
            )
            r.raise_for_status()
            envelope = r.json()
            body = envelope["body"]
            verify(self.key, READ_CONTEXT, body, envelope["signature"])
            if (body["nonce"] != nonce
                    or body["realm_id"] != self.realm
                    or body["store_id"] != self.store):
                raise WitnessIntegrityError("stale / cross-scope read")
            return self._head(body["head"])
        except (httpx.HTTPError, OSError) as exc:
            raise WitnessUnavailable("read unavailable") from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise WitnessIntegrityError("invalid signed read") from exc

    def get_head_at(self, sequence):
        try:
            r = self.http.get(self.base_url + f"/head/at/{sequence}")
            if r.status_code == 404:
                raise WitnessChainBroken("historical head missing")
            r.raise_for_status()
            return self._head(r.json()["head"])
        except httpx.HTTPError as exc:
            raise WitnessUnavailable("history unavailable") from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise WitnessIntegrityError("invalid history") from exc

    def walk_back(self, *, minimum=None, max_heads=10000):
        """Verifies chain relative to a fresh signed head and trusted floor.

        The floor must be provisioned outside the attacker's writable domain.
        This method cannot independently guarantee the floor's provenance.
        """
        head = self.get_head()
        if head is None:
            if minimum is not None:
                raise WitnessChainBroken("head missing despite pinned floor")
            return 0
        if minimum:
            if head["sequence"] < minimum.sequence:
                raise WitnessChainBroken("witness sequence regression")
            pinned = self.get_head_at(minimum.sequence)
            if head_digest({k: pinned[k] for k in HEAD_KEYS}) != minimum.head_digest:
                raise WitnessChainBroken("pinned head mismatch")
        count = 0
        while head is not None:
            count += 1
            if count > max_heads:
                raise WitnessChainBroken("proof depth exhausted")
            expected = (
                GENESIS_DIGEST if head["sequence"] == 1 else None
            )
            if expected is None:
                previous = self.get_head_at(head["sequence"] - 1)
                expected = head_digest({k: previous[k] for k in HEAD_KEYS})
            if head["previous_head_digest"] != expected:
                raise WitnessChainBroken("broken predecessor digest")
            if head["sequence"] == 1:
                return count
            head = previous
        raise WitnessChainBroken("unexpected empty chain")

    def advance(self, body):
        """Lab control-path only, not exposed to the runtime container."""
        if self.engine_key is None:
            raise WitnessIntegrityError("no authorized engine signing key")
        envelope = {
            "body": body,
            "signature": sign(self.engine_key, ADVANCE_CONTEXT, body),
        }
        try:
            r = self.http.post(self.base_url + "/advance", json=envelope)
            r.raise_for_status()
            result = r.json()
            verify(
                self.key, ADVANCE_RESULT_CONTEXT,
                result["body"], result["signature"]
            )
            response = result["body"]
            if response.get("request_digest") != digest(ADVANCE_CONTEXT, body):
                raise WitnessIntegrityError("advance response bound to another request")
            if response["head"] is not None:
                verified = self._head(response["head"])
                if response["decision"] == "ADVANCED":
                    if (verified["sequence"] != body["expected_prev_sequence"] + 1
                            or verified["previous_head_digest"] != body["expected_prev_digest"]
                            or any(verified[k] != body[k] for k in (
                                "state_digest", "key_digest", "quarantine_digest",
                                "realm_id", "store_id", "epoch"
                            ))):
                        raise WitnessIntegrityError("advance result does not match request")
            return response
        except (httpx.HTTPError, OSError) as exc:
            raise WitnessUnavailable("advance outcome UNKNOWN") from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise WitnessIntegrityError("untrusted advance response") from exc
