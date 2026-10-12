# Evidence ledger anchors

This directory publishes checkpoints of the membrane's evidence ledger, produced by
`tenir-conformance-s1-g1` (`src/tenir_conformance/membrane/evidence_ledger.py` and
`checkpoint_policy.py`).

## What is published, and what never is

- **Published: only anchor files**, named `YYYY-MM-DD-<length>.anchor.json`.
- **Never published: entries files** (`*.entries.json`). They can contain signatures and
  trust-root snapshots. They stay on the machine that runs the membrane, outside any Git
  repository, and are shared with an auditor only under a separate agreement.

## Anchor format

```json
{
  "format": "evidence-ledger-anchor/v1",
  "head": "<64 lowercase hex characters>",
  "length": 3
}
```

`head` is the hash of the last entry; `length` is the number of entries. Anchor files are
produced by the membrane tooling and are never edited by hand.

## What an anchor proves, and what it does not

An anchor proves that a ledger with this head and length existed when the anchor was
committed to this repository, and that the chain up to that head was intact. It does not
prove that the events summarised by the entries are true, nor that any verification key was
legitimate. Those remain assumptions A and the trust-root obligation in the manuscript.

## How checkpoints are produced

The membrane writes checkpoints itself, from its own process, when started with:

| Variable | Meaning |
|---|---|
| `TENIR_CHECKPOINT_ENABLED=1` | enables checkpoints (disabled by default) |
| `TENIR_CHECKPOINT_DIR` | output directory, required, must not be inside a Git repository |
| `TENIR_CHECKPOINT_EVERY_ENTRIES` | checkpoint after this many new entries (integer >= 1, default 100) |
| `TENIR_CHECKPOINT_DAILY` | `1` checkpoints the first new entries of each day (default `1`) |

Configuration is read at start-up. A change requires a restart.

## Publishing an anchor

1. Take the anchor file from `TENIR_CHECKPOINT_DIR`. Do not take the entries file.
2. Check its format before committing:

   ```bash
   python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d['format']=='evidence-ledger-anchor/v1' and len(d['head'])==64, d"  <path>
   ```

3. Branch, copy the file, commit, push, and open a pull request:

   ```bash
   git checkout main && git pull
   git checkout -b anchor/<name>
   cp <path>/<name>.anchor.json anchors/
   git add anchors/<name>.anchor.json
   git commit -m "anchor: <name>"
   git push -u origin anchor/<name>
   gh pr create --base main --head anchor/<name> --title "anchor: <name>" \
     --body "Checkpoint of the evidence ledger. Only the anchor is published."
   ```

4. Merge the pull request after review. `main` is protected: no direct push and no force-push.

## Verifying an anchor

An auditor who receives the entries file from the operator checks it against the published
anchor:

```bash
PYTHONPATH=src python tools/checkpoint_ledger.py <name>.entries.json
```

The output must equal the anchor file in this directory. The tool exits non-zero, and prints
nothing on stdout, if the chain does not verify.

## Restarts

A restart of the membrane starts a new chain from genesis. Its anchors are independent of
earlier ones: an auditor verifies each chain against its own anchors. The pull request that
publishes the first anchor after a restart must say so in its description, with the restart
time. Silence about a restart would make a reset look like a truncation.

## Incidents

If an entries file fails verification against an already published anchor, do not publish a
new anchor to replace it. Open an issue, attach the verification output, and keep the
original anchor in place.
