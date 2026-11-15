# E1/E2 replay — 15 November 2026

Replay of the experiments behind *Governing the Unobserved* §§5.4, 6 and 8 against three revisions of `skiredj-prog/tenir-conformance-s1-g1`. No event, invariant, state key or scenario was added. Python 3.13.18; the companion kernel `tenir_governance` was not installed, so `KernelBridge` used its documented local fallback.

| Label | Revision | Role |
|---|---|---|
| historical | explorer `cf1b1ea` (tag `archive/forensic/e2-key-audit-20261009`) + membrane overlay `84e46d9` | Table 1, as in workflow `e1-e2-repro.yml` |
| current | `d42499b` | Table 3 CI artifact; Table 4 |
| latest | `8bc0e5e` (main, 30 Oct 2026) | trace and E1 check only |

The two diffs in `scripts/` apply from the repository root at `d42499b` with `git apply scripts/<name>.diff`; the corresponding `*_adapted.py` files are the patched scripts, run from `scripts/`.

## Results

**1. Table 1 reproduces.** The four historical outputs equal the committed `experiments/e1_e2/r*.json` on every field except `seconds`, including 42,934 `I1` occurrences and the three-transition witness (`results/historical-84e46d9/comparison_with_committed.txt`). The E1 script at `cf1b1ea` also equals that commit's `e1_results.txt`.

**2. The Table 3 CI artifact never puts a second attempt to the admission guard.** `scripts/e2_instrument.py` replays the explorer's loop with the same events, key and checks and reproduces the CI counts (`honest` 675/25,297, `adversarial` 2,307/88,567). It shows that every `process(...)` event raises `NONCE_REQUIRED` and every qualified `declare_failed` / negative `reconcile` is rejected for a missing signature. First-attempt effects are still dispatched through `admit_await`, which carries a nonce (384 states with an observed effect in `honest`, 768 in `adversarial`), but no explored state contains a `FAILED` attempt or two admitted attempts (`results/current-d42499b/instr-*.json`; zero counts are omitted from `reachability`). The guard is never asked to admit an attempt after a failed one, the case on which I1 depends.

**3. Table 4: current revision with nonces and signed attestations.** `scripts/e2_explore_adapted.diff` (13 changed lines) passes the attempt nonce on dispatch-class calls and attaches an Ed25519 attestation, signed with the repository's own test signer (`tests/s7_helpers.py`, lab key K1), to qualified non-execution claims.

| World | Depth | States | Transitions | I1 occurrences | Shortest trace | FAILED states | Two-attempt states |
|---|---:|---:|---:|---:|---:|---:|---:|
| honest | 8 | 149,771 | 2,702,234 | 0 | — | 147,964 | 145,992 |
| false_attest | 7 | 178,890 | 2,201,968 | 0 | — | 173,995 | 169,805 |
| hidden_honest | 8 | 180,193 | 3,424,852 | 0 | — | 177,822 | 175,850 |
| adversarial | 7 | 280,023 | 3,410,213 | 305,429 | 3 | 273,962 | 267,926 |

Depth-6 runs of all four worlds are included. Remaining exceptions are only `KeyError` on events addressed to an unregistered attempt and `StaleReceiptError` on expired tokens; this was checked event by event at depth 5. No run reached a fixpoint.

**4. The three-transition trace with a verified signature** (`results/*/e3_three_transition_trace.txt`, `scripts/e3_trace.py`). On `d42499b` and `8bc0e5e`: hidden effect, then a false attestation correctly bound and signed by K1, is accepted (`LEI_UNLOCKED_BY_VERIFIED_NON_EXECUTION`), and the second dispatch resolves. That gives two world effects, so I1 is violated. Controls hold I1: an unsigned qualified flag, an invalid signature, and an observed effect with the same signed false attestation (`T7_REJECTED_EFFECT_ALREADY_OBSERVED`).

**5. E1 on the current membrane.** The committed E1 script, unmodified, collapses M1 on `d42499b`: 18 single-effect outcomes instead of 38, and 64 blocked retries (`results/current-d42499b/e1_unmodified_vs_committed.txt`). With `scripts/e1_baseline_adapted.diff` (signed attestation on negative evidence), the output is byte-identical to the committed `e1_results.txt` on `d42499b` and `8bc0e5e`.

## Not covered

Real `tenir_governance` kernel (fallback only; it reproduced the CI counts, which used the real kernel), Table 2 forensic key audit, Hypothesis Lab, S7–S12, depth 8 for `false_attest`/`adversarial`.

## Commands

From a checkout of the revision, with `pip install -e .` for `d42499b`/`8bc0e5e` (dependencies `cryptography`, `PyYAML`, `rfc8785`):

```bash
export PYTHONHASHSEED=0 PYTHONPATH=src S1G1_TESTS=$PWD/tests
# Table 4 (d42499b)
python scripts/e2_instrument.py scripts/e2_explore_adapted.py adversarial 7 > adapt-adversarial-d7.json
# three-transition trace
python scripts/e3_trace.py $PWD
# E1 with signed evidence
python scripts/e1_baseline_adapted.py > e1.txt && cmp e1.txt experiments/e1_e2/e1_results.txt
```

Historical commands are in Appendix A.1 of the revised manuscript. `SHA256SUMS` lists every file in this archive.
