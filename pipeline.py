#!/usr/bin/env python3
"""
pipeline.py
End-to-end NEKROMANCER pipeline runner.
Orchestrates: probe → model → synth → parity → ledger

Usage:
  python pipeline.py <artifact_path>
  python pipeline.py fixtures/synthetic/sample_contacts.csv
"""
import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT))

from packages.probe.runner import run_probe
from packages.model.builder import build_model, save_model
from packages.synth.engine import render_site
from packages.parity.reporter import run_parity, save_report
from packages.ledger.writer import append_entry


def run_pipeline(artifact_path: str, n_parity: int = 1000, seed: int | None = None) -> dict:
    """
    Full pipeline. Returns summary dict.
    Gate 1 and Gate 2 are logged but not interactive (demo mode).
    """
    start = time.time()
    path = pathlib.Path(artifact_path)
    print(f"\n{'='*60}")
    print(f"🔮 NEKROMANCER Pipeline — {path.name}")
    print(f"{'='*60}\n")

    # ── 1. INGEST + PROBE ───────────────────────────────────────────
    print("[1/5] Probe...")
    dossier = run_probe(artifact_path, smoke_test=True)
    artifact_id = dossier["artifact"]["id"]

    code = dossier["unresolved"][0]["code"] if dossier["unresolved"] else "OK"
    if code != "OK":
        print(f"  ❌ Probe failed: {code}")
        return {"artifact_id": artifact_id, "status": "probe_failed", "code": code}

    print(f"  ✅ Format: {dossier['format']['family']} "
          f"(confidence={dossier['format']['confidence']:.0%}) "
          f"| {len(dossier['structure'])} fields")

    append_entry("probe", dossier["artifact"]["sha256"],
                 json.dumps(dossier, sort_keys=True), "ARCHAEOLOGIST")

    # ── GATE 1 ──────────────────────────────────────────────────────
    confidence = dossier["format"]["confidence"]
    unresolved_count = len(dossier["unresolved"])
    if confidence < 0.7 or unresolved_count > 10:
        print(f"\n⛩ GATE 1 FAIL: confidence={confidence:.2f}, unresolved={unresolved_count}")
        return {"artifact_id": artifact_id, "status": "gate1_failed"}
    print(f"  ⛩ Gate 1 PASS\n")

    # ── 2. MODEL ────────────────────────────────────────────────────
    print("[2/5] Build semantic model...")
    dossier_path = ROOT / "dossiers" / artifact_id / "dossier.json"
    model = build_model(dossier_path)
    model_dir = ROOT / "packages" / "model"
    model_path = save_model(model, model_dir)

    entities = model.get("entities", [{}])
    fields = entities[0].get("fields", []) if entities else []
    uncited = [f for f in fields if not f.get("cite")]
    if uncited:
        print(f"  ⚠️ {len(uncited)} fields without citation (FR-7)")
    else:
        print(f"  ✅ All {len(fields)} fields cited")

    append_entry("model", dossier["artifact"]["sha256"],
                 json.dumps(model, sort_keys=True, default=str), "PALEOGRAPHER")

    # ── 3. SYNTHESIS ────────────────────────────────────────────────
    print("\n[3/5] Synthesize static site...")
    index_path = render_site(model_path, dossier_path)
    print(f"  ✅ Site: {index_path.relative_to(ROOT)}")

    append_entry("synth", dossier["artifact"]["sha256"],
                 str(index_path), "GOLEM")

    # ── 4. PARITY ───────────────────────────────────────────────────
    print(f"\n[4/5] Parity verification ({n_parity} sequences)...")
    format_family = dossier["format"]["family"]
    report = run_parity(artifact_id, format_family, n_sequences=n_parity, seed=seed)
    report_path = save_report(report, artifact_id)

    passed = sum(1 for p in report["properties"] if p["status"] == "pass")
    total  = len(report["properties"])
    cxs    = len(report["counterexamples"])
    print(f"  ✅ {passed}/{total} properties passed | "
          f"{report['sequences_run']} sequences | "
          f"{cxs} counterexample(s) | {report['elapsed_seconds']}s")

    append_entry("parity", dossier["artifact"]["sha256"],
                 json.dumps(report, sort_keys=True, default=str), "REVENANT")

    # Copy parity report to restored dir
    import shutil
    parity_dest = ROOT / "apps" / "restored" / artifact_id / "parity-report.json"
    parity_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(report_path, parity_dest)

    # ── GATE 2 ──────────────────────────────────────────────────────
    all_pass = all(p["status"] == "pass" for p in report["properties"])
    pii_clear = not any(w["code"] == "PII_SUSPECTED" for w in dossier.get("warnings", []))

    print(f"\n⛩ Gate 2: properties={'PASS' if all_pass else 'FAIL'} | PII={'CLEAR' if pii_clear else 'BLOCKED'}")
    if not all_pass or not pii_clear:
        print("  ⚠️  Gate 2 PENDING — awaiting human approval in Forge UI")
        status = "gate2_pending"
    else:
        print("  ✅ Gate 2 PASS — ready for approval")
        status = "ready"

    append_entry("gate2", dossier["artifact"]["sha256"], status, "WATCHER")

    # ── 5. LEDGER VERIFY ────────────────────────────────────────────
    print("\n[5/5] Verify ledger chain...")
    from packages.ledger.verifier import verify_chain
    chain = verify_chain(ROOT / "ledger" / "entries.jsonl")
    if chain["valid"]:
        print(f"  ✅ Chain valid: {chain['entries_count']} entries")
    else:
        print(f"  ❌ Chain broken: {chain['breaks']}")

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"✅ Pipeline complete — {elapsed:.1f}s")
    print(f"   Artifact:  {artifact_id}")
    print(f"   App:       apps/restored/{artifact_id}/index.html")
    print(f"   Parity:    evidence/{artifact_id}/parity-report.json")
    print(f"   Ledger:    ledger/entries.jsonl")
    print(f"{'='*60}\n")

    return {
        "artifact_id": artifact_id,
        "status": status,
        "format": format_family,
        "fields": len(fields),
        "sequences_run": report["sequences_run"],
        "properties_passed": f"{passed}/{total}",
        "counterexamples": cxs,
        "elapsed_seconds": round(elapsed, 2),
        "app_path": str(index_path.relative_to(ROOT)),
        "parity_report": str(report_path.relative_to(ROOT)),
    }


def main():
    parser = argparse.ArgumentParser(description="NEKROMANCER end-to-end pipeline")
    parser.add_argument("artifact", help="Path to artifact file")
    parser.add_argument("--n-parity", type=int, default=1000, help="Number of parity sequences")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--json", action="store_true", help="Output summary as JSON")
    args = parser.parse_args()

    result = run_pipeline(args.artifact, n_parity=args.n_parity, seed=args.seed)

    if args.json:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
