"""REG guided syntax interpretation v0.1.

A tiny, exhaustive grammar for illustrative requirements. Not semantic NLP,
normative interpretation, legal applicability or an executable compiler.

Full-match-only: unknown clauses or qualifications cause abstention, never
partial automatic interpretation. All proposals remain unreviewed.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

VERSION = "0.1.0"
MAX_TEXT = 4000
LIMIT_MS = 600000
LIMIT_AMOUNT = 10**12

PATTERNS = (
    (
        "LATENCY_DEDUP_FR",
        re.compile(
            r"ne jamais exécuter deux fois un règlement si la latence "
            r"(?:système )?dépasse (?P<value>[0-9]+) ms\.?",
            re.IGNORECASE,
        ),
        "latency_dedup",
    ),
    (
        "LATENCY_DEDUP_EN",
        re.compile(
            r"never execute a settlement twice if (?:system )?latency "
            r"exceeds (?P<value>[0-9]+) ms\.?",
            re.IGNORECASE,
        ),
        "latency_dedup",
    ),
    (
        "HUMAN_APPROVAL_FR",
        re.compile(
            r"tout paiement supérieur à (?P<value>[0-9]+(?: [0-9]{3})*) "
            r"(?P<currency>MAD|EUR|USD) exige une approbation humaine avant exécution\.?",
            re.IGNORECASE,
        ),
        "human_approval",
    ),
    (
        "HUMAN_APPROVAL_EN",
        re.compile(
            r"every payment above (?P<value>[0-9]+(?:,[0-9]{3})*) "
            r"(?P<currency>MAD|EUR|USD) requires human approval before execution\.?",
            re.IGNORECASE,
        ),
        "human_approval",
    ),
    (
        "RESIDENCY_AUDIT_FR",
        re.compile(
            r"les données clients ne doivent jamais quitter la région autorisée,? "
            r"et chaque accès doit être journalisé\.?",
            re.IGNORECASE,
        ),
        "residency_audit",
    ),
    (
        "RESIDENCY_AUDIT_EN",
        re.compile(
            r"customer data must never leave the (?:authorized|permitted) region,? "
            r"and every access must be logged\.?",
            re.IGNORECASE,
        ),
        "residency_audit",
    ),
)

def _candidate(property_id: str, trigger: dict | None, obligations: list[dict],
               excerpt: str, pattern_id: str, questions: list[str]) -> dict:
    return {
        "proposal_id": "CAND_" + property_id,
        "pattern_id": pattern_id,
        "source_excerpt": excerpt,
        "trigger": trigger,
        "obligations": obligations,
        "interpretation_status": "UNREVIEWED_SYNTAX_CANDIDATE",
        "canonical_invariant_id": None,
        "open_questions": questions,
    }


def interpret(text: str) -> dict:
    """Recognize a complete narrow sentence or explicitly abstain.

    A match is neither a semantically verified requirement nor a profile.
    No silent threshold fallback, inference from keywords or source authority.
    """
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT:
        raise ValueError("intent must be nonempty text within 4000 characters")
    original = text.strip()
    normalized = re.sub(r"\s+", " ", original)
    result = {
        "schema_version": VERSION,
        "status": "ABSTAIN_UNSUPPORTED",
        "source_text": original,
        "source_kind": "USER_DECLARED_INTENT",
        "proposals": [],
        "open_questions": [
            "Clarify the precise normative condition, scope, exceptions and external effects."
        ],
        "review_required": True,
        "meaning_verified": False,
        "applicability": "NOT_ASSESSED",
        "profile_status": "NOT_ADMITTED",
        "code_generation": "NOT_GENERATED",
    }
    for pattern_id, grammar, kind in PATTERNS:
        match = grammar.fullmatch(normalized)
        if not match:
            continue
        if kind == "latency_dedup":
            value = int(match["value"])
            if not 0 < value <= LIMIT_MS:
                break
            proposals = [_candidate(
                "CONDITIONAL_NO_DUPLICATE_SETTLEMENT",
                {"operand": "latency_ms", "operator": ">", "value": value, "unit": "ms"},
                [{"property": "no_duplicate_settlement_effect", "operator": "==",
                  "value": True, "timing": "external_effect"}],
                original, pattern_id,
                ["What constitutes one settlement identity across retries and external providers?",
                 "Does the original requirement apply ONLY above the latency threshold?",
                 "How are UNKNOWN outcomes reconciled without producing a second effect?"],
            )]
        elif kind == "human_approval":
            value = int(match["value"].replace(" ", "").replace(",", ""))
            if not 0 < value <= LIMIT_AMOUNT:
                break
            proposals = [_candidate(
                "CONDITIONAL_HUMAN_APPROVAL",
                {"operand": "payment_amount", "operator": ">", "value": value,
                 "unit": match["currency"].upper()},
                [{"property": "human_approval", "operator": "==",
                  "value": True, "timing": "before_execution"}],
                original, pattern_id,
                ["What authority and payment payload does the approval bind?",
                 "Which currency conversion and amount valuation rules apply?",
                 "How can the system establish approval occurred before the effect?"],
            )]
        else:
            proposals = [
                _candidate("CUSTOMER_DATA_RESIDENCY", None,
                           [{"property": "customer_data_remains_in_authorized_region",
                             "operator": "==", "value": True, "timing": "continuous"}],
                           original, pattern_id,
                           ["Which region is authorized, and for which data and processors?"]),
                _candidate("ACCESS_LOGGING", None,
                           [{"property": "each_access_recorded", "operator": "==",
                             "value": True, "timing": "on_access"}],
                           original, pattern_id,
                           ["What counts as an access and what minimum logging evidence is needed?"]),
            ]
        result["status"] = "SYNTAX_CANDIDATES_UNVERIFIED"
        result["proposals"] = proposals
        result["open_questions"] = [question for item in proposals
                                    for question in item["open_questions"]]
        break
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="UTF-8 plain-text requirement")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    text = args.input.read_text(encoding="utf-8")
    output = interpret(text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(output["status"], len(output["proposals"]), "candidate(s)")


if __name__ == "__main__":
    main()
