"""
RFC-4 attempt lifecycle vocabulary (shared with lab membrane experiments).

Canonical home for AttemptState in the conformance suite. The executable
membrane lives in tenir-conformance-s1-g1 until a native adapter lands here;
vectors CT-R4-011..013 (T6–T8) reference this vocabulary.
"""

from __future__ import annotations

from enum import Enum


class AttemptState(str, Enum):
    PENDING = "PENDING"
    AWAITING_QUALIFICATION = "AWAITING_QUALIFICATION"
    UNKNOWN = "UNKNOWN"
    FAILED = "FAILED"
    RESOLVED = "RESOLVED"


T6_UNKNOWN_TO_RESOLVED = "T6"
T7_UNKNOWN_TO_FAILED = "T7"
T8_FAILED_RETRY_ELIGIBLE = "T8"

NORMATIVE = {
    "timeout_alone_is_not_failed": True,
    "unknown_blocks_retry_until_t7_or_resolve": True,
    "t7_requires_evidence_qualification": True,
    "t8_requires_retry_eligible_property": True,
}
