# Sprint 1 — W2 native integration intake (pending delivery)

This document prepares the W4 consumer boundary. It is not a new normative CEB schema, producer implementation or approval. Existing owners remain: Agent 1 for W2, Agent 3 for W4, Agent 2/C for W3, PMO for source/deployment lock.

On 2026-10-28, [TENIR #81](https://github.com/skiredj-prog/tenir_governance/issues/81) contains two comments: a reference request and an explicitly unfilled delivery template. No integrated source commit or completed CEB-01 delivery was found in those comments. Searches of the related local workspaces did not locate the named B3/RC-01 kit. This is a bounded absence observation, not proof that no kit exists elsewhere.

| Required input | Intended consumer check | Current status |
|---|---|---|
| B3 `proof-provider-bundle/candidate-v0.1` source, schema and original receipt | Signature domain, exact signed bytes, attempt/operation/payload/epoch bindings, trusted signer role | NOT DELIVERED IN INSPECTED HANDOFF |
| REG-RC-01 candidate v0.1 source and native UNKNOWN/REPAIR records | Valid transitions, causal links, crash checkpoint and idempotent recovery | NOT DELIVERED IN INSPECTED HANDOFF |
| Integrated G4-A/B3/RC-01/I8 commit | Actual checkout and integrated code, one state/budget/dispatch owner | PENDING; do not reuse G4-A-only SHA |
| Deployment manifest and SHA-256; topology/profile/instance IDs | Same deployed subject across W2/W3/W4, exact environment and fault model | PENDING |
| CEB-01 v0.1 inventory `proof-manifest-v1.json` | All declared hashes; source originals retained; no synthetic re-signing | DOCUMENTARY READER PREPARED; NO NATIVE BUNDLE RUN |
| Native event/state/I8/witness/receipt files, test logs and JUnit | Reconstruct lost ACK → UNKNOWN → REPAIR → crash → recovery; measure effects and net settlement | NOT RUN |
| External trust pins and custody, write-path inventory | Separate integrity, signer authority, observation independence and coverage | OPEN |

## Acceptance scenarios prepared for the first actual delivery

| ID | Stimulus on the real integrated subject | Required observation, never assumed |
|---|---|---|
| S1-W2-01 | Provider receives operation; ACK is lost | UNKNOWN persists; reservation retained; no uncontrolled replay; native provider record remains original |
| S1-W2-02 | Provider EXECUTED receipt arrives but I8 settlement fails | REPAIR explicitly linked to the receipt and pending settlement; no false terminal state |
| S1-W2-03 | SIGKILL in the declared REPAIR window, then restart | Durable state recovered; receipt retained; no second net settlement; exact crash point logged |
| S1-W2-04 | Two processes attempt recovery | Single effective settlement under the declared authority; all attempts represented in evidence |
| S1-W2-05 | Old authority epoch or changed payload is reused | Refusal tied to the failed binding; no budget/effect authorization |
| S1-W2-06 | Supplied configuration differs from pinned deployment | Evidence marked stale for that subject; no claim that a complete transitive impact graph already exists |
| S1-W2-07 | A provider event never enters the runtime trace | Independent observation or explicit INDETERMINATE; local sequence continuity does not imply completeness |

All scenario statuses are **NOT_RUN**. No fixture in the W4 packaging tests is an execution of these scenarios. UNKNOWN cannot simply be renamed to one of the synthetic W4 states; Decimal amounts cannot silently be rounded into the synthetic integer schema. A versioned mapping and evidence of property preservation are required before native semantic verification.

Minimum delivery follows the existing #81 template: source SHA; deploy digest/topology; `convergence.json`; `states/operation-states.jsonl`; `events/g4a-events.jsonl`; `events/i8-events.jsonl`; original `receipts/` and `witness/`; reports, logs and open-items with B1/B2 explicit; non-certifying label. An inventory match is readiness for further review, not E2E acceptance.

**No changes to TENIR-Gov, REG Engine, REG+ or their PRs. No production effects, merges or normative promotion.**
