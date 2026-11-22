#!/usr/bin/env python3
"""
mcp/crew-bridge/budget.py
Credit-budget guard for the budget-alert Kiro hook (PostToolUse).

The hook receives Kiro's event context as JSON on stdin. When the payload
exposes a credit figure we accumulate it; when it does not, we only re-check
the running total. State lives in .kiro/state/budget.json (git-ignored).

Exit codes (Kiro hook semantics):
  0  under budget
  1  error while reading state (treated as a hook error, not a block)
  2  hard stop — the crew must be killed (>= 400 credits)
"""
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent.parent
STATE_PATH = ROOT / ".kiro" / "state" / "budget.json"

WARN_CREDITS = 300
STOP_CREDITS = 400


def _extract_credits(payload: dict) -> float:
    """Pull a credit delta out of a Kiro hook payload, if one is present."""
    candidates = [
        payload.get("credits"),
        payload.get("usage", {}).get("credits") if isinstance(payload.get("usage"), dict) else None,
        payload.get("tool_response", {}).get("credits") if isinstance(payload.get("tool_response"), dict) else None,
        payload.get("tool_result", {}).get("credits") if isinstance(payload.get("tool_result"), dict) else None,
    ]
    for value in candidates:
        if isinstance(value, (int, float)):
            return float(value)
    return 0.0


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {"credits_used": 0.0, "tool_calls": 0}
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"credits_used": 0.0, "tool_calls": 0}
    state.setdefault("credits_used", 0.0)
    state.setdefault("tool_calls", 0)
    return state


def _save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def main() -> int:
    raw = sys.stdin.read() if "--stdin" in sys.argv else ""
    payload = {}
    if raw.strip():
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {}

    state = _load_state()
    state["tool_calls"] += 1
    state["credits_used"] += _extract_credits(payload)
    state["updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _save_state(state)

    used = float(state["credits_used"])
    print(f"[budget] credits_used={used:.1f} tool_calls={state['tool_calls']}")

    if used >= STOP_CREDITS:
        print(
            f"[budget] HARD STOP — {used:.1f} >= {STOP_CREDITS} credits. "
            "Kill every crew session before continuing.",
            file=sys.stderr,
        )
        return 2

    if used >= WARN_CREDITS:
        print(f"[budget] WARNING — {used:.1f} >= {WARN_CREDITS} credits.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
