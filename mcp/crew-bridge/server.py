#!/usr/bin/env python3
"""
mcp/crew-bridge/server.py
MCP Server: Crew Bridge
Orchestrate pipeline runs, manage gates, budget tracking.
"""
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# In-memory run state (persisted to runs.json)
_runs: dict = {}
_budget_per_run: dict = {}

BUDGET_WARN  = 300
BUDGET_HARD  = 400

TOOLS = {
    "start_run": {
        "description": "Start a new pipeline run for an artifact",
        "inputSchema": {
            "type": "object",
            "required": ["artifact_path"],
            "properties": {
                "artifact_path": {"type": "string"}
            }
        }
    },
    "get_run_status": {
        "description": "Get status of a pipeline run",
        "inputSchema": {
            "type": "object",
            "required": ["run_id"],
            "properties": {"run_id": {"type": "string"}}
        }
    },
    "approve_run": {
        "description": "Approve Gate 2 — allows commit",
        "inputSchema": {
            "type": "object",
            "required": ["run_id"],
            "properties": {"run_id": {"type": "string"}}
        }
    },
    "reject_run": {
        "description": "Reject Gate 2 — marks run as rejected",
        "inputSchema": {
            "type": "object",
            "required": ["run_id"],
            "properties": {
                "run_id": {"type": "string"},
                "reason": {"type": "string"}
            }
        }
    },
    "track_credits": {
        "description": "Track credit usage for a run",
        "inputSchema": {
            "type": "object",
            "required": ["run_id", "credits_used"],
            "properties": {
                "run_id":       {"type": "string"},
                "credits_used": {"type": "number"}
            }
        }
    },
    "list_runs": {
        "description": "List all pipeline runs",
        "inputSchema": {"type": "object", "properties": {}}
    }
}


def _save_runs():
    """Persist run state to Forge data directory."""
    out = ROOT / "apps" / "forge" / "data" / "runs.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"runs": list(_runs.values())}, f, indent=2)


def dispatch(tool_name: str, arguments: dict) -> dict:
    if tool_name == "start_run":
        import hashlib
        path = arguments["artifact_path"]
        run_id = hashlib.sha256(f"{path}{time.time()}".encode()).hexdigest()[:16]
        _runs[run_id] = {
            "artifact_id": run_id,
            "name": pathlib.Path(path).name,
            "artifact_path": path,
            "status": "pending",
            "format": "unknown",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "restored_path": f"../restored/{run_id}/index.html",
            "parity_path": f"../restored/{run_id}/parity-report.json",
        }
        _budget_per_run[run_id] = 0
        _save_runs()
        return {"run_id": run_id, "status": "pending"}

    elif tool_name == "get_run_status":
        run = _runs.get(arguments["run_id"])
        if not run:
            return {"error": "RUN_NOT_FOUND"}
        return {**run, "credits_used": _budget_per_run.get(arguments["run_id"], 0)}

    elif tool_name == "approve_run":
        run_id = arguments["run_id"]
        if run_id not in _runs:
            return {"error": "RUN_NOT_FOUND"}
        _runs[run_id]["status"] = "done"
        _runs[run_id]["approved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _save_runs()
        return {"run_id": run_id, "status": "done"}

    elif tool_name == "reject_run":
        run_id = arguments["run_id"]
        if run_id not in _runs:
            return {"error": "RUN_NOT_FOUND"}
        _runs[run_id]["status"] = "failed"
        _runs[run_id]["rejection_reason"] = arguments.get("reason", "rejected")
        _save_runs()
        return {"run_id": run_id, "status": "failed"}

    elif tool_name == "track_credits":
        run_id = arguments["run_id"]
        credits = arguments["credits_used"]
        _budget_per_run[run_id] = _budget_per_run.get(run_id, 0) + credits
        total = _budget_per_run[run_id]

        if total > BUDGET_HARD:
            if run_id in _runs:
                _runs[run_id]["status"] = "failed"
                _runs[run_id]["failure_reason"] = f"BUDGET_EXCEEDED: {total} credits"
            _save_runs()
            return {"run_id": run_id, "credits_total": total,
                    "action": "KILL_ALL", "message": f"Hard limit exceeded ({total} > {BUDGET_HARD})"}

        if total > BUDGET_WARN:
            return {"run_id": run_id, "credits_total": total,
                    "action": "STOP_RUN", "message": f"Budget warning exceeded ({total} > {BUDGET_WARN})"}

        return {"run_id": run_id, "credits_total": total, "action": "continue"}

    elif tool_name == "list_runs":
        return {"runs": list(_runs.values())}

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
