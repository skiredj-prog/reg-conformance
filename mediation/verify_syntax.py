"""Validate the bounded syntax artifact by schema AND deterministic replay.

A presentation consumer should never trust a hand-edited candidate: acceptance
requires a complete source-text match against the explicit, versioned grammar.
"""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from mediation.interpret import interpret

HERE = Path(__file__).resolve().parent
SCHEMA = json.loads((HERE / "contracts" / "syntax-v0.1.schema.json")
                    .read_text(encoding="utf-8"))
Draft202012Validator.check_schema(SCHEMA)
VALIDATOR = Draft202012Validator(SCHEMA)


def validate_syntax_result(result: dict) -> None:
    """Reject unknown fields, authority promotion and forged candidate clauses."""
    VALIDATOR.validate(result)
    if result != interpret(result["source_text"]):
        raise ValueError("Syntax candidate differs from deterministic source interpretation")
