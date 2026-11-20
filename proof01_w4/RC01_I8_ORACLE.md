# RC-01/I8 projection oracle — preparation profile v0.1

This is W4 preparation under PMO 1.0, not a producer state machine, a second I8 ledger or a ratified wire contract. It consumes data only and makes no runtime calls. Its code is independent of the producer and existing verifier replay logic; that implementation separation is not an external institutional review of this author's changes.

## Input boundary

`replay_projection()` accepts exactly the internal profile `w4-rc01-i8-projection/0.1`:

- `operation_id`, `resource_id`, positive integer `amount_minor`.
- `baseline` with nonnegative integer `capacity`, `reserved`, `committed`.
- Explicit `initial_view=INIT`, `initial_settlement=NONE`; other starting histories are unsupported.
- A `records` array, at most 10000 entries, containing unique contiguous `sequence` numbers in a supplied causal order and bound operation IDs.

Kinds are `STATE` (`from`, `to`); `I8` (`action`, resource and amount); and `PROVIDER` (effect status, resource/amount, plus receipt digest and finality for a final assertion). This is an internal test/consumer projection. It does not require W2 to adopt these field names or a global total-order implementation. A mapping may be established from actual native per-operation/resource versions and causal relations only when those data are delivered and reviewed.

**Never fabricate missing fields, copy amounts into unbound settlement rows, or sort unsigned timestamps to create a seemingly valid replay.** An absent field/order/baseline is indeterminate. The mathematical baseline and absence of other resource changes during this single-operation projection are explicit scope assumptions, not evidence of real capture completeness.

## Modeled checks

- Reservation consumes available capacity; commit moves held capacity to committed; release restores held capacity only after a declared negative-final assertion. Confirmation does not restore spent capacity.
- Applied records (`RESERVE_APPLIED`, `COMMIT_APPLIED`, `RELEASE_APPLIED`) differ from observations of replay (`*_REPLAY`). Duplicate applied commits are refused; repeated observations do not inflate applied counts.
- UNKNOWN keeps held resources. REVIEW_REQUIRED is nonterminal and returns to UNKNOWN without releasing budget.
- REPAIR requires an observed final provider assertion and accounting record. It can remain after local COMMITTED/RELEASED while an anchor acknowledgement is pending; witness validity is not checked by this oracle.
- Terminal positive/negative views require matching committed/released accounting. Provider contradictions, binding changes and capacity excesses are refused relative to the supplied projection.
- Provider assertions are model inputs. Their signatures, authority, negative tombstone's real coverage, revocation and real effects are not established here. A later absent response does not erase a final assertion already observed.
- Missing sequence data is indeterminate; a reused sequence or invalid declared transition is refuted. Unknown record/state extensions and multiple receipt versions needing equivocation analysis are not silently accepted.

## Output and comparison

`VERIFIED / PROJECTED_RC01_I8_CONSISTENT` means **only state/arithmetic consistency of the supplied projection**. Output includes balances, applied/replay counters, final view, settlement, and explicit nonclaims for authenticity, completeness, grant and witness. UNKNOWN can be a consistent unresolved prefix; it is not successful outcome resolution. Integration and production remain HOLD in every output.

`compare_projection()` compares that result with a verifier report for the same profile. Missing verifier fields remain indeterminate; value or type differences are refuted (including bool versus integer counters). An agreement proves only agreement of those reports on that projection, not that two implementations or institutions are independently trustworthy.

The current native verifier does not yet emit this projection result. Comparison unit tests use a manually specified report fixture; **no real W2/native differential agreement is claimed**. The historical synthetic `oracle.py` remains a separate format and is not substituted for native evidence.

```sh
python -B -m proof01_w4.rc01_i8_oracle reviewed-projection.json
python -B -m proof01_w4.rc01_i8_oracle reviewed-projection.json --verifier-report native-projection-report.json
python -B -m unittest discover -s proof01_w4/tests -v
```

Exit 0 denotes a VERIFIED mathematical projection property, 1 a refuted projection, 2 indeterminate/invalid input. It never indicates native operational conformance. All JSON/files are bounded and duplicate JSON keys/special files are refused.

## Readiness

The new tests cover held UNKNOWN, REPAIR after failed/local-completed settlement, supervisory review, positive/negative outcomes, improper release, applied versus replayed commits, provider contradictions, capacity and typed binding mismatches, missing evidence, sequence gaps, predecessor mismatch and comparison safeguards. They are oracle preparation fixtures, not producer integration tests.

Full native replay awaits the CEB-01 handoff described in [the pinned W2 compatibility review](docs/w2-02ea1d3/INTERFACE_REVIEW.md), on the same accepted source/deployment/topology as W2/W3. Merkle/witness checks are not bypassed by passing this oracle. **INDEPENDENT REVIEW OPEN / M3 PENDING / E2E HOLD / PRODUCTION HOLD.**
