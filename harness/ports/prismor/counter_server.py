#!/usr/bin/env python3
"""Harmless, countable MCP tool for the effect journal.

A stdio MCP server with one tool, `record`. Every call that actually reaches
this process appends one line to the journal named by REG_EFFECT_JOURNAL.
The journal is owned by the test controller: the runtime under test never
writes to it, so a line in it is an effect observed independently of the
runtime's own account of what happened.

Standard library only.
"""
import json
import os
import sys
import time

JOURNAL = os.environ["REG_EFFECT_JOURNAL"]
TOOL = {
    "name": "record",
    "description": "Append one line to the test journal.",
    "inputSchema": {
        "type": "object",
        "properties": {"token": {"type": "string"}, "intent": {"type": "string"}},
        "required": ["token"],
    },
}


def reply(req_id, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": req_id}
    msg.update({"error": error} if error else {"result": result})
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        req = json.loads(line)
    except ValueError:
        continue
    method, req_id = req.get("method"), req.get("id")
    if req_id is None:
        continue                                   # notification
    if method == "initialize":
        reply(req_id, {"protocolVersion": req.get("params", {}).get("protocolVersion", "2024-11-05"),
                       "capabilities": {"tools": {}},
                       "serverInfo": {"name": "reg-effect-counter", "version": "0.1.0"}})
    elif method == "tools/list":
        reply(req_id, {"tools": [TOOL]})
    elif method == "tools/call":
        args = req.get("params", {}).get("arguments") or {}
        with open(JOURNAL, "a", encoding="utf-8") as f:
            f.write(json.dumps({"token": args.get("token"), "intent": args.get("intent"),
                                "at": time.time()}) + "\n")
        reply(req_id, {"content": [{"type": "text", "text": "recorded"}], "isError": False})
    elif method == "ping":
        reply(req_id, {})
    else:
        reply(req_id, error={"code": -32601, "message": f"method not found: {method}"})
