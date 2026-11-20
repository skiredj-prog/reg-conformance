# W4 — Five-identifier binding review

Producer source: `skiredj-prog/tenir_governance` at `02ea1d3bcf5c6fca8e4de6bd7bf5c69cb63f4413`, identified in [source-reference.json](source-reference.json). Consumer basis: #62 at `ecad17b2dd7018823074c53e21f694b85e6042f9`, plus the prepared oracle introduced by #63 at `98ede2b7735694d6026c47a2ed7eb84f21352089`. This review extends that preparation; it does not change either receipt wire schema or producer code.

## Coverage of the five identifiers

| Identifier | Inspected W2 source | Current W4 check | Limit / required handoff |
|---|---|---|---|
| `operation_id` | Receipt body and effects primary key; RC-01 uses `op` and I8 uses its operation argument | Signed receipt equality against the caller's separately held request reference; projection rows must match their declared operation | Name mapping `op`/`op_id`/`operation_id` is only source-level correspondence. No authenticated cross-stream join or global operation uniqueness is established. |
| `evaluation_id` | Absent from the three inspected modules and candidate receipt schema | No native binding check exists; unknown fields in request-reference/profile inputs are refused | Need a versioned evaluation/authorization record and explicit relation to operation/request. A temporal verifier evaluation time is not this identifier. |
| `grant_id` | Scenario assumes authorization; no grant artifact in its returned evidence | Successful signature/time checks still leave `grant authority` unresolved | Need authority provenance, grant scope, conditions/lifetime and binding to evaluation/operation/request/dispatch. Neither a matching string nor a valid provider signature proves admissibility. |
| `idempotency_key` | Signed receipt field; bridge passes a literal key, provider lookup is by operation ID | Exact equality against caller reference; changing it is refused even with a valid fixture signature | No cross-operation uniqueness, request-collision safety or concurrent exclusion follows. W3 owns those attacks. |
| `request_hash` | Signed field computed from compact sorted-key Python JSON of the payload | Exact hash equality against caller reference | Codec/domain/version and original request bytes need identification. No request preimage or hash recomputation is currently delivered to this primitive; no arbitrary reserialization or JCS equivalence is presumed. |

The candidate receipt schema disallows additional fields. It cannot be silently extended with `evaluation_id` or `grant_id`, even by signing an extended fixture. These relations may be carried by a separately authenticated authorization/dispatch artifact that references the exact request/operation and, where appropriate after receipt creation, the receipt digest. The provider need not sign facts outside its authority. The producer and Agent 0 must define and review that relationship before W4 maps it; this consumer review does not invent a mandatory wire format.

## Causality and same-subject requirements

| Relation | Current observation | Condition for real replay |
|---|---|---|
| Evaluation → grant → dispatch | Grant assumed; evaluation/grant evidence absent | Explicit versioned authorization decision and dispatch linkage, including applicable scope/expiry/revocation and the point where it was enforced. |
| Dispatch → provider receipt | Source-level arguments match some receipt fields; exact signed bytes are not returned by the inspected scenario | Native original signed bytes/signature plus independently held request/key references and a reviewed request codec. |
| Receipt → RC-01 transition | Summary gives receipt status; traces give state changes and reasons | Per-transition evidence references and causal/version relations. Receipt truth/finality remains conditional on provider trust and coverage. |
| RC-01 → I8 application | I8 summary is a settled flag; no versioned journal/baseline exported | Durable operation/resource/amount binding, applied-vs-attempt/replay distinction, baseline/capacity and recovery evidence. No copied amount or invented event order. |
| W2/W3 subject → W4 subject | Source SHA alone is insufficient | Same full source SHA, deployment-manifest digest, topology and test-instance/campaign identity, with referenced raw artifacts. Any relevant drift requires revalidation. |

The oracle checks an explicit single-operation ordered projection. It does not authenticate causal order or link all five identifiers. Its strict profile rejects unreviewed extra context fields instead of silently claiming coverage. Consistency of a projection and validity of a signature are separate partial properties; combining their labels does not establish authorization, completeness, native integration or conformity.

## Reproducible negative checks

`python -B -m unittest discover -s proof01_w4/tests -p test_native_binding_boundary.py -v`

Nine consumer tests cover operation/idempotency/request substitution, absent independent bindings, unsupported evaluation/grant fields in references or signed receipts, unsigned outer-context substitution, unsupported oracle context mapping, and request-codec divergence for non-ASCII payloads.

Keys/messages/signatures are generated test fixtures. W2 is neither imported nor executed. Outer-context substitution demonstrates a coverage limit of the receipt primitive, not an exploit reproduced against W2. Request-codec divergence compares two concrete encodings; it is not a claim of a hash collision or a JCS implementation test.

## Verdict

- Receipt operation/idempotency/request equality: **SUPPORTED for the supplied key and independent caller-reference assumptions in the tested primitive**.
- Evaluation/grant-to-execution relation: **GAP in the inspected exported evidence**, not a demonstrated deployment guarantee.
- RC-01/I8 cross-stream causal binding: **INDETERMINATE**, pending native causal records and reviewed mapping.
- Complete integrated verdict: **NOT RUN**; independent review of the author's W4 changes remains open.

**W4 PREPARATION GO / INTEGRATION LOCK HOLD / E2E HOLD / PRODUCTION HOLD.** Agent 1 owns producer fixes, Agent 2 security testing, Agent 0 convergence, Agent C independent B2 custody, and PMO gate decisions.
