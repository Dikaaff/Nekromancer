#!/usr/bin/env python3
"""
packages/codec/csv_codec.py
CSV/TSV parser — produces dossier structure entries.

Security rules:
- All string values are escaped before being stored (S-5, S-6).
- No value is ever interpreted as an instruction.
- Streaming parse: never loads the full file into memory at once.
- Max rows sampled: 10. Max fields: 500.
"""
import csv
import html
import io
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Generator

MAX_SAMPLE_ROWS = 10
MAX_FIELDS = 500
MAX_ROWS_FOR_TYPE_INFERENCE = 100

_DATE_RE = re.compile(r"^\d{4}[-/]\d{2}[-/]\d{2}$|^\d{8}$|^\d{2}[-/]\d{2}[-/]\d{4}$")
_INT_RE  = re.compile(r"^-?\d{1,15}$")
_FLOAT_RE = re.compile(r"^-?\d+[.,]\d+$")

# Injection detection (S-5)
_INJECTION_RE = re.compile(
    r"(ignore\s+previous|system\s+prompt|you\s+are\s+an?\s+ai|"
    r"disregard\s+all|forget\s+instructions|act\s+as)",
    re.IGNORECASE,
)


@dataclass
class FieldInfo:
    name: str
    inferred_type: str = "string"
    nullable: bool = False
    sample_values: list = field(default_factory=list)


def _escape_value(v: str) -> str:
    """Escape string for safe storage — prevents prompt injection and XSS."""
    if not isinstance(v, str):
        v = str(v)
    # HTML-escape to prevent XSS (S-6)
    v = html.escape(v, quote=True)
    # Escape block delimiters (S-5)
    v = v.replace("===", "&#61;&#61;&#61;")
    return v


def _infer_type(values: list[str]) -> str:
    """Infer field type from a sample of values."""
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return "string"

    if all(_DATE_RE.match(v.strip()) for v in non_empty):
        return "date"
    if all(_INT_RE.match(v.strip().replace(".", "").replace(",", "")) for v in non_empty):
        return "integer"
    if all(_FLOAT_RE.match(v.strip().replace(",", ".")) for v in non_empty):
        return "float"
    if all(v.strip().lower() in ("true", "false", "1", "0", "y", "n", "ya", "tidak") for v in non_empty):
        return "boolean"
    return "string"


def parse(
    path: str | pathlib.Path,
    encoding: str = "utf-8",
    delimiter: str = ",",
) -> dict:
    """
    Parse CSV/TSV artifact.
    Returns a partial dossier dict (structure, samples, unresolved, warnings).
    """
    path = pathlib.Path(path)
    unresolved = []
    warnings = []
    structure = []
    samples = []
    injection_fields = []

    try:
        with open(path, encoding=encoding, errors="replace") as fh:
            # Stream through for type inference
            reader = csv.reader(fh, delimiter=delimiter)

            try:
                raw_header = next(reader)
            except StopIteration:
                unresolved.append({"code": "EMPTY_FILE", "message": "CSV has no rows"})
                return _result(structure, samples, unresolved, warnings)

            # Sanitise header names
            if len(raw_header) > MAX_FIELDS:
                warnings.append({
                    "code": "FIELD_TRUNCATED",
                    "message": f"Field count {len(raw_header)} exceeds MAX_FIELDS {MAX_FIELDS}; truncated"
                })
                raw_header = raw_header[:MAX_FIELDS]

            fields_info: list[FieldInfo] = [FieldInfo(name=_escape_value(h)) for h in raw_header]

            row_count = 0
            sample_rows: list[dict] = []

            for raw_row in reader:
                row_count += 1

                # Pad / trim to header width
                row = raw_row[:MAX_FIELDS]
                while len(row) < len(fields_info):
                    row.append("")

                # Type inference on first N rows
                if row_count <= MAX_ROWS_FOR_TYPE_INFERENCE:
                    for i, fi in enumerate(fields_info):
                        v = row[i] if i < len(row) else ""
                        fi.sample_values.append(v)
                        if not v.strip():
                            fi.nullable = True
                        # Injection detection (S-5)
                        if _INJECTION_RE.search(v):
                            injection_fields.append(fi.name)

                # Collect samples
                if row_count <= MAX_SAMPLE_ROWS:
                    sample_rows.append({
                        fields_info[i].name: _escape_value(row[i] if i < len(row) else "")
                        for i in range(len(fields_info))
                    })

    except UnicodeDecodeError as e:
        unresolved.append({"code": "ENCODING_ERROR", "message": str(e)})
        return _result(structure, samples, unresolved, warnings)
    except Exception as e:
        unresolved.append({"code": "PARSE_ERROR", "message": str(e)})
        return _result(structure, samples, unresolved, warnings)

    # Build structure entries
    for i, fi in enumerate(fields_info):
        inferred = _infer_type(fi.sample_values)
        structure.append({
            "record": "row",
            "field": fi.name,
            "type": inferred,
            "byte_offset": 0,  # CSV doesn't have fixed byte offsets
            "nullable": fi.nullable,
        })

    samples = sample_rows

    # Injection warnings (S-5)
    for fname in set(injection_fields):
        warnings.append({
            "code": "INJECTION_ATTEMPT",
            "message": f"Field '{fname}' contains text resembling an instruction",
            "field": fname,
        })

    return _result(structure, samples, unresolved, warnings)


def _result(structure, samples, unresolved, warnings) -> dict:
    return {
        "structure": structure,
        "samples": samples,
        "unresolved": unresolved,
        "warnings": warnings,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: csv_codec.py <path> [encoding] [delimiter]")
        sys.exit(1)
    enc = sys.argv[2] if len(sys.argv) > 2 else "utf-8"
    delim = sys.argv[3] if len(sys.argv) > 3 else ","
    result = parse(sys.argv[1], encoding=enc, delimiter=delim)
    print(json.dumps(result, indent=2, ensure_ascii=False))
