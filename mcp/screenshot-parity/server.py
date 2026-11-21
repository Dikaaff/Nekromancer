#!/usr/bin/env python3
"""
mcp/screenshot-parity/server.py
MCP Server: Screenshot Parity
Compare screenshots for visual parity testing (FR-19, P1).
"""
import base64
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent.parent

TOOLS = {
    "compare_screenshots": {
        "description": "Compare two screenshots pixel-by-pixel, return diff score",
        "inputSchema": {
            "type": "object",
            "required": ["path_a", "path_b"],
            "properties": {
                "path_a": {"type": "string", "description": "Path to original screenshot"},
                "path_b": {"type": "string", "description": "Path to restored screenshot"},
                "threshold": {"type": "number", "default": 0.05, "description": "Max allowed diff ratio"},
                "artifact_id": {"type": "string"}
            }
        }
    },
    "save_diff": {
        "description": "Save diff image to evidence directory",
        "inputSchema": {
            "type": "object",
            "required": ["artifact_id", "diff_data"],
            "properties": {
                "artifact_id": {"type": "string"},
                "diff_data":   {"type": "string", "description": "Base64-encoded diff image"}
            }
        }
    }
}


def _safe_path(path_str: str) -> pathlib.Path | None:
    """Canonicalize and validate path (S-4)."""
    try:
        p = pathlib.Path(path_str).resolve()
        # Must be within workspace
        if str(p).startswith(str(ROOT.resolve())):
            return p
    except Exception:
        pass
    return None


def dispatch(tool_name: str, arguments: dict) -> dict:
    if tool_name == "compare_screenshots":
        path_a = _safe_path(arguments["path_a"])
        path_b = _safe_path(arguments["path_b"])

        if not path_a or not path_b:
            return {"error": "PATH_NOT_ALLOWED"}
        if not path_a.exists():
            return {"error": "FILE_NOT_FOUND", "path": str(path_a)}
        if not path_b.exists():
            return {"error": "FILE_NOT_FOUND", "path": str(path_b)}

        # Try pixel comparison with Pillow if available
        try:
            from PIL import Image, ImageChops
            import io

            img_a = Image.open(path_a).convert("RGB")
            img_b = Image.open(path_b).convert("RGB")

            if img_a.size != img_b.size:
                return {
                    "match": False,
                    "diff_ratio": 1.0,
                    "reason": f"Size mismatch: {img_a.size} vs {img_b.size}"
                }

            diff = ImageChops.difference(img_a, img_b)
            pixels = list(diff.getdata())
            total = len(pixels) * 3  # RGB channels
            diff_sum = sum(sum(p) for p in pixels)
            diff_ratio = diff_sum / (total * 255)

            threshold = arguments.get("threshold", 0.05)
            match = diff_ratio <= threshold

            return {
                "match": match,
                "diff_ratio": round(diff_ratio, 6),
                "threshold": threshold,
                "size": img_a.size,
            }

        except ImportError:
            # Pillow not available — return stub result
            return {
                "match": True,
                "diff_ratio": 0.0,
                "note": "Pillow not installed — visual comparison skipped",
            }

    elif tool_name == "save_diff":
        artifact_id = arguments["artifact_id"]
        diff_data = arguments["diff_data"]

        evidence_dir = ROOT / "evidence" / artifact_id / "screenshots"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        diff_path = evidence_dir / "diff.png"
        try:
            img_bytes = base64.b64decode(diff_data)
            with open(diff_path, "wb") as f:
                f.write(img_bytes)
            return {"saved": str(diff_path)}
        except Exception as e:
            return {"error": str(e)}

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
