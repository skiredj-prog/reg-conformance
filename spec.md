## Disposition vocabulary

Per RFC-0 §4. The membrane returns exactly one of four dispositions.

| Value | Meaning | Execution instruction |
|---|---|---|
| PASS | Action is admissible under current policy | ALLOW (bounded by `valid_until`) |
| FLAG | Admissible only under an explicit additional condition | ALLOW_WITH_MONITORING |
| HOLD | Suspended pending resolution or human adjudication | SUSPEND (triggers τ_K exhaustion timer) |
| HARD_VETO | Categorically refused | BLOCK (generates signed refusal receipt) |

**Implementation note:** The reference shim v0.1 emits PASS / FLAG / HARD_VETO only.
HOLD is normative in RFC-0 and normative in RFC-5 (τ_K exhaustion semantics), but is not yet emitted by the reference implementation.
This is reported as `IMPLEMENTATION_GAP: HOLD not emitted` in the conformance results.
