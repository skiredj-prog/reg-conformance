"""W4 read-only source reproduction, on isolated temporary SQLite stores.

Producer files are Git-blob checked before import. No producer patch, mock,
replacement ledger, signature fabrication or CEB construction is performed.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources" / "w2_integration"
MANIFEST = json.loads((ROOT / "source-reference.json").read_text())


def check_sources():
    results = []
    for f in MANIFEST["files"]:
        path = SOURCES / Path(f["path"]).name
        raw = path.read_bytes()
        # Snapshot materialization may use Windows newlines. Restore Git's
        # fetched LF bytes before checking; no source statements are changed.
        lf = raw.replace(b"\r\n", b"\n")
        if raw != lf:
            path.write_bytes(lf)
        digest = hashlib.sha1(b"blob " + str(len(lf)).encode() + b"\0" + lf).hexdigest()
        if digest != f["git_blob"]:
            raise RuntimeError("Source blob mismatch: " + f["path"])
        results.append({"path": f["path"], "git_blob": digest,
                        "sha256": hashlib.sha256(lf).hexdigest()})
    return results


def worker(mode, store):
    check_sources()
    sys.path.insert(0, str(SOURCES))
    from lab_s1_bridge import run_lab_s1_scenario, RC01Lab
    from proof_provider import ProofProvider
    from i8_ledger import I8Ledger
    store = Path(store)
    if mode == "scenario":
        observations = []

        def trace(frame, event, arg):
            filename = Path(frame.f_code.co_filename)
            if filename == SOURCES / "i8_ledger.py" and frame.f_code.co_name == "settle":
                if event == "exception" and isinstance(arg[1], RuntimeError):
                    observations.append({"kind": "SETTLE_EXCEPTION", "message": str(arg[1])})
                elif event == "return" and arg is None:
                    # Raw return events also occur on exception unwind. They
                    # are not classified as successful settlement records.
                    observations.append({"kind": "SETTLE_RETURN", "line": frame.f_lineno})
            if (filename == SOURCES / "lab_s1_bridge.py" and frame.f_code.co_name == "transition"
                    and event == "call"):
                observations.append({"kind": "TRANSITION_CALL", "to": frame.f_locals["to"]})
            return trace

        sys.settrace(trace)
        try:
            native = run_lab_s1_scenario(op_id="w4-restart-op", db_dir=str(store))
        finally:
            sys.settrace(None)
        db = sqlite3.connect(store / "provider.db")
        receipt = json.loads(db.execute("SELECT receipt_json FROM effects").fetchone()[0]); db.close()
        return {"native_summary": native, "observer_events": observations,
                "observer_scope": "W4 sys.settrace in-process observation; not native durable journal",
                "receipt_key_id": receipt["key_id"], "receipt_sequence": receipt["sequence"]}
    if mode == "reload":
        provider = ProofProvider(db_path=str(store / "provider.db"))
        i8 = I8Ledger(db_path=str(store / "i8.db"))
        rc = RC01Lab(db_path=str(store / "rc01.db"))
        receipt = provider.reconcile("w4-restart-op")
        from cryptography.hazmat.primitives import serialization
        key = provider.public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        report = {"effect_rows": provider.execute_count("w4-restart-op"),
                  "settlement_flag": i8.net_settlement_count("w4-restart-op"),
                  "i8_row": list(i8.conn.execute("SELECT operation_id,reserved,settled,released FROM ledger").fetchone()),
                  "receipt_key_id": receipt["key_id"],
                  "new_constructor_key_id": hashlib.sha256(key).hexdigest(),
                  "new_constructor_sequence": provider.sequence,
                  "rc01_loaded_state": rc.get_state("w4-restart-op"),
                  "unique_index_columns": unique_indexes(provider.conn),
                  "rc01_constructor_parameters": list(inspect.signature(RC01Lab).parameters)}
        provider.conn.close(); i8.conn.close(); rc.conn.close()
        return report
    if mode == "inspect-old-schema":
        provider = ProofProvider(db_path=str(store / "old-provider.db"))
        result = {"unique_index_columns": unique_indexes(provider.conn)}
        provider.conn.close()
        return result
    if mode == "same-key-alias":
        provider = ProofProvider(db_path=str(store / "alias.db"))
        payload = {"scope": {"account": "fixture", "amount_minor": 100, "currency": "EUR"}}
        first = provider.execute("alias-first-op", "same-key", payload)
        second = provider.execute("alias-second-op", "same-key", payload)
        result = {"requested_operation": "alias-second-op", "returned_operation": second["operation_id"],
                  "same_returned_receipt": first == second,
                  "rows": provider.conn.execute("SELECT COUNT(*) FROM effects").fetchone()[0],
                  "scope": "Native component output-binding check; not a concurrency or external-effect test"}
        provider.conn.close()
        return result
    raise ValueError("Unknown worker")


def unique_indexes(conn):
    return [[r[0] for r in conn.execute("SELECT name FROM pragma_index_info(?)", (name,))]
            for (name,) in conn.execute('SELECT name FROM pragma_index_list(\'effects\') WHERE "unique"=1')]


def main():
    global SOURCES
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=["scenario", "reload", "same-key-alias", "inspect-old-schema"])
    parser.add_argument("--store")
    parser.add_argument("--sources", type=Path, default=SOURCES,
                        help="Directory containing the four exact producer files")
    parser.add_argument("--out", type=Path, default=ROOT / "results")
    parser.add_argument("--previous-sources", type=Path,
                        help="Optional isolated f1ada7b source directory for real old-schema creation")
    args = parser.parse_args()
    SOURCES = args.sources.resolve()
    identities = check_sources()
    if args.worker:
        print(json.dumps(worker(args.worker, args.store))); return
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    executions = []

    def execute(name, command, cwd=ROOT):
        completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=60)
        (out / (name + ".stdout.log")).write_text(completed.stdout)
        (out / (name + ".stderr.log")).write_text(completed.stderr)
        executions.append({"name": name, "command": command, "cwd": str(cwd),
                           "exit_code": completed.returncode})
        if completed.returncode:
            raise RuntimeError(name + " failed; see retained logs")
        return completed.stdout

    execute("native-test-script", [sys.executable, "-B", str(SOURCES / "test_w2_1.py")], SOURCES)
    with tempfile.TemporaryDirectory(prefix="w4-w21-") as store:
        first = json.loads(execute("native-scenario", [sys.executable, "-B", str(Path(__file__).resolve()),
                                                       "--sources", str(SOURCES), "--worker", "scenario", "--store", store]))
        second = json.loads(execute("new-process-reload", [sys.executable, "-B", str(Path(__file__).resolve()),
                                                           "--sources", str(SOURCES), "--worker", "reload", "--store", store]))
        alias = json.loads(execute("native-alias-binding", [sys.executable, "-B", str(Path(__file__).resolve()),
                                                           "--sources", str(SOURCES), "--worker", "same-key-alias", "--store", store]))
        repeated = json.loads(execute("completed-scenario-reentry", [sys.executable, "-B", str(Path(__file__).resolve()),
                                  "--sources", str(SOURCES), "--worker", "scenario", "--store", store]))
        old_schema = None
        if args.previous_sources:
            # The old file is verified in that subprocess before importing it.
            creator = (
                "import sys,hashlib,json;from pathlib import Path;"
                "p=Path(sys.argv[1])/'proof_provider.py';b=p.read_bytes().replace(b'\\r\\n',b'\\n');"
                "assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\\0'+b).hexdigest()=='5e64adc8f35e2698622c5a3ae47b2bd353946ba9';"
                "sys.path.insert(0,str(p.parent));from proof_provider import ProofProvider;"
                "x=ProofProvider(db_path=sys.argv[2]);x.conn.close();"
                "print(json.dumps({'schema_created_by':'f1ada7b78d9f4c13656efc7f9f8c5a165394a9fb'}))"
            )
            execute("old-schema-create", [sys.executable, "-B", "-c", creator,
                                         str(args.previous_sources.resolve()), str(Path(store)/"old-provider.db")])
            old_schema = json.loads(execute("old-schema-new-code-open", [sys.executable, "-B", str(Path(__file__).resolve()),
                                     "--sources", str(SOURCES), "--worker", "inspect-old-schema", "--store", store]))
    events = first["observer_events"]
    failed = next(i for i, e in enumerate(events) if e["kind"] == "SETTLE_EXCEPTION")
    repair = next(i for i, e in enumerate(events) if e.get("to") == "REPAIR")
    result = {"producer_sha": MANIFEST["producer_sha"], "source_identities": identities,
              "environment": {"python": sys.version, "platform": platform.platform(),
                              "assertions_enabled": __debug__, "sqlite": sqlite3.sqlite_version},
              "native_test_script": {"result": "PASS", "test_functions": 2,
                                     "scope": "Two supplied test functions; restart function reopens B3 and RC01 in same process"},
              "separate_process_component_reopen": {
                  "b3_rows_persist": second["effect_rows"] == 1,
                  "i8_flag_persists": second["settlement_flag"] == 1,
                  "rc01_state_restored": second["rc01_loaded_state"] == "RECONCILED_CONFIRMED",
                  "key_continuity": second["receipt_key_id"] == second["new_constructor_key_id"]},
              "repair_order_observed": failed < repair,
              "first_process": first, "second_process": second, "alias_binding": alias,
              "completed_scenario_reentry": repeated,
              "prior_schema_opened_by_new_code": old_schema,
              "executions": executions,
              "limitations": ["Cooperative process exit/reopen, not SIGKILL or power-loss durability",
                              "SQLite flags/rows are not independently observed external effects",
                              "Trace hook observes order but is not an authenticated durable native ledger",
                              "No integrated grant, native I8 convergence or CEB-01 validation",
                              "No W3 concurrency/privileged writer/same-UID campaign executed"],
              "verdict": "W2_1B_PARTIAL", "integration_lock": "HOLD", "e2e": "HOLD", "production": "HOLD"}
    (out / "review.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("producer_sha", "native_test_script",
                    "separate_process_component_reopen", "repair_order_observed", "alias_binding",
                    "prior_schema_opened_by_new_code", "verdict")}, indent=2))


if __name__ == "__main__":
    main()
