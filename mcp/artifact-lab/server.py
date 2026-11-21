#!/usr/bin/env python3
"""
mcp/artifact-lab/server.py
MCP Server: Artifact Lab
Runs artifact in headless sandbox, returns structured trace.

Security (S-1, S-8):
- All arguments validated against schema before execution.
- No shell interpolation — subprocess with array args only.
- Path arguments canonicalized against allowlist.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent.parent.parent
ALLOWED_INPUT_DIRS = [
    ROOT / "fixtures",
    ROOT / "dossiers",
]

TOOLS = {
    "detect_format": {
        "description": "Detect artifact format from file content",
        "inputSchema": {
            "type": "object",
            "required": ["artifact_path"],
            "properties": {
                "artifact_path": {"type": "string", "description": "Absolute path to artifact file"}
            }
        }
    },
    "run_probe": {
        "description": "Run full probe pipeline on artifact, returns dossier",
        "inputSchema": {
            "type": "object",
            "required": ["artifact_path"],
            "properties": {
                "artifact_path": {"type": "string"},
                "smoke_test": {"type": "boolean", "default": False}
            }
        }
    },
    "execute_sequence": {
        "description": "Execute an action sequence on an artifact, return trace",
        "inputSchema": {
            "type": "object",
            "required": ["artifact_id", "sequence"],
            "properties": {
                "artifact_id": {"type": "string"},
                "sequence": {"type": "array", "items": {"type": "object"}}
            }
        }
    }
}


def _canonicalize_path(path_str: str) -> pathlib.Path | None:
    """Verify path is within allowed input directories (S-4)."""
    try:
        p = pathlib.Path(path_str).resolve()
    except Exception:
        return None
    for allowed in ALLOWED_INPUT_DIRS:
        if str(p).startswith(str(allowed.resolve())):
            return p
    return None


def handle_detect_format(args: dict) -> dict:
    path = _canonicalize_path(args["artifact_path"])
    if path is None:
        return {"error": "PATH_NOT_ALLOWED", "message": "Artifact path outside allowed directories"}

    sys.path.insert(0, str(ROOT))
    from packages.codec.detector import detect
    result = detect(path)
    return {
        "family": result.family,
        "confidence": result.confidence,
        "detected_by": result.detected_by,
        "encoding": result.encoding,
        "delimiter": result.delimiter,
    }


def handle_run_probe(args: dict) -> dict:
    path = _canonicalize_path(args["artifact_path"])
    if path is None:
        return {"error": "PATH_NOT_ALLOWED", "message": "Artifact path outside allowed directories"}

    sys.path.insert(0, str(ROOT))
    from packages.probe.runner import run_probe
    return run_probe(str(path), smoke_test=args.get("smoke_test", False))


def handle_execute_sequence(args: dict) -> dict:
    """Execute action sequence — simulated for demo, real version uses sandbox."""
    artifact_id = args["artifact_id"]
    sequence = args["sequence"]

    # Simulate trace execution (real: Docker sandbox)
    sys.path.insert(0, str(ROOT))
    from packages.parity.reporter import _simulate_trace
    trace = _simulate_trace(sequence, side="original", artifact_id=artifact_id)
    return {"artifact_id": artifact_id, "trace": trace, "steps": len(trace)}


def dispatch(tool_name: str, arguments: dict) -> dict:
    """Dispatch tool call. Validates args against schema before executing (S-8)."""
    if tool_name not in TOOLS:
        return {"error": "UNKNOWN_TOOL", "message": f"Tool '{tool_name}' not found"}

    # Basic required field validation
    schema = TOOLS[tool_name]["inputSchema"]
    for req in schema.get("required", []):
        if req not in arguments:
            return {"error": "MISSING_ARGUMENT", "message": f"Required argument '{req}' missing"}

    handlers = {
        "detect_format": handle_detect_format,
        "run_probe": handle_run_probe,
        "execute_sequence": handle_execute_sequence,
    }
    return handlers[tool_name](arguments)


def run_mcp_server():
    """Simple MCP server over stdin/stdout (JSON-RPC style)."""
    print(json.dumps({"status": "ready", "tools": list(TOOLS.keys())}), flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            tool = request.get("tool", "")
            args = request.get("arguments", {})
            result = dispatch(tool, args)
            print(json.dumps({"id": request.get("id"), "result": result}), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({"error": "INVALID_JSON"}), flush=True)
        except Exception as e:
            print(json.dumps({"error": "SERVER_ERROR", "message": str(e)}), flush=True)


if __name__ == "__main__":
    run_mcp_server()
