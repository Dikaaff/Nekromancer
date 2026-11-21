#!/usr/bin/env python3
"""
packages/probe/pii_sniffer.py
Scan artifact or dossier for PII patterns before publish (S-10).

Returns:
  exit 0 = clean
  exit 2 = PII found (blocked)
"""
import json
import re
import sys
from dataclasses import dataclass

# PII patterns — conservative, designed to minimize false negatives
_PATTERNS = {
    "EMAIL":       re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"),
    "PHONE_ID":    re.compile(r"\b(?:08\d{8,11}|\+62\d{8,12})\b"),
    "NIK":         re.compile(r"\b\d{16}\b"),           # Indonesian ID
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "PASSPORT":    re.compile(r"\b[A-Z]{1,2}\d{6,9}\b"),
}


@dataclass
class PIIFinding:
    category: str
    snippet: str   # masked
    location: str


def _mask(match: str) -> str:
    """Mask middle of match for safe display."""
    if len(match) <= 4:
        return "****"
    return match[:2] + "*" * (len(match) - 4) + match[-2:]


def scan_text(text: str, location: str = "unknown") -> list[PIIFinding]:
    findings = []
    for category, pattern in _PATTERNS.items():
        for m in pattern.finditer(text):
            findings.append(PIIFinding(
                category=category,
                snippet=_mask(m.group()),
                location=location,
            ))
    return findings


def scan_dossier(dossier_path: str) -> list[PIIFinding]:
    """Scan dossier samples for PII."""
    with open(dossier_path, encoding="utf-8") as f:
        data = json.load(f)

    findings = []
    for i, sample in enumerate(data.get("samples", [])):
        for field_name, value in sample.items():
            if isinstance(value, str):
                findings.extend(scan_text(value, f"samples[{i}].{field_name}"))
    return findings


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PII sniffer for NEKROMANCER")
    parser.add_argument("path", help="Path to dossier.json or text file")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin instead")
    args = parser.parse_args()

    if args.stdin:
        content = sys.stdin.read()
        findings = scan_text(content, "stdin")
    else:
        try:
            findings = scan_dossier(args.path)
        except Exception:
            with open(args.path, encoding="utf-8", errors="replace") as f:
                findings = scan_text(f.read(), args.path)

    if findings:
        print(f"❌ PII FOUND — {len(findings)} finding(s):", file=sys.stderr)
        for f in findings:
            print(f"  [{f.category}] {f.snippet} @ {f.location}", file=sys.stderr)
        sys.exit(2)
    else:
        print("✅ No PII detected")
        sys.exit(0)


if __name__ == "__main__":
    main()
