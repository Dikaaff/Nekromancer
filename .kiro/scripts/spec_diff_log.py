#!/usr/bin/env python3
"""
.kiro/scripts/spec_diff_log.py
Run on session Stop: generate changelog from spec task diffs.
"""
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent.parent

def main():
    # Get git diff of spec files
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--", ".kiro/specs/"],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        changed_specs = [f for f in result.stdout.strip().split("\n") if f]
    except Exception:
        changed_specs = []

    if not changed_specs:
        print("[spec-diff] No spec changes in this session")
        return

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "changed_specs": changed_specs,
        "suggested_commit": f"spec: update {', '.join(pathlib.Path(s).stem for s in changed_specs[:3])}",
    }

    print(f"[spec-diff] {len(changed_specs)} spec file(s) changed:")
    for s in changed_specs:
        print(f"  - {s}")
    print(f"[spec-diff] Suggested commit: {summary['suggested_commit']}")

    # Append to journal
    journal_path = ROOT / "KIRO_JOURNAL.md"
    if journal_path.exists():
        with open(journal_path, "a", encoding="utf-8") as f:
            f.write(f"\n## Auto-log {summary['timestamp']}\n")
            f.write(f"Changed specs: {', '.join(changed_specs)}\n")
            f.write(f"Suggested commit: `{summary['suggested_commit']}`\n")


if __name__ == "__main__":
    main()
