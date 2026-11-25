# results/

`runner.py` and `python -m harness` write their reports here by default
(`results/tenirlabs-v0.4.0.json`, `results/port-run.json`). The four JSON files
kept in the repository are historical outputs, left as they were produced:

| File | Suite | Run | Mode | Level the file carries |
|---|---|---|---|---|
| `validate-adapter-v0.2.4.json` | v0.2.4 | 2026-10-02 | adapter | 2, `ADAPTER_TESTED` |
| `validate-native-v0.2.4.json` | v0.2.4 | 2026-10-02 | native | 3, `NATIVE_CONFORMANT` |
| `tenirlabs-v0.3.1-adapter.json` | v0.3.1 | 2026-10-04 | adapter | 2, `ADAPTER_TESTED` |
| `tenirlabs-v0.3.1-native.json` | v0.3.1 | 2026-10-04 | native | 3, `NATIVE_CONFORMANT` |

Level 3 is the label those suites gave the reference kernel bundled in this
repository. Since 30 October 2026 the runner reports that kernel at level 1,
`SEMANTIC_MAPPING` (see the qualification boundary in `README.md` and the note
under the interface modes in `spec.md`), and no run reaches level 3 today
(`CLAIMS.md`). Do not quote these files as results: the published runs are in
[`RESULTS.md`](../RESULTS.md).
