"""Port over the real Prismor MCP gateway.

What is under test: `prismor mcp-gateway` in enforce mode, started as a
subprocess from an installed Prismor build, in front of one stdio MCP server
(`counter_server.py`). The port speaks MCP to the gateway as an agent would.
Nothing in Prismor is patched, mocked or imported.

What this port does NOT add: replay protection, grants, standing, receipts.
Anything Prismor does not do itself stays undeclared and is reported
ADAPTER_REQUIRED.

Shape of the boundary: the gateway decides and forwards in one step. There is
no grant that is later committed, so `commit` is not declared and `evaluate`
is the boundary crossing.

Disposition mapping (PROVISIONAL, written by the harness author from the
gateway's own replies; to be confirmed or corrected by Prismor):
    forwarded, isError false                      -> PASS
    "Blocked by Prismor", rule action block       -> HARD_VETO
    "Blocked by Prismor", rule action step_up     -> HOLD
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from ... import port as P

_HERE = Path(__file__).resolve().parent
_INTENT_ARG = {P.ADMISSIBLE: "allow", P.DENIED: "deny", P.NEEDS_APPROVAL: "step_up"}
_RULE_DISPOSITION = {"reg-pilot-deny": "HARD_VETO", "reg-pilot-step-up": "HOLD"}
TOOL = "count__record"


class PrismorGatewayPort(P.RuntimePort):
    name = "prismor-mcp-gateway"
    interface_mode = "port:prismor-mcp-gateway"
    evidence_level = 2
    capabilities = frozenset({P.EVALUATE, P.EFFECTS})
    # DENIED, not INADMISSIBLE: a Prismor policy block is not a REG structural verdict.
    intents = frozenset({P.ADMISSIBLE, P.DENIED, P.NEEDS_APPROVAL})

    def __init__(self, prismor_bin=None, timeout=30):
        self._bin = prismor_bin or os.environ.get("PRISMOR_BIN") or shutil.which("prismor")
        if not self._bin:
            raise RuntimeError("Prismor binary not found: set PRISMOR_BIN to the pinned build.")
        self._timeout = timeout
        self._proc = None
        self._dir = None
        self._id = 0

    # -- lifecycle ----------------------------------------------------------
    def reset(self):
        self.close()
        self._dir = Path(tempfile.mkdtemp(prefix="reg-prismor-"))
        ws, home = self._dir / "ws", self._dir / "home"
        (ws / ".prismor").mkdir(parents=True)
        home.mkdir()
        shutil.copy(_HERE / "policy.yaml", ws / ".prismor" / "policy.yaml")
        self._journal = self._dir / "effects.jsonl"
        self._journal.touch()
        env = dict(os.environ, HOME=str(home), PRISMOR_HOME=str(home),
                   REG_EFFECT_JOURNAL=str(self._journal))
        env.pop("PRISMOR_AGENT_KEY", None)          # no control plane in this scope
        self._stderr = open(self._dir / "gateway.stderr", "w")
        self._proc = subprocess.Popen(
            [self._bin, "mcp-gateway", "serve", "--mode", "enforce",
             "--server", f"count={sys.executable} {_HERE / 'counter_server.py'}",
             "--workspace", str(ws)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._stderr,
            env=env, text=True, cwd=str(ws))
        self._rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                 "clientInfo": {"name": "reg-harness", "version": "0"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        names = [t["name"] for t in self._rpc("tools/list", {})["result"]["tools"]]
        if TOOL not in names:
            raise RuntimeError(f"gateway does not expose {TOOL}: {names}")

    def close(self):
        if self._proc is not None:
            try:
                self._proc.stdin.close()
                self._proc.wait(timeout=10)
            except Exception:
                self._proc.kill()
            self._stderr.close()
            self._proc = None
        if self._dir is not None:
            shutil.rmtree(self._dir, ignore_errors=True)
            self._dir = None

    def __del__(self):
        self.close()

    # -- MCP over stdio -----------------------------------------------------
    def _send(self, msg):
        self._proc.stdin.write(json.dumps(msg) + "\n")
        self._proc.stdin.flush()

    def _rpc(self, method, params):
        self._id += 1
        want = self._id
        self._send({"jsonrpc": "2.0", "id": want, "method": method, "params": params})
        while True:
            line = self._proc.stdout.readline()
            if not line:
                raise RuntimeError("gateway closed its output")
            msg = json.loads(line)
            if msg.get("id") == want:
                return msg

    # -- primitives ---------------------------------------------------------
    def evaluate(self, intent, *, principal, action_type, nonce=None):
        token = uuid.uuid4().hex
        reply = self._rpc("tools/call", {"name": TOOL, "arguments": {
            "token": token, "intent": _INTENT_ARG[intent]}})
        result = reply.get("result")
        if result is None:
            raise RuntimeError(f"protocol error from gateway: {reply.get('error')}")
        text = " ".join(c.get("text", "") for c in result.get("content", []))
        if not result.get("isError"):
            disposition = "PASS"
        elif "Blocked by Prismor" in text:
            rule = next((r for r in _RULE_DISPOSITION if f"(rule: {r})" in text), None)
            if rule is None:
                raise RuntimeError(f"blocked by a rule outside the test policy: {text[:160]}")
            disposition = _RULE_DISPOSITION[rule]
        else:
            raise RuntimeError(f"tool error that is not a Prismor refusal: {text[:160]}")
        return P.Decision(token, disposition, action_type, principal,
                          {"token": token, "gateway_text": text})

    def observed_effects(self, decision):
        count = 0
        for line in self._journal.read_text(encoding="utf-8").splitlines():
            if json.loads(line).get("token") == decision.raw["token"]:
                count += 1
        return count
