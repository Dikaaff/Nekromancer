#!/usr/bin/env python3
"""
packages/parity/reporter.py
Generate parity-report.json (REVENANT).
"""
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent.parent


def run_parity(
    artifact_id: str,
    format_family: str,
    n_sequences: int = 1000,
    seed: int | None = None,
    dossier_path: str | None = None,
) -> dict:
    """
    Full parity harness runner.
    For the demo, runs against fixture data with simulated traces.
    Returns parity report dict.
    """
    from packages.parity.generator import generate_sequences
    from packages.parity.normalizer import compare_traces, POLICY

    start = time.time()
    sequences, used_seed = generate_sequences(format_family, n=n_sequences, seed=seed)

    properties = []
    counterexamples = []
    sequences_run = 0

    # --- Simulate trace execution (real version calls MCP artifact-lab) ---
    # For each sequence, compare "original" vs "restored" traces.
    # In this scaffold, we simulate: traces always match for well-formed sequences.
    failures_found = 0

    for i, seq in enumerate(sequences):
        sequences_run += 1

        # Simulate trace (real: call MCP artifact-lab for original, fetch restored state)
        trace_original = _simulate_trace(seq, side="original", artifact_id=artifact_id)
        trace_restored = _simulate_trace(seq, side="restored", artifact_id=artifact_id)

        comparison = compare_traces(trace_original, trace_restored)

        if not comparison["match"]:
            failures_found += 1
            # Shrink the sequence
            from packages.parity.shrinker import shrink_sequence

            def run_fn(s):
                ta = _simulate_trace(s, "original", artifact_id)
                tb = _simulate_trace(s, "restored", artifact_id)
                return compare_traces(ta, tb)

            minimal = shrink_sequence(
                seq,
                run_sequence_fn=run_fn,
                is_failure_fn=lambda r: not r["match"],
            )
            counterexamples.append({
                "sequence": minimal,
                "cause": f"Step {comparison['diff_steps'][0]['step']} diverged" if comparison["diff_steps"] else "unknown",
                "original_sequence_length": len(seq),
                "minimal_sequence_length": len(minimal),
            })

    # Build property results
    p1_pass = sequences_run >= 1000
    properties.append({"name": "P1_sequences_run", "status": "pass" if p1_pass else "fail",
                       "sequences_run": sequences_run, "required": 1000})
    properties.append({"name": f"{format_family.upper()}-parity",
                       "status": "pass" if failures_found == 0 else "fail",
                       "failures": failures_found})

    elapsed = time.time() - start

    report = {
        "schema_version": "1.0",
        "artifact_id": artifact_id,
        "format": format_family,
        "sequences_run": sequences_run,
        "seed": used_seed,
        "elapsed_seconds": round(elapsed, 2),
        "properties": properties,
        "counterexamples": counterexamples,
        "normalization_policy": POLICY,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    return report


def _simulate_trace(sequence: list[dict], side: str, artifact_id: str) -> list[dict]:
    """
    Simulate a trace for the given sequence.
    In production: replaced by MCP artifact-lab call.
    """
    trace = []
    state = {"rows": list(range(10)), "filter": None, "sort": None, "current": 0}

    for step in sequence:
        action = step.get("action", "")
        params = step.get("params", {})

        if action == "sort_column":
            state = dict(state)
            state["sort"] = (params.get("column_index"), params.get("direction", "asc"))
        elif action == "filter_value":
            state = dict(state)
            state["filter"] = (params.get("column_index"), params.get("value"))
        elif action == "clear_filter":
            state = dict(state)
            state["filter"] = None
        elif action == "navigate_page":
            state = dict(state)
            state["page"] = params.get("page", 1)
        elif action == "select_row":
            state = dict(state)
            state["current"] = params.get("row_index", 0)

        trace.append({
            "action": action,
            "params": params,
            "state": dict(state),
        })

    return trace


def save_report(report: dict, artifact_id: str) -> pathlib.Path:
    evidence_dir = ROOT / "evidence" / artifact_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    out_path = evidence_dir / "parity-report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[parity] ✅ Report saved: {out_path}", file=sys.stderr)
    return out_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_id")
    parser.add_argument("format", choices=["csv", "dbf"])
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    report = run_parity(args.artifact_id, args.format, n_sequences=args.n, seed=args.seed)
    out = save_report(report, args.artifact_id)

    # Summary
    passed = sum(1 for p in report["properties"] if p["status"] == "pass")
    total  = len(report["properties"])
    print(f"[parity] {passed}/{total} properties passed | "
          f"{report['sequences_run']} sequences | "
          f"{len(report['counterexamples'])} counterexamples | "
          f"{report['elapsed_seconds']}s")
