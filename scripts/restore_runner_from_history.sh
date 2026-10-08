#!/usr/bin/env bash
# Restore full runner.py after MCP truncation incidents.
# Usage: bash scripts/restore_runner_from_history.sh
set -euo pipefail
cd "$(dirname "$0")/.."

GOOD_COMMIT="0d088dba7e5017d4323741b7bc9c0b2e6eabec1a"

echo "Restoring runner.py from ${GOOD_COMMIT}..."
git show "${GOOD_COMMIT}:runner.py" > runner.py

python3 - <<'PY'
from pathlib import Path
text = Path("runner.py").read_text(encoding="utf-8")
if "_run_t7_membrane_vector" in text:
    print("T7 wire already present")
else:
    helper = '''
def _run_t7_membrane_vector(adapter):
    """Execute CT-R4-012 against lab membrane when importable."""
    try:
        from lifecycle.t7_membrane_probe import run_t7_probe
    except ImportError:
        try:
            from t7_membrane_probe import run_t7_probe
        except ImportError:
            return adapter._gap("CT-R4-012", T6_T8_GAP_NOTE + " (probe module missing)")
    status, detail = run_t7_probe()
    if status == "PASS":
        return adapter._r("CT-R4-012", ReportingState.PASS, details=detail)
    if status == "GAP":
        return adapter._gap("CT-R4-012", detail)
    return adapter._fail("CT-R4-012", detail)


'''
    marker = "T6_T8_GAP_NOTE = ("
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("T6_T8_GAP_NOTE not found")
    end = text.find("\n\n\n# ── Base adapter", idx)
    if end < 0:
        end = text.find("\n# ── Base adapter", idx)
    text = text[:end] + "\n" + helper + text[end:]
    old = '    def _v_ct_r4_012(self):\n        return self._gap("CT-R4-012", T6_T8_GAP_NOTE)'
    new = '    def _v_ct_r4_012(self):\n        return _run_t7_membrane_vector(self)'
    n = text.count(old)
    if n != 2:
        raise SystemExit(f"expected 2 handlers to replace, found {n}")
    text = text.replace(old, new)
    Path("runner.py").write_text(text, encoding="utf-8")
    print(f"Applied T7 wire ({n} handlers)")

compile(Path("runner.py").read_text(encoding="utf-8"), "runner.py", "exec")
print("syntax OK", Path("runner.py").stat().st_size, "bytes")
PY

echo "Done. Review and commit:"
echo "  git add runner.py && git commit -m 'RESTORE full runner.py + CT-R4-012 membrane wire'"
