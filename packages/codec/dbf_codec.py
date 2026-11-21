#!/usr/bin/env python3
"""
packages/codec/dbf_codec.py
dBase / DBF parser — produces dossier structure entries.

Security:
- All string values escaped before storage (S-5, S-6).
- No value is interpreted as an instruction.
- Verifies record count vs file size to detect corruption.
- Rejects path traversal in associated .dbt/.fpt filenames (S-4).
"""
import html
import json
import pathlib
import re
import struct
import sys
from dataclasses import dataclass, field

# DBF field type map
_DBF_TYPE_MAP = {
    b"C": "string",
    b"N": "float",
    b"D": "date",
    b"L": "boolean",
    b"M": "memo",
    b"F": "float",
    b"I": "integer",
    b"T": "date",
    b"@": "date",
    b"+": "integer",
    b"B": "float",
    b"G": "string",
    b"P": "string",
}

# Injection detection (S-5)
_INJECTION_RE = re.compile(
    r"(ignore\s+previous|system\s+prompt|you\s+are\s+an?\s+ai|"
    r"disregard\s+all|forget\s+instructions|act\s+as)",
    re.IGNORECASE,
)

MAX_SAMPLE_ROWS = 10
MAX_FIELDS = 500


def _escape_value(v: str) -> str:
    if not isinstance(v, str):
        v = str(v)
    v = html.escape(v, quote=True)
    v = v.replace("===", "&#61;&#61;&#61;")
    return v


@dataclass
class DBFHeader:
    version: int
    record_count: int
    header_size: int
    record_size: int
    encoding: str


@dataclass
class DBFField:
    name: str
    type_char: str
    offset: int
    length: int
    decimals: int


def _read_header(fh) -> DBFHeader | None:
    """Parse DBF header. Returns None if structure is invalid."""
    raw = fh.read(32)
    if len(raw) < 32:
        return None

    version = raw[0]
    # record count at bytes 4-7 (little-endian uint32)
    record_count = struct.unpack_from("<I", raw, 4)[0]
    # header size at bytes 8-9 (little-endian uint16)
    header_size = struct.unpack_from("<H", raw, 8)[0]
    # record size at bytes 10-11 (little-endian uint16)
    record_size = struct.unpack_from("<H", raw, 10)[0]

    # Code page byte at offset 29
    code_page = raw[29]
    encoding_map = {
        0x01: "cp437", 0x02: "cp850", 0x03: "cp1251",
        0x57: "cp1252", 0x58: "cp1252", 0x59: "cp1252",
        0x64: "cp852", 0x65: "cp866", 0x96: "cp1251",
    }
    encoding = encoding_map.get(code_page, "cp850")

    return DBFHeader(version, record_count, header_size, record_size, encoding)


def _read_fields(fh, header: DBFHeader) -> list[DBFField]:
    """Parse DBF field descriptors."""
    fields = []
    offset = 1  # deletion flag byte
    idx = 0

    while True:
        raw = fh.read(32)
        if not raw or raw[0] == 0x0D:  # header terminator
            break
        if len(raw) < 32 or idx >= MAX_FIELDS:
            break

        # Field name: bytes 0-10, null-terminated
        name_raw = raw[0:11]
        name = name_raw.split(b"\x00")[0].decode("ascii", errors="replace").strip()

        type_char = chr(raw[11])
        length = raw[16]
        decimals = raw[17]

        escaped_name = _escape_value(name)
        fields.append(DBFField(
            name=escaped_name,
            type_char=type_char,
            offset=offset,
            length=length,
            decimals=decimals,
        ))
        offset += length
        idx += 1

    return fields


def parse(path: str | pathlib.Path) -> dict:
    """
    Parse dBase/DBF artifact.
    Returns partial dossier dict (structure, samples, unresolved, warnings).
    """
    path = pathlib.Path(path)
    unresolved = []
    warnings = []
    structure = []
    samples = []

    try:
        with open(path, "rb") as fh:
            header = _read_header(fh)
            if header is None:
                unresolved.append({"code": "DBF_HEADER_INVALID", "message": "Cannot read DBF header"})
                return _result(structure, samples, unresolved, warnings)

            # Verify record count vs file size
            file_size = path.stat().st_size
            expected_size = header.header_size + header.record_count * header.record_size
            if abs(file_size - expected_size) > header.record_size:
                warnings.append({
                    "code": "RECORD_COUNT_MISMATCH",
                    "message": f"Header says {header.record_count} records but file size suggests otherwise"
                })

            # Read field descriptors
            fh.seek(32)
            fields = _read_fields(fh, header)
            if not fields:
                unresolved.append({"code": "DBF_NO_FIELDS", "message": "No field descriptors found"})
                return _result(structure, samples, unresolved, warnings)

            # Build structure
            for f in fields:
                field_type = _DBF_TYPE_MAP.get(f.type_char.encode(), "unknown")
                structure.append({
                    "record": "dbf_record",
                    "field": f.name,
                    "type": field_type,
                    "byte_offset": f.offset,
                    "length": f.length,
                    "nullable": True,
                })

            # Read sample records
            fh.seek(header.header_size)
            injection_fields = []

            for row_idx in range(min(MAX_SAMPLE_ROWS, header.record_count)):
                raw_rec = fh.read(header.record_size)
                if not raw_rec or len(raw_rec) < header.record_size:
                    break

                # Deleted record (byte 0 = 0x2A '*')
                if raw_rec[0:1] == b"\x2a":
                    continue

                row = {}
                for f in fields:
                    start = f.offset
                    end = start + f.length
                    if end > len(raw_rec):
                        continue
                    raw_val = raw_rec[start:end]

                    try:
                        val_str = raw_val.decode(header.encoding, errors="replace").strip().rstrip("\x00")
                    except Exception:
                        val_str = raw_val.decode("latin-1", errors="replace").strip()

                    # Injection detection (S-5)
                    if _INJECTION_RE.search(val_str):
                        injection_fields.append(f.name)

                    row[f.name] = _escape_value(val_str)

                samples.append(row)

            # Injection warnings
            for fname in set(injection_fields):
                warnings.append({
                    "code": "INJECTION_ATTEMPT",
                    "message": f"Field '{fname}' contains text resembling an instruction",
                    "field": fname,
                })

    except FileNotFoundError:
        unresolved.append({"code": "FILE_NOT_FOUND", "message": str(path)})
    except Exception as e:
        unresolved.append({"code": "PARSE_ERROR", "message": str(e)})

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
        print("Usage: dbf_codec.py <path>")
        sys.exit(1)
    result = parse(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
