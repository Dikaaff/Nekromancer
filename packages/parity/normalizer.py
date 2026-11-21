#!/usr/bin/env python3
"""
packages/parity/normalizer.py
Normalize traces before comparison.
Policy from resurrection-doctrine.md:
  - Ignore presentation differences
  - Ignore whitespace differences in string values
  - Ignore column order (unless schema specifies otherwise)
  - Normalize date formats
"""
import re
from copy import deepcopy

POLICY = {
    "ignore_presentation_differences": True,
    "ignore_whitespace_differences": True,
    "ignore_column_order": False,
    "date_format_normalize": True,
}

_DATE_PATTERNS = [
    (re.compile(r"^(\d{4})(\d{2})(\d{2})$"), r"\1-\2-\3"),          # YYYYMMDD → YYYY-MM-DD
    (re.compile(r"^(\d{2})/(\d{2})/(\d{4})$"), r"\3-\2-\1"),        # DD/MM/YYYY → YYYY-MM-DD
    (re.compile(r"^(\d{2})-(\d{2})-(\d{4})$"), r"\3-\2-\1"),        # DD-MM-YYYY → YYYY-MM-DD
]


def _normalize_date(value: str) -> str:
    for pattern, replacement in _DATE_PATTERNS:
        m = pattern.match(value.strip())
        if m:
            return pattern.sub(replacement, value.strip())
    return value


def _normalize_value(value: object) -> object:
    """Normalize a single field value."""
    if not isinstance(value, str):
        return value

    result = value

    if POLICY["ignore_whitespace_differences"]:
        result = re.sub(r"\s+", " ", result).strip()

    if POLICY["date_format_normalize"]:
        result = _normalize_date(result)

    return result


def normalize_record(record: dict) -> dict:
    """Normalize a single record dict."""
    normalized = {}
    for key, value in record.items():
        norm_key = key.strip() if isinstance(key, str) else key
        normalized[norm_key] = _normalize_value(value)
    return normalized


def normalize_trace(trace: list[dict]) -> list[dict]:
    """
    Normalize a trace (list of state snapshots).
    Each snapshot is a dict with 'action', 'state', etc.
    """
    normalized = []
    for step in trace:
        norm_step = deepcopy(step)

        # Normalize state records
        if "state" in norm_step and isinstance(norm_step["state"], list):
            norm_step["state"] = [normalize_record(r) for r in norm_step["state"]]
        elif "state" in norm_step and isinstance(norm_step["state"], dict):
            norm_step["state"] = normalize_record(norm_step["state"])

        # Presentation fields to ignore
        if POLICY["ignore_presentation_differences"]:
            for key in ("style", "css", "font", "color", "padding", "margin"):
                norm_step.pop(key, None)

        normalized.append(norm_step)
    return normalized


def compare_traces(trace_a: list[dict], trace_b: list[dict]) -> dict:
    """
    Compare two normalized traces.
    Returns {
        "match": bool,
        "diff_steps": [{"step": N, "a": ..., "b": ...}],
        "policy": POLICY
    }
    """
    norm_a = normalize_trace(trace_a)
    norm_b = normalize_trace(trace_b)

    diff_steps = []
    max_len = max(len(norm_a), len(norm_b))

    for i in range(max_len):
        step_a = norm_a[i] if i < len(norm_a) else None
        step_b = norm_b[i] if i < len(norm_b) else None

        if step_a != step_b:
            diff_steps.append({"step": i, "original": step_a, "restored": step_b})

    return {
        "match": len(diff_steps) == 0,
        "diff_steps": diff_steps,
        "policy": POLICY,
    }


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) != 3:
        print("Usage: normalizer.py <trace_a.json> <trace_b.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        a = json.load(f)
    with open(sys.argv[2]) as f:
        b = json.load(f)
    result = compare_traces(a, b)
    print(json.dumps(result, indent=2))
