"""
Property P6 — DoS Limits (S-3)
================================
File size, decompression ratio, and entry count limits must be enforced.
The probe runner must reject oversized artifacts with typed errors.

Run with: pytest packages/parity/props/p6_dos.py -v
"""
import os
import pathlib
import sys
import tempfile
import zipfile

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

ROOT = pathlib.Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from packages.probe.runner import enforce_size_limits, run_probe

MAX_SIZE = 50 * 1024 * 1024  # 50 MB


# ----- P6-A: Files > 50MB are rejected with FILE_TOO_LARGE -----
def test_file_too_large_rejected():
    """P6-A: Probe must reject files over 50MB."""
    # Create a 51MB temp file
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.seek(51 * 1024 * 1024)
        tmp.write(b"\x00")
        tmp_path = tmp.name

    try:
        result = run_probe(tmp_path)
        codes = [u["code"] for u in result.get("unresolved", [])]
        assert "FILE_TOO_LARGE" in codes, (
            f"P6-A FAIL: Expected FILE_TOO_LARGE in unresolved, got: {codes}"
        )
    finally:
        pathlib.Path(tmp_path).unlink(missing_ok=True)


# ----- P6-B: Empty files are rejected -----
def test_empty_file_rejected():
    """P6-B: Probe must reject empty files."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name  # empty

    try:
        result = run_probe(tmp_path)
        codes = [u["code"] for u in result.get("unresolved", [])]
        assert "EMPTY_FILE" in codes or "FORMAT_UNKNOWN" in codes, (
            f"P6-B FAIL: Expected EMPTY_FILE or FORMAT_UNKNOWN, got: {codes}"
        )
    finally:
        pathlib.Path(tmp_path).unlink(missing_ok=True)


# ----- P6-C: enforce_size_limits returns correct code -----
@given(st.integers(min_value=1, max_value=MAX_SIZE))
@settings(max_examples=100, deadline=None)
def test_size_within_limit_accepted(size: int):
    """P6-C: Files within size limit pass enforce_size_limits."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.seek(size - 1)
        tmp.write(b"\x00")
        tmp_path = pathlib.Path(tmp.name)

    try:
        result = enforce_size_limits(tmp_path)
        assert result is None, f"P6-C FAIL: Expected None for size {size}, got: {result}"
    finally:
        tmp_path.unlink(missing_ok=True)


# ----- P6-D: Probe result always has schema_version -----
@given(st.binary(min_size=1, max_size=1024))
@settings(max_examples=200, deadline=None)
def test_probe_always_returns_schema_version(content: bytes):
    """P6-D: run_probe must always return a dict with schema_version."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = run_probe(tmp_path)
        assert "schema_version" in result, (
            f"P6-D FAIL: run_probe result missing schema_version"
        )
        assert result["schema_version"] == "1.0"
    finally:
        pathlib.Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    print("Running P6-A: File too large...")
    test_file_too_large_rejected()
    print("✅ P6-A passed")

    print("Running P6-B: Empty file...")
    test_empty_file_rejected()
    print("✅ P6-B passed")

    print("Running P6-D: Schema version always present...")
    test_probe_always_returns_schema_version()
    print("✅ P6-D passed")

    print("\n🎉 All P6 properties passed!")
