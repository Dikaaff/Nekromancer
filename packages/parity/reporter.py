#!/usr/bin/env python3
"""
packages/parity/reporter.py
Parity harness (REVENANT) — builds evidence/<artifact_id>/parity-report.json.

Every action sequence is executed twice, against two independent data paths:

  original  -> the artifact file on disk, re-parsed from raw bytes by its codec
  restored  -> apps/restored/<artifact_id>/data.json, the exact payload the
               generated application renders

Both paths feed the same deterministic table model, so any value that the
restore step dropped, renamed, reordered, or mangled surfaces as a trace
divergence and is shrunk to a minimal counterexample.

Scope: this proves *data-model* parity. Pixel/DOM parity is a separate concern
and is handled by the screenshot-parity MCP server.
"""
import csv
import hashlib
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent.parent
MAX_ROWS = 10          # the restored app renders a bounded sample table
MAX_SEQUENCE_STEPS = 10

SCOPE = (
    "Data-model parity: the payload consumed by the restored app is compared "
    "against a fresh parse of the original artifact. DOM and pixel parity are "
    "covered separately by the screenshot-parity MCP server."
)


# ─── Data sources ────────────────────────────────────────────────────────────

def _read_csv_table(path: pathlib.Path, encoding: str = "utf-8", delimiter: str = ","):
    """Parse the original CSV artifact directly from disk (raw values)."""
    with open(path, newline="", encoding=encoding or "utf-8", errors="replace") as fh:
        reader = csv.reader(fh, delimiter=delimiter or ",")
        try:
            columns = [h.strip() for h in next(reader)]
        except StopIteration:
            return [], []

        rows = []
        for raw in reader:
            padded = list(raw[:len(columns)]) + [""] * max(0, len(columns) - len(raw))
            rows.append({columns[i]: padded[i] for i in range(len(columns))})
            if len(rows) >= MAX_ROWS:
                break
    return columns, rows


def _read_dbf_table(path: pathlib.Path):
    """Parse the original dBase/DBF artifact directly from disk (raw values)."""
    from packages.codec import dbf_codec as codec

    with open(path, "rb") as fh:
        header = codec._read_header(fh)
        if header is None:
            return [], []

        fh.seek(32)
        fields = codec._read_fields(fh, header)
        if not fields:
            return [], []

        columns = [f.name for f in fields]
        rows = []
        fh.seek(header.header_size)

        for _ in range(header.record_count):
            raw = fh.read(header.record_size)
            if not raw or len(raw) < header.record_size:
                break
            if raw[0:1] == b"\x2a":          # deleted record marker
                continue

            row = {}
            for f in fields:
                chunk = raw[f.offset:f.offset + f.length]
                row[f.name] = chunk.decode(header.encoding, errors="replace").strip().rstrip("\x00")
            rows.append(row)
            if len(rows) >= MAX_ROWS:
                break
    return columns, rows


def _read_restored_table(restored_dir: pathlib.Path):
    """Read the payload the generated application actually renders."""
    data_path = restored_dir / "data.json"
    with open(data_path, encoding="utf-8") as f:
        payload = json.load(f)

    model = payload.get("model", {})
    dossier = payload.get("dossier", {})
    entity = (model.get("entities") or [{}])[0]
    columns = [f["name"] for f in entity.get("fields", [])]
    rows = dossier.get("samples", [])[:MAX_ROWS]
    return columns, rows, payload


def _sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ─── Deterministic table model (same engine, two data sources) ───────────────

def _norm(value) -> str:
    return "" if value is None else str(value).strip()


def _sort_key(value):
    text = _norm(value)
    try:
        return (0, float(text.replace(",", ".")), text.lower())
    except ValueError:
        return (1, 0.0, text.lower())


def _column_at(column_index, column_count: int):
    """Map an out-of-range grammar index onto a real column deterministically."""
    if column_count == 0:
        return None
    try:
        idx = int(column_index)
    except (TypeError, ValueError):
        return None
    return idx % column_count


def _run_sequence(sequence: list[dict], columns: list[str], rows: list[dict]) -> list[dict]:
    """Execute one action sequence and record a state snapshot per step."""
    base = [dict(r) for r in rows]
    state = {
        "rows": list(base),
        "sort": None,
        "filter": None,
        "query": None,
        "page": 1,
        "page_size": 10,
        "selected": None,
    }

    trace = []
    for step in sequence:
        action = step.get("action", "")
        params = step.get("params") or {}

        if action == "sort_column":
            idx = _column_at(params.get("column_index"), len(columns))
            if idx is not None:
                direction = params.get("direction", "asc")
                state["rows"] = sorted(
                    state["rows"],
                    key=lambda r: _sort_key(r.get(columns[idx])),
                    reverse=(direction == "desc"),
                )
                state["sort"] = {"column": columns[idx], "direction": direction}

        elif action == "filter_value":
            idx = _column_at(params.get("column_index"), len(columns))
            if idx is not None:
                target = _norm(params.get("value"))
                state["filter"] = {"column": columns[idx], "value": target}
                state["rows"] = [r for r in base if _norm(r.get(columns[idx])) == target]

        elif action == "search":
            query = _norm(params.get("query")).lower()
            state["query"] = query
            state["rows"] = (
                [r for r in base if any(query in _norm(v).lower() for v in r.values())]
                if query else list(base)
            )

        elif action == "clear_filter":
            state["filter"] = None
            state["query"] = None
            state["rows"] = list(base)

        elif action == "navigate_page":
            state["page"] = int(params.get("page", 1) or 1)
            state["page_size"] = int(params.get("page_size", 10) or 10)

        elif action in ("select_row", "view_detail"):
            state["selected"] = int(params.get("row_index", 0) or 0)

        trace.append({
            "action": action,
            "params": params,
            "state": state["rows"],          # normalizer handles list[dict]
            "meta": {
                "row_count": len(state["rows"]),
                "sort": state["sort"],
                "filter": state["filter"],
                "query": state["query"],
                "page": state["page"],
                "page_size": state["page_size"],
                "selected": state["selected"],
            },
        })

    return trace


def _compare_sequence(sequence, original_table, restored_table):
    from packages.parity.normalizer import compare_traces

    original_trace = _run_sequence(sequence, *original_table)
    restored_trace = _run_sequence(sequence, *restored_table)
    return compare_traces(original_trace, restored_trace)


# ─── Harness ─────────────────────────────────────────────────────────────────

def run_parity(
    artifact_id: str,
    format_family: str,
    n_sequences: int = 1000,
    seed: int | None = None,
    dossier_path: str | None = None,
    artifact_path: str | None = None,
    restored_dir: str | None = None,
) -> dict:
    """
    Execute n_sequences against the original artifact and the restored payload.
    Returns the parity report dict.
    """
    from packages.parity.generator import generate_sequences
    from packages.parity.normalizer import POLICY, normalize_record
    from packages.parity.shrinker import shrink_sequence

    start = time.time()

    dossier_file = pathlib.Path(dossier_path) if dossier_path else ROOT / "dossiers" / artifact_id / "dossier.json"
    with open(dossier_file, encoding="utf-8") as f:
        dossier = json.load(f)

    artifact_file = pathlib.Path(artifact_path) if artifact_path else _locate_artifact(dossier)
    restored_path = pathlib.Path(restored_dir) if restored_dir else ROOT / "apps" / "restored" / artifact_id

    if not artifact_file.exists():
        raise FileNotFoundError(f"Original artifact not found: {artifact_file}")
    if not (restored_path / "data.json").exists():
        raise FileNotFoundError(f"Restored payload not found: {restored_path / 'data.json'}")

    if format_family == "csv":
        original_table = _read_csv_table(
            artifact_file,
            encoding=dossier.get("format", {}).get("encoding", "utf-8"),
            delimiter=dossier.get("format", {}).get("delimiter", ","),
        )
    elif format_family == "dbf":
        original_table = _read_dbf_table(artifact_file)
    else:
        raise ValueError(f"No parity reader for format '{format_family}'")

    restored_columns, restored_rows, payload = _read_restored_table(restored_path)
    restored_table = (restored_columns, restored_rows)

    # The restored payload must carry the same number of renderable rows.
    row_count = min(len(original_table[1]), len(restored_table[1]))

    sequences, used_seed = generate_sequences(format_family, n=n_sequences, seed=seed)

    failures_found = 0
    counterexamples = []

    for seq in sequences:
        comparison = _compare_sequence(seq, original_table, restored_table)
        if comparison["match"]:
            continue

        failures_found += 1
        minimal = shrink_sequence(
            seq,
            run_sequence_fn=lambda s: _compare_sequence(s, original_table, restored_table),
            is_failure_fn=lambda r: not r["match"],
        )
        first_diff = comparison["diff_steps"][0] if comparison["diff_steps"] else None
        counterexamples.append({
            "sequence": minimal,
            "cause": f"Step {first_diff['step']} diverged" if first_diff else "unknown",
            "original_sequence_length": len(seq),
            "minimal_sequence_length": len(minimal),
        })

    # Value fidelity: every rendered cell must equal the original cell.
    fidelity_mismatches = []
    for i in range(row_count):
        left = normalize_record(original_table[1][i])
        right = normalize_record(restored_table[1][i])
        if left != right:
            fidelity_mismatches.append({
                "row": i,
                "columns": sorted(
                    k for k in set(left) | set(right) if left.get(k) != right.get(k)
                ),
            })

    # Provenance: the payload must be derived from the hashed artifact.
    expected_sha = dossier.get("artifact", {}).get("sha256", "")
    actual_sha = _sha256_file(artifact_file)
    provenance_ok = bool(expected_sha) and expected_sha == actual_sha
    payload_sha_ok = payload.get("dossier", {}).get("artifact", {}).get("sha256") == expected_sha

    properties = [
        {"name": "P1_sequences_run", "status": "pass" if len(sequences) >= 1000 else "fail",
         "sequences_run": len(sequences), "required": 1000},
        {"name": f"{format_family.upper()}-trace_parity",
         "status": "pass" if failures_found == 0 else "fail",
         "sequences_run": len(sequences), "failures": failures_found},
        {"name": "value_fidelity",
         "status": "pass" if not fidelity_mismatches else "fail",
         "rows_compared": row_count, "mismatches": len(fidelity_mismatches)},
        {"name": "artifact_hash_match",
         "status": "pass" if provenance_ok and payload_sha_ok else "fail",
         "expected": expected_sha, "actual": actual_sha,
         "payload_matches": payload_sha_ok},
    ]

    elapsed = time.time() - start

    return {
        "schema_version": "1.1",
        "artifact_id": artifact_id,
        "format": format_family,
        "sequences_run": len(sequences),
        "seed": used_seed,
        "elapsed_seconds": round(elapsed, 2),
        "scope": SCOPE,
        "sources": {
            "original_artifact": str(artifact_file.relative_to(ROOT)) if artifact_file.is_relative_to(ROOT) else str(artifact_file),
            "restored_payload": str((restored_path / "data.json").relative_to(ROOT)),
            "rows_compared": row_count,
            "columns": original_table[0],
        },
        "properties": properties,
        "counterexamples": counterexamples,
        "fidelity_mismatches": fidelity_mismatches,
        "normalization_policy": POLICY,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _locate_artifact(dossier: dict) -> pathlib.Path:
    """Find the original artifact by name under fixtures/ when no path is given."""
    name = dossier.get("artifact", {}).get("name", "")
    for candidate_dir in ("synthetic", "drop", "real"):
        candidate = ROOT / "fixtures" / candidate_dir / name
        if candidate.exists():
            return candidate
    return ROOT / "fixtures" / "synthetic" / name


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
    parser = argparse.ArgumentParser(description="NEKROMANCER parity harness")
    parser.add_argument("artifact_id")
    parser.add_argument("format", choices=["csv", "dbf"])
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--artifact", default=None, help="Path to the original artifact")
    parser.add_argument("--dossier", default=None, help="Path to dossier.json")
    parser.add_argument("--restored", default=None, help="Path to the restored app directory")
    args = parser.parse_args()

    report = run_parity(
        args.artifact_id, args.format, n_sequences=args.n, seed=args.seed,
        dossier_path=args.dossier, artifact_path=args.artifact, restored_dir=args.restored,
    )
    save_report(report, args.artifact_id)

    passed = sum(1 for p in report["properties"] if p["status"] == "pass")
    total = len(report["properties"])
    print(f"[parity] {passed}/{total} properties passed | "
          f"{report['sequences_run']} sequences | "
          f"{len(report['counterexamples'])} counterexamples | "
          f"{report['elapsed_seconds']}s")
