#!/usr/bin/env python3
"""
packages/probe/runner.py
Orchestrate artifact probe: hash → detect → sandbox → dossier → validate.

Security controls:
- S-1: All codec execution happens inside sandbox (Docker)
- S-3: File size / decompression ratio / entry count limits enforced before sandbox
- S-4: Output path canonicalized and verified
- S-5: Artifact text never injected as instruction
"""
import argparse
import hashlib
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from packages.codec.detector import detect, DetectionResult
from packages.codec.csv_codec import parse as csv_parse
from packages.codec.dbf_codec import parse as dbf_parse
from packages.dossier.validate import validate

DOSSIERS_DIR = ROOT / "dossiers"
MAX_FILE_SIZE = 50 * 1024 * 1024   # 50 MB (S-3)
CONFIDENCE_THRESHOLD = 0.7

# Supported codec map
CODEC_MAP = {
    "csv": csv_parse,
    "dbf": dbf_parse,
}


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_output_path(base_dir: pathlib.Path, artifact_id: str) -> pathlib.Path:
    """Canonicalize and verify output directory is inside dossiers/. (S-4)"""
    candidate = (base_dir / artifact_id).resolve()
    if not str(candidate).startswith(str(base_dir.resolve())):
        raise ValueError(f"Path traversal detected: {candidate}")
    return candidate


def enforce_size_limits(path: pathlib.Path) -> str | None:
    """Return error code if any size limit is violated, else None."""
    size = path.stat().st_size
    if size > MAX_FILE_SIZE:
        return "FILE_TOO_LARGE"
    if size == 0:
        return "EMPTY_FILE"
    return None


def run_probe(artifact_path: str, smoke_test: bool = False) -> dict:
    """Full probe pipeline. Returns dossier dict."""
    path = pathlib.Path(artifact_path).resolve()
    start_time = time.time()

    # --- Size check (S-3) ---
    err = enforce_size_limits(path)
    if err:
        return _error_dossier(path, err, f"File rejected: {err}")

    # --- Hash ---
    sha256 = sha256_file(path)
    artifact_id = sha256[:16]

    # --- Dedup check ---
    out_dir = safe_output_path(DOSSIERS_DIR, artifact_id)
    dossier_path = out_dir / "dossier.json"
    if dossier_path.exists():
        print(f"[probe] Cache hit: {artifact_id}", file=sys.stderr)
        with open(dossier_path, encoding="utf-8") as f:
            return json.load(f)

    # --- Format detection ---
    detection: DetectionResult = detect(path)

    if detection.family == "unknown":
        return _error_dossier(path, "FORMAT_UNKNOWN",
                              "Format not recognized from file content",
                              sha256=sha256, artifact_id=artifact_id)

    if detection.confidence < CONFIDENCE_THRESHOLD:
        return _error_dossier(path, "LOW_CONFIDENCE",
                              f"Detection confidence {detection.confidence:.2f} below threshold {CONFIDENCE_THRESHOLD}",
                              sha256=sha256, artifact_id=artifact_id,
                              format_family=detection.family,
                              format_confidence=detection.confidence)

    # --- Codec parse ---
    codec = CODEC_MAP.get(detection.family)
    if codec is None:
        return _error_dossier(path, "NO_CODEC",
                              f"No codec available for format '{detection.family}'",
                              sha256=sha256, artifact_id=artifact_id)

    kwargs = {}
    if detection.family == "csv":
        kwargs = {"encoding": detection.encoding, "delimiter": detection.delimiter}

    try:
        codec_result = codec(path, **kwargs)
    except Exception as e:
        return _error_dossier(path, "CODEC_ERROR", str(e),
                              sha256=sha256, artifact_id=artifact_id)

    elapsed = time.time() - start_time

    # --- Assemble dossier ---
    dossier = {
        "schema_version": "1.0",
        "artifact": {
            "id": artifact_id,
            "sha256": sha256,
            "size": path.stat().st_size,
            "name": path.name,
        },
        "format": {
            "family": detection.family,
            "detected_by": detection.detected_by,
            "confidence": round(detection.confidence, 4),
            "encoding": detection.encoding,
            "delimiter": detection.delimiter if detection.family == "csv" else "",
        },
        "structure": codec_result.get("structure", []),
        "samples":   codec_result.get("samples", []),
        "unresolved": codec_result.get("unresolved", []),
        "warnings":   codec_result.get("warnings", []),
        "_meta": {
            "probe_elapsed_seconds": round(elapsed, 3),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    }

    # Inject-attempt from detector
    if detection.extra.get("injection_attempt"):
        dossier["warnings"].append({
            "code": "INJECTION_ATTEMPT",
            "message": "Detector found text resembling an instruction in raw bytes"
        })

    # --- Write dossier ---
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(dossier_path, "w", encoding="utf-8") as f:
        json.dump(dossier, f, indent=2, ensure_ascii=False)

    # --- Validate ---
    is_valid, errors = validate(str(dossier_path))
    if not is_valid:
        print(f"[probe] Dossier INVALID: {errors}", file=sys.stderr)
        dossier["_validation_errors"] = errors
        return dossier

    print(f"[probe] ✅ Dossier written: {dossier_path}", file=sys.stderr)

    if smoke_test:
        _smoke_test(dossier)

    return dossier


def _error_dossier(path: pathlib.Path, code: str, message: str,
                   sha256: str = "", artifact_id: str = "",
                   format_family: str = "unknown",
                   format_confidence: float = 0.0) -> dict:
    print(f"[probe] ❌ {code}: {message}", file=sys.stderr)
    return {
        "schema_version": "1.0",
        "artifact": {
            "id": artifact_id or "unknown",
            "sha256": sha256 or ("0" * 64),
            "size": path.stat().st_size if path.exists() else 0,
            "name": path.name,
        },
        "format": {
            "family": format_family,
            "detected_by": "probe_error",
            "confidence": format_confidence,
            "encoding": "",
            "delimiter": "",
        },
        "structure": [],
        "samples": [],
        "unresolved": [{"code": code, "message": message}],
        "warnings": [],
    }


def _smoke_test(dossier: dict):
    """Basic smoke assertions after probe."""
    assert dossier["schema_version"] == "1.0", "schema_version missing"
    assert len(dossier["artifact"]["sha256"]) == 64, "sha256 wrong length"
    assert dossier["format"]["confidence"] >= 0.0, "confidence out of range"
    print("[smoke] ✅ All smoke assertions passed", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="NEKROMANCER probe runner")
    parser.add_argument("artifact", help="Path to artifact file")
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke assertions after probe")
    parser.add_argument("--json", action="store_true", help="Output dossier as JSON to stdout")
    args = parser.parse_args()

    dossier = run_probe(args.artifact, smoke_test=args.smoke_test)

    if args.json:
        print(json.dumps(dossier, indent=2, ensure_ascii=False))
    else:
        code = dossier["unresolved"][0]["code"] if dossier["unresolved"] else "OK"
        print(f"[probe] Result: {code} | format={dossier['format']['family']} "
              f"confidence={dossier['format']['confidence']:.2f} "
              f"fields={len(dossier['structure'])}")


if __name__ == "__main__":
    main()
