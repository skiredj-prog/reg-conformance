"""Optional customer-facing preview combining existing mediation with syntax candidates.

PREVENT can start from direct intent or from a validated Discovery report.
PREPARE remains independent and does not pass through a language interpreter.
Every output is review-required; no new normative or execution authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mediation.engine import mediate
from mediation.interpret import interpret


def guide(request: dict) -> dict:
    draft = mediate(request)  # Existing strict v0.1 validation, unchanged.
    syntax = interpret(draft["intent"]) if draft["entry"] == "PREVENT" else None
    questions = list(draft["open_questions"])
    if syntax is not None:
        for question in syntax["open_questions"]:
            if question not in questions:
                questions.append(question)
    return {
        "schema_version": "0.1.0",
        "artifact_kind": "REG_GUIDED_MEDIATION_PREVIEW",
        "mediation_draft": draft,
        "syntax_interpretation": syntax,
        "next_questions": questions,
        "review_required": True,
        "authority_promotion": "NONE",
        "not_legal_advice": True,
        "not_runtime_admissibility": True,
        "not_effective_guarantee": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = json.loads(args.input.read_text(encoding="utf-8"))
    output = guide(request)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    status = (output["syntax_interpretation"] or {}).get("status", "NOT_APPLICABLE")
    print(output["mediation_draft"]["artifact_id"], status)


if __name__ == "__main__":
    main()
