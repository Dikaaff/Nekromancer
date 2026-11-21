#!/usr/bin/env python3
"""
mcp/provenance-ledger/server.py
MCP Server: Provenance Ledger
Read and verify the ledger chain hash.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

TOOLS = {
    "verify_chain": {
        "description": "Verify ledger chain integrity",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ledger_path": {"type": "string"}
            }
        }
    },
    "get_entries": {
        "description": "Get ledger entries",
        "inputSchema": {
            "type": "object",
            "properties": {
                "artifact_id": {"type": "string"},
                "limit": {"type": "integer", "default": 50}
            }
        }
    },
    "append_entry": {
        "description": "Append a new ledger entry",
        "inputSchema": {
            "type": "object",
            "required": ["stage", "output_content", "actor"],
            "properties": {
                "stage":          {"type": "string"},
                "input_hash":     {"type": "string"},
                "output_content": {"type": "string"},
                "actor":          {"type": "string"}
            }
        }
    }
}


def dispatch(tool_name: str, arguments: dict) -> dict:
    from packages.ledger.writer import append_entry
    from packages.ledger.verifier import verify_chain

    ledger_dir = ROOT / "ledger"
    default_entries = ledger_dir / "entries.jsonl"

    if tool_name == "verify_chain":
        p = pathlib.Path(arguments.get("ledger_path", str(default_entries)))
        return verify_chain(p)

    elif tool_name == "get_entries":
        entries_path = default_entries
        if not entries_path.exists():
            return {"entries": [], "count": 0}
        entries = []
        with open(entries_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass
        limit = arguments.get("limit", 50)
        return {"entries": entries[-limit:], "count": len(entries)}

    elif tool_name == "append_entry":
        entry = append_entry(
            stage=arguments["stage"],
            input_hash=arguments.get("input_hash", "0" * 64),
            output_content=arguments["output_content"],
            actor=arguments["actor"],
        )
        return entry

    return {"error": "UNKNOWN_TOOL"}


def run_mcp_server():
    print(json.dumps({"status": "ready", "tools": list(TOOLS.keys())}), flush=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            result = dispatch(req.get("tool", ""), req.get("arguments", {}))
            print(json.dumps({"id": req.get("id"), "result": result}), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)


if __name__ == "__main__":
    run_mcp_server()
