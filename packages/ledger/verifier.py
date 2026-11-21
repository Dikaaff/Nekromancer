#!/usr/bin/env python3
"""
packages/ledger/verifier.py
Verify ledger chain integrity (S-11).
Reads entries.jsonl, checks prev_hash chain, reports breaks.
"""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent.parent
LEDGER_DIR = ROOT / "ledger"


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def verify_chain(entries_path: pathlib.Path) -> dict:
    """
    Returns {
        "valid": bool,
        "entries_count": int,
        "breaks": [{"seq": N, "reason": "..."}]
    }
    """
    if not entries_path.exists():
        return {"valid": False, "entries_count": 0, "breaks": [{"seq": 0, "reason": "File not found"}]}

    entries = []
    with open(entries_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                return {"valid": False, "entries_count": i, "breaks": [{"seq": i, "reason": f"JSON error: {e}"}]}

    breaks = []
    prev_output_hash = "0" * 64

    for entry in entries:
        seq = entry.get("seq", "?")

        # Skip genesis and chain break markers
        if entry.get("stage") in ("GENESIS", "CHAIN_BREAK_MARKER"):
            prev_output_hash = entry.get("output_hash", "0" * 64)
            continue

        expected_prev = prev_output_hash
        actual_prev = entry.get("prev_hash", "")

        if actual_prev != expected_prev:
            breaks.append({
                "seq": seq,
                "reason": f"prev_hash mismatch: expected {expected_prev[:16]}… got {actual_prev[:16]}…"
            })

        prev_output_hash = entry.get("output_hash", "")

    return {
        "valid": len(breaks) == 0,
        "entries_count": len(entries),
        "breaks": breaks,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Verify ledger chain integrity")
    parser.add_argument("--ledger", default=str(LEDGER_DIR / "entries.jsonl"))
    args = parser.parse_args()

    result = verify_chain(pathlib.Path(args.ledger))
    print(json.dumps(result, indent=2))

    if not result["valid"]:
        print(f"❌ Chain BROKEN: {len(result['breaks'])} break(s)", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"✅ Chain VALID: {result['entries_count']} entries", file=sys.stderr)


if __name__ == "__main__":
    main()
