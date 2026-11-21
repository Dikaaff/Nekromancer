#!/usr/bin/env python3
"""
packages/codec/detector.py
Detect artifact format from file content (not extension).
Returns (family, confidence, metadata).

Security: This module reads raw bytes only. It does NOT execute artifact content.
"""
import re
import pathlib
from dataclasses import dataclass, field


@dataclass
class DetectionResult:
    family: str          # csv | dbf | mdb | html_legacy | unknown
    confidence: float    # 0.0 – 1.0
    detected_by: str     # method used
    encoding: str = "utf-8"
    delimiter: str = ","
    extra: dict = field(default_factory=dict)


# Magic bytes signatures
_DBF_MAGIC = {0x03, 0x83, 0x8B, 0xF5, 0x30, 0x31, 0x32}
_MDB_MAGIC_V3 = b"\x00\x01\x00\x00Standard Jet DB"
_MDB_MAGIC_V4 = b"\x00\x01\x00\x00Standard ACE DB"
_HTML_PATTERNS = [b"<html", b"<!doctype", b"<head", b"<body", b"<title"]

# Injection detection patterns (S-5)
_INJECTION_RE = re.compile(
    r"(ignore\s+previous|system\s+prompt|you\s+are\s+an?\s+ai|"
    r"disregard\s+all|forget\s+instructions|act\s+as)",
    re.IGNORECASE,
)


def _detect_encoding(raw: bytes) -> str:
    """Simple encoding detection with fallback chain."""
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    for enc in ("utf-8", "cp1252", "latin-1", "cp850"):
        try:
            raw.decode(enc)
            return enc
        except (UnicodeDecodeError, ValueError):
            continue
    return "latin-1"  # final fallback


def _detect_csv_delimiter(sample: str) -> tuple[str, float]:
    """Detect delimiter from first 10 lines."""
    lines = [l for l in sample.split("\n")[:10] if l.strip()]
    if not lines:
        return ",", 0.3

    counts: dict[str, list[int]] = {",": [], ";": [], "\t": [], "|": []}
    for line in lines:
        for d, lst in counts.items():
            lst.append(line.count(d))

    best_delim = ","
    best_score = 0.0
    for delim, cnts in counts.items():
        if not cnts:
            continue
        mean = sum(cnts) / len(cnts)
        # Variance: consistent count → more confident
        variance = sum((c - mean) ** 2 for c in cnts) / len(cnts)
        score = mean / (1 + variance) if mean > 0 else 0
        if score > best_score:
            best_score = score
            best_delim = delim

    # Confidence: at least 2 columns per line
    confidence = min(0.95, 0.5 + best_score * 0.05) if best_score >= 1 else 0.3
    return best_delim, confidence


def detect(path: str | pathlib.Path) -> DetectionResult:
    """
    Detect format of artifact at `path`.
    Reads up to 4096 bytes for magic detection, up to 8192 for CSV heuristics.
    """
    path = pathlib.Path(path)

    if not path.exists():
        return DetectionResult("unknown", 0.0, "file_not_found")

    size = path.stat().st_size
    if size == 0:
        return DetectionResult("unknown", 0.0, "empty_file")
    if size > 52_428_800:  # 50 MB hard limit (S-3)
        return DetectionResult("unknown", 0.0, "file_too_large")

    with open(path, "rb") as fh:
        header = fh.read(64)
        fh.seek(0)
        sample_bytes = fh.read(8192)

    # --- DBF ---
    if header[0:1] and header[0] in _DBF_MAGIC:
        # Verify DBF header structure: bytes 4-7 = record count, bytes 8-9 = header size
        if len(header) >= 10 and header[8] > 0:
            return DetectionResult(
                "dbf", 0.92, "magic_bytes",
                encoding=_detect_encoding(sample_bytes),
                extra={"dbf_version": header[0]}
            )

    # --- MDB (Access) ---
    if sample_bytes[:16] in (_MDB_MAGIC_V3, _MDB_MAGIC_V4):
        return DetectionResult("mdb", 0.98, "magic_bytes")

    # --- HTML legacy ---
    lower_head = sample_bytes[:256].lower()
    html_hits = sum(1 for p in _HTML_PATTERNS if p in lower_head)
    if html_hits >= 2:
        conf = min(0.95, 0.6 + html_hits * 0.07)
        return DetectionResult("html_legacy", conf, "html_patterns")

    # --- CSV / TSV (text-based heuristic) ---
    encoding = _detect_encoding(sample_bytes)
    try:
        sample_text = sample_bytes.decode(encoding, errors="replace")
    except Exception:
        sample_text = sample_bytes.decode("latin-1", errors="replace")

    # Check for injection attempts (S-5) — record as warning but still detect
    injection_found = bool(_INJECTION_RE.search(sample_text))

    delimiter, csv_conf = _detect_csv_delimiter(sample_text)

    if csv_conf >= 0.5:
        result = DetectionResult(
            "csv", csv_conf, "delimiter_heuristic",
            encoding=encoding,
            delimiter=delimiter,
            extra={"injection_attempt": injection_found}
        )
        return result

    return DetectionResult("unknown", 0.0, "no_match")


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) != 2:
        print("Usage: detector.py <path>")
        sys.exit(1)
    r = detect(sys.argv[1])
    print(json.dumps({
        "family": r.family,
        "confidence": r.confidence,
        "detected_by": r.detected_by,
        "encoding": r.encoding,
        "delimiter": r.delimiter,
        "extra": r.extra,
    }, indent=2))
