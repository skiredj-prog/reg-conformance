# W4 — W2 evidence interface compatibility at 02ea1d3

PMO 1.0, 28 October 2026. Owner: **Agent 3 / W4**. This is the W4 consumer review and oracle-preparation deliverable; Agent 0 retains cross-project coordination, Agent 1 producer development, Agent 2 security attacks and Agent C B2/witness custody. It does not accept a governance gate or independently attest this author's own verifier code.

## Examined producer reference

Repository `skiredj-prog/tenir_governance`, branch `w2-lab-s1-integration`, full SHA **`02ea1d3bcf5c6fca8e4de6bd7bf5c69cb63f4413`**. The GitHub PR lookup for this exact head branch returned no PR at inspection. Source identities are recorded in [source-reference.json](source-reference.json). Only the three W2 modules were inspected; they were not imported, executed or modified by W4.

This is a producer **source reference**, not an accepted integrated G4-A subject. The earlier reconstructed `campaign_instrumented_001.tar.gz` has its own digest and declares no integrated source SHA; its generation by this specific branch has not been established. Those two references must not be silently joined.

## Consumer mapping and gaps

| W2 source/interface | W4 #61/#62 consumer requirement | Current compatibility / missing evidence |
|---|---|---|
| [proof_provider.py:53](https://github.com/skiredj-prog/tenir_governance/blob/02ea1d3bcf5c6fca8e4de6bd7bf5c69cb63f4413/w2_integration/proof_provider.py#L53) `execute()` / `reconcile()` return receipt-body dictionaries | Exact provider-signed message bytes, raw signature and separately referenced key/request bindings | Receipt-body field names align with the candidate schema. Return value alone supplies neither signature nor signed message bytes; no native export is supplied here. **PARTIAL** |
| [proof_provider.py:47](https://github.com/skiredj-prog/tenir_governance/blob/02ea1d3bcf5c6fca8e4de6bd7bf5c69cb63f4413/w2_integration/proof_provider.py#L47) `_canonical()` sorts keys and uses compact JSON before encoding | Interpret the declared versioned producer codec; preserve original signature-covered bytes | Known for this source revision only. Do not substitute arbitrary `json.dumps(receipt)` bytes, claim JCS or infer compatibility with historical ZIP codecs. **CODEC SOURCE KNOWN / EXPORT PENDING** |
| [proof_provider.py:24](https://github.com/skiredj-prog/tenir_governance/blob/02ea1d3bcf5c6fca8e4de6bd7bf5c69cb63f4413/w2_integration/proof_provider.py#L24) constructs a new signing key; sequence starts at zero at line 27 | Key-ID history, external pins, validity/revocation and checkpoint continuity | These lifecycle/provenance records are not returned by the scenario. No independent custody is inferred. **OPEN** |
| Effects table stores signature and JSON | A typed, immutable native receipt export with linked manifest and signature material | Database storage is not a delivered verification bundle. #62 cannot apply temporal/key policy without the external policy and evaluation-time reference. **MISSING INPUT** |
| Provider idempotence lookup uses operation ID; idempotency key is stored without a uniqueness constraint | Valid interpretation of cross-operation claims and request binding | Source evidence to route to W3/Agent 2. No cross-operation security attack was executed in this W4 task, and signature validity cannot demonstrate global idempotence. **OUTSIDE THIS PREPARATION'S PROOF** |
| [lab_s1_bridge.py:31](https://github.com/skiredj-prog/tenir_governance/blob/02ea1d3bcf5c6fca8e4de6bd7bf5c69cb63f4413/w2_integration/lab_s1_bridge.py#L31) calls provider and I8 with their default `:memory:` stores | Durable, correlated state/budget evidence and process-recovery records | Explicit file-path support exists in the classes, but this scenario does not select it. RC-01 uses an in-memory dictionary. No durability/restart claim follows. **OPEN FOR W2** |
| [lab_s1_bridge.py:65](https://github.com/skiredj-prog/tenir_governance/blob/02ea1d3bcf5c6fca8e4de6bd7bf5c69cb63f4413/w2_integration/lab_s1_bridge.py#L65) returns final state, counts, receipt status and traces | CEB-01 manifest, native artifacts, source/deployment/topology identity, raw causal ledger | No CEB-01 exporter in these inspected modules. Do not manufacture a CEB manifest to promote the summary. **NOT IMPORT-READY** |
| RC-01 traces contain timestamp/op/from/to/reason | Version/epoch or causal ordering supported by native evidence | Timestamps alone are not an authenticated cross-stream order. Oracle projection must wait for explicit causal data. **INCOMPLETE** |
| [i8_ledger.py:33](https://github.com/skiredj-prog/tenir_governance/blob/02ea1d3bcf5c6fca8e4de6bd7bf5c69cb63f4413/w2_integration/i8_ledger.py#L33) updates a settlement flag | Distinguish applied settlement, failed attempt and replay; amount/resource/op bindings and before/after accounting | Methods do not return a versioned journal or per-resource baseline/capacity. **INCOMPLETE** |
| [i8_ledger.py:67](https://github.com/skiredj-prog/tenir_governance/blob/02ea1d3bcf5c6fca8e4de6bd7bf5c69cb63f4413/w2_integration/i8_ledger.py#L67) `net_settlement_count()` returns a Boolean-like 0/1 view | Independent assessment of one applied net settlement and duplicate attempts | This flag is not an independently observed physical write/effect count. Do not equate them. **BOUNDED SUMMARY ONLY** |
| No Merkle/checkpoint or witness export in the three W2 modules | Native inclusion proof, signed checkpoint, external pin and witness chain/custody | No proof is invented by W4. Mathematical Merkle verification awaits actual evidence/codec. Agent C retains B2. **MISSING** |
| Scenario explicitly assumes the grant and does not wire historical G4-A | Actual authority boundary and integrated subject identity | W4 does not relabel it as native G4-A. Agent 1/0 own the integration decision; W3 tests its security boundary. **INTEGRATION LOCK HOLD** |

These are source/interface observations. They do not replace Agent 2 counterexamples, producer test results or a native replay on a locked integrated subject.

## Prepared oracle

`rc01_i8_oracle.py` is a separate state/arithmetic implementation and imports no producer module, receipt verifier or synthetic semantic replay. Its internal input profile is documented in [RC01_I8_ORACLE.md](../../RC01_I8_ORACLE.md). It recognizes explicit ordered single-operation projections only. It never infers missing operation/amount bindings or sorts independent timestamp streams into an invented causal order.

The earlier campaign 001 lacks required settlement bindings/baselines and trustworthy causal ordering. The current W2 source returns a scenario summary rather than this projection or a CEB-01. **No complete replay or actual verifier/oracle agreement is claimed for either input.** The comparison API and tests are prepared; the verifier currently has no native projection result to compare.

## M3 entry conditions and next handoff

Agent 1 supplies the native export, integrated commit, deployment digest/topology/test-instance identity, original receipts/signatures, baseline and causal ledger; W3 supplies results for that same subject. Agent 0 checks reference convergence. W4 then fixes the explicit field mapping, verifies available native evidence and performs the independent replay/differential comparison. PMO decides the resulting gate; B2/custody remains a distinct Agent C responsibility.

Full acceptance still needs raw run commands/logs, actual SIGKILL/recovery and concurrency evidence, external trust references and explicit limitations. A local model test, a checklist or an isolated CI PASS does not satisfy those requirements.

**W4 PREPARATION GO / COMPLETE NATIVE REPLAY NOT RUN / INTEGRATION LOCK HOLD / E2E HOLD / PRODUCTION HOLD.**
