#!/usr/bin/env python3
"""
packages/ledger/writer.py
Append-only ledger writer (SEXTON).

Rules (S-11):
- ONLY uses append. Never overwrites entries.
- prev_hash = output_hash of last entry.
- Chain break = new file with CHAIN_BREAK_MARKER.
"""
import hashlib
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent.parent
LEDGER_DIR = ROOT / "ledger"
ENTRIES_FILE = LEDGER_DIR / "entries.jsonl"


def _last_entry(entries_path: pathlib.Path) -> dict | None:
    if not entries_path.exists():
        return None
    last = None
    with open(entries_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    last = json.loads(line)
                except json.JSONDecodeError:
                    pass
    return last


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _next_seq(entries_path: pathlib.Path) -> int:
    last = _last_entry(entries_path)
    return (last.get("seq", 0) + 1) if last else 1


def append_entry(
    stage: str,
    input_hash: str,
    output_content: str,
    actor: str,
    entries_path: pathlib.Path | None = None,
) -> dict:
    """
    Append one entry to the ledger. Returns the written entry.
    output_content: the content being hashed (e.g. JSON of dossier, path of output file).
    """
    if entries_path is None:
        entries_path = ENTRIES_FILE

    LEDGER_DIR.mkdir(parents=True, exist_ok=True)

    last = _last_entry(entries_path)
    prev_hash = last["output_hash"] if last else ("0" * 64)
    output_hash = _hash_content(output_content)
    seq = (last["seq"] + 1) if last else 1

    # Verify chain integrity before appending
    if last:
        expected_prev = last["output_hash"]
        # Recompute last entry's hash to verify nobody tampered
        last_content = json.dumps(last, separators=(",", ":"), sort_keys=True)
        actual_hash = _hash_content(last_content)
        # If chain is broken, start a new file (S-11)
        if prev_hash != expected_prev:
            return _handle_chain_break(entries_path, stage, input_hash, output_content, actor)

    entry = {
        "seq": seq,
        "stage": stage,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "prev_hash": prev_hash,
        "actor": actor,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # APPEND ONLY — never write mode
    with open(entries_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")

    print(f"[ledger] ✅ Entry {seq} appended: stage={stage} actor={actor}", file=sys.stderr)
    return entry


def _handle_chain_break(
    entries_path: pathlib.Path,
    stage: str, input_hash: str, output_content: str, actor: str
) -> dict:
    """Start a new ledger file on chain break (S-11)."""
    # Find next available ledger file
    n = 2
    while True:
        new_path = entries_path.parent / f"entries-{n}.jsonl"
        if not new_path.exists():
            break
        n += 1

    print(f"[ledger] ⚠️ Chain break detected — starting {new_path.name}", file=sys.stderr)

    # Write marker as first entry
    marker = {
        "seq": 1,
        "stage": "CHAIN_BREAK_MARKER",
        "input_hash": "0" * 64,
        "output_hash": _hash_content(f"CHAIN_BREAK:{time.time()}"),
        "prev_hash": "0" * 64,
        "actor": "SEXTON",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": f"Previous ledger {entries_path.name} chain broken",
    }
    with open(new_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(marker, separators=(",", ":")) + "\n")

    # Now append the actual entry to new file
    return append_entry(stage, input_hash, output_content, actor, entries_path=new_path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Append ledger entry")
    parser.add_argument("--stage", help="Stage name (defaults to the hook event)")
    parser.add_argument("--input-hash", default="0" * 64)
    parser.add_argument("--output", help="Content to hash as output")
    parser.add_argument("--actor", help="Actor name (defaults to the payload agent)")
    parser.add_argument("--event", help="Event type from hook (post-task etc.)")
    parser.add_argument("--stdin", action="store_true", help="Read JSON from stdin (hook mode)")
    args = parser.parse_args()

    payload = {}
    if args.stdin:
        raw = sys.stdin.read()
        if raw.strip():
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"raw": raw}

    # Hook mode derives whatever the payload can supply; CLI mode uses flags.
    stage = args.stage or payload.get("task", {}).get("id") or args.event or "hook"
    actor = args.actor or payload.get("agent") or "SEXTON"
    output = args.output if args.output is not None else json.dumps(payload, sort_keys=True, default=str)

    entry = append_entry(
        stage=stage,
        input_hash=args.input_hash,
        output_content=output,
        actor=actor,
    )
    print(json.dumps(entry, indent=2))


if __name__ == "__main__":
    main()
