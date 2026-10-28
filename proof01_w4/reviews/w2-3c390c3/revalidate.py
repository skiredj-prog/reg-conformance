"""W4 affected-property reproduction for W2.1c; no producer patch or mock."""
import argparse
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "source-reference.json").read_text())
TERMINALS = ("RECONCILED_CONFIRMED", "RECONCILED_NOT_EXECUTED", "CONFIRMED", "FAILED")


def check_files(directory, old=False):
    refs = ([{"path": "proof_provider.py", "git_blob": MANIFEST["legacy_provider"]["git_blob"]}]
            if old else MANIFEST["files"])
    results = []
    for ref in refs:
        path = directory / Path(ref["path"]).name
        raw = path.read_bytes(); lf = raw.replace(b"\r\n", b"\n")
        if raw != lf:
            path.write_bytes(lf)
        blob = hashlib.sha1(b"blob " + str(len(lf)).encode() + b"\0" + lf).hexdigest()
        if blob != ref["git_blob"]:
            raise RuntimeError("Source Git blob mismatch: " + str(path))
        results.append({"name": path.name, "git_blob": blob,
                        "sha256": hashlib.sha256(lf).hexdigest()})
    return results


def indexes(conn):
    return [[r[0] for r in conn.execute("SELECT name FROM pragma_index_info(?)", (name,))]
            for (name,) in conn.execute('SELECT name FROM pragma_index_list(\'effects\') WHERE "unique"=1')]


def race_writer(sources, db, target, barrier, queue):
    try:
        check_files(Path(sources))
        sys.path.insert(0, sources)
        import lab_s1_bridge as bridge
        rc = bridge.RC01Lab(db_path=db)
        gate_line = next(i for i, line in enumerate(Path(bridge.__file__).read_text().splitlines(), 1)
                         if line.strip().startswith("terminal ="))

        def observer(frame, event, arg):
            if (event == "line" and frame.f_code is bridge.RC01Lab.transition.__code__
                    and frame.f_lineno == gate_line):
                # Schedule both real processes after get_state(), before the
                # guard/write. No return value, variable or producer code changes.
                barrier.wait(timeout=15)
            return observer

        sys.settrace(observer)
        try:
            result = rc.transition("race-op", target, "W4 controlled interleaving")
        finally:
            sys.settrace(None)
        rc.conn.close()
        queue.put({"target": target, "accepted": True, "native_transition": result})
    except Exception as exc:
        queue.put({"target": target, "accepted": False, "error": type(exc).__name__ + ": " + str(exc)})


def worker(args):
    old = args.worker.startswith("legacy-")
    check_files(args.previous_sources if old else args.sources, old=old)
    sys.path.insert(0, str(args.previous_sources if old else args.sources))
    if old:
        from proof_provider import ProofProvider
        p = ProofProvider(db_path=str(args.db))
        for n in range(2 if args.worker == "legacy-duplicates" else 1):
            payload = {"scope": {"account": "legacy-" + str(n), "amount_minor": 100 + n, "currency": "EUR"}}
            p.execute("legacy-op-" + str(n), "legacy-reused-key", payload)
        result = {"created_by": MANIFEST["legacy_provider"]["producer_sha"],
                  "rows": p.conn.execute("SELECT COUNT(*) FROM effects").fetchone()[0],
                  "unique_index_columns": indexes(p.conn),
                  "fixture_scope": "Actual historical laboratory producer, not externally observed real effects"}
        p.conn.close(); return result
    if args.worker == "migrate":
        from proof_provider import ProofProvider
        result = {"constructor_accepted": False}
        try:
            p = ProofProvider(db_path=str(args.db))
            result["constructor_accepted"] = True
            result["unique_index_columns"] = indexes(p.conn)
            payload = {"scope": {"account": "after-upgrade", "amount_minor": 3, "currency": "EUR"}}
            p.execute("new-op", "new-key", payload)
            result["new_distinct_key_write_accepted"] = True
            result["duplicate_groups_after_open_and_write"] = [list(r) for r in p.conn.execute(
                "SELECT idempotency_key,COUNT(*) FROM effects GROUP BY idempotency_key HAVING COUNT(*)>1")]
            p.conn.close()
        except Exception as exc:
            result["error"] = type(exc).__name__ + ": " + str(exc)
        return result
    if args.worker == "terminals":
        from lab_s1_bridge import RC01Lab, run_lab_s1_scenario
        rc = RC01Lab(db_path=str(args.db))
        blocked, accepted = [], []
        for before in TERMINALS:
            for after in (*TERMINALS, "RESERVED"):
                op = before + "-to-" + after
                rc.transition(op, before, "fixture terminal initialization")
                try:
                    transition = rc.transition(op, after, "W4 bounded terminal check")
                    accepted.append(transition)
                except RuntimeError as exc:
                    blocked.append({"before": before, "after": after, "error": str(exc),
                                    "state_preserved": rc.get_state(op) == before})
        rc.transition("race-op", "RESERVED", "fixture nonterminal initialization")
        rc.conn.close()
        ctx = mp.get_context("spawn"); barrier = ctx.Barrier(2); queue = ctx.Queue()
        children = [ctx.Process(target=race_writer, args=(str(args.sources), str(args.db), target, barrier, queue))
                    for target in ("RECONCILED_CONFIRMED", "FAILED")]
        race = []
        try:
            for child in children:
                child.start()
            race = [queue.get(timeout=25) for _ in children]
            for child in children:
                child.join(10)
                if child.exitcode != 0:
                    raise RuntimeError("Race worker did not finish cleanly")
        finally:
            for child in children:
                if child.pid is not None and child.is_alive():
                    child.terminate(); child.join(5)
            queue.close(); queue.join_thread()
        rc = RC01Lab(db_path=str(args.db)); final = rc.get_state("race-op"); rc.conn.close()
        # Exercise the actual bridge after completion, separately from direct
        # transition probes. Restart uses the same operation and stores.
        scenario_dir = args.db.parent / "scenario"; scenario_dir.mkdir()
        first = run_lab_s1_scenario(op_id="bridge-replay-op", db_dir=str(scenario_dir))
        replay = {"first_final_state": first["final_state"], "second_call_rejected": False}
        try:
            replay["second_result"] = run_lab_s1_scenario(op_id="bridge-replay-op", db_dir=str(scenario_dir))
        except RuntimeError as exc:
            replay.update(second_call_rejected=True, error=str(exc))
        rc = RC01Lab(db_path=str(scenario_dir / "rc01.db"))
        replay["persisted_state_after_replay"] = rc.get_state("bridge-replay-op"); rc.conn.close()
        return {"blocked_terminal_to_reserved": blocked,
                "accepted_terminal_replacements": [r for r in accepted if r["from"] != r["to"]],
                "same_terminal_replays_accepted": sum(r["from"] == r["to"] for r in accepted),
                "race_results": race, "race_final_state": final,
                "race_scope": "Two real processes scheduled after read; trace hook changes scheduling only",
                "bridge_replay": replay}
    raise ValueError("Unknown worker")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sources", type=Path, default=ROOT / "sources" / "w2_integration")
    p.add_argument("--previous-sources", type=Path, required=True)
    p.add_argument("--out", type=Path, default=ROOT / "results")
    p.add_argument("--worker", choices=["legacy-clean", "legacy-duplicates", "migrate", "terminals"])
    p.add_argument("--db", type=Path)
    args = p.parse_args(); args.sources = args.sources.resolve(); args.previous_sources = args.previous_sources.resolve()
    if args.worker:
        print(json.dumps(worker(args))); return
    current = check_files(args.sources); previous = check_files(args.previous_sources, old=True)
    args.out.mkdir(parents=True, exist_ok=True)
    executions = []

    def execute(name, command, cwd=ROOT):
        r = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=90)
        (args.out / (name + ".stdout.log")).write_text(r.stdout)
        (args.out / (name + ".stderr.log")).write_text(r.stderr)
        executions.append({"name": name, "command": command, "cwd": str(cwd), "exit_code": r.returncode})
        if r.returncode:
            raise RuntimeError(name + " failed; retained logs required")
        return r.stdout

    def invoke(name, mode, db):
        return json.loads(execute(name, [sys.executable, "-B", str(Path(__file__).resolve()),
                    "--sources", str(args.sources), "--previous-sources", str(args.previous_sources),
                    "--worker", mode, "--db", str(db)]))

    execute("native-three-tests", [sys.executable, "-B", str(args.sources / "test_w2_1.py")], args.sources)
    with tempfile.TemporaryDirectory(prefix="w4-w21c-") as store:
        root = Path(store)
        clean_before = invoke("legacy-clean-create", "legacy-clean", root / "clean.db")
        clean_after = invoke("clean-upgrade", "migrate", root / "clean.db")
        duplicate_before = invoke("legacy-duplicate-create", "legacy-duplicates", root / "duplicates.db")
        duplicate_after = invoke("duplicate-upgrade", "migrate", root / "duplicates.db")
        terminal = invoke("terminal-properties", "terminals", root / "rc01.db")
    migration_open = (duplicate_after["constructor_accepted"]
                      and ["idempotency_key"] not in duplicate_after.get("unique_index_columns", []))
    contradictory_race = (all(r["accepted"] for r in terminal["race_results"])
                          and len({r["native_transition"]["to"] for r in terminal["race_results"]}) > 1)
    terminal_open = bool(terminal["accepted_terminal_replacements"]) or contradictory_race
    result = {"producer_sha": MANIFEST["producer_sha"], "current_sources": current, "legacy_sources": previous,
              "environment": {"python": sys.version, "platform": platform.platform(),
                              "sqlite": sqlite3.sqlite_version, "assertions_enabled": __debug__},
              "native_test_script": {"test_functions": 3, "result": "PASS"},
              "clean_migration": {"before": clean_before, "after": clean_after},
              "duplicate_migration": {"before": duplicate_before, "after": duplicate_after},
              "terminal_properties": terminal, "executions": executions,
              "scope": "Affected-property review only, not a full W3 or integrated crash/recovery campaign",
              "verdict": "W2_1C_SCOPED_PROGRESS" if migration_open or terminal_open else "REQUIRES_REVIEW",
              "p0_migration": "OPEN" if migration_open else "NOT_REPRODUCED",
              "p0_terminal": "OPEN" if terminal_open else "NOT_REPRODUCED",
              "integration_lock": "HOLD", "e2e": "HOLD", "production": "HOLD"}
    (args.out / "review.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"producer_sha": result["producer_sha"], "native_test_script": result["native_test_script"],
                      "clean_upgrade": clean_after, "duplicate_upgrade": duplicate_after,
                      "blocked_terminal_to_reserved": len(terminal["blocked_terminal_to_reserved"]),
                      "accepted_terminal_replacements": len(terminal["accepted_terminal_replacements"]),
                      "race_results": terminal["race_results"], "bridge_replay": terminal["bridge_replay"],
                      "verdict": result["verdict"]}, indent=2))


if __name__ == "__main__":
    main()
