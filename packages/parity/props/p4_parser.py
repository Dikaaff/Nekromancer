"""
Property P4 — Parser Fuzzing (S-2)
=====================================
CSV and DBF parsers must not crash on arbitrary byte input.
They must either return a valid partial result or a typed error — never an exception.

Run with: pytest packages/parity/props/p4_parser.py -v
"""
import pathlib
import sys
import tempfile

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

ROOT = pathlib.Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from packages.codec.csv_codec import parse as csv_parse
from packages.codec.dbf_codec import parse as dbf_parse
from packages.codec.detector import detect


def _result_is_safe(result: dict) -> bool:
    """A parser result is 'safe' if it has the required keys and no unhandled exception."""
    required = {"structure", "samples", "unresolved", "warnings"}
    return required.issubset(result.keys())


# ----- P4-A: CSV parser does not crash on arbitrary bytes -----
@given(st.binary(min_size=0, max_size=2048))
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_csv_parser_no_crash(arbitrary_bytes: bytes):
    """
    P4-A: csv_parse must not raise an unhandled exception
    regardless of byte content.
    """
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(arbitrary_bytes)
        tmp_path = tmp.name

    try:
        result = csv_parse(tmp_path)
        assert _result_is_safe(result), f"P4-A FAIL: Missing required keys in result: {result.keys()}"
    except Exception as e:
        pytest.fail(f"P4-A FAIL: csv_parse raised unhandled exception: {type(e).__name__}: {e}")
    finally:
        pathlib.Path(tmp_path).unlink(missing_ok=True)


# ----- P4-B: DBF parser does not crash on arbitrary bytes -----
@given(st.binary(min_size=0, max_size=2048))
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_dbf_parser_no_crash(arbitrary_bytes: bytes):
    """
    P4-B: dbf_parse must not raise an unhandled exception
    regardless of byte content.
    """
    with tempfile.NamedTemporaryFile(suffix=".dbf", delete=False) as tmp:
        tmp.write(arbitrary_bytes)
        tmp_path = tmp.name

    try:
        result = dbf_parse(tmp_path)
        assert _result_is_safe(result), f"P4-B FAIL: Missing required keys in result: {result.keys()}"
    except Exception as e:
        pytest.fail(f"P4-B FAIL: dbf_parse raised unhandled exception: {type(e).__name__}: {e}")
    finally:
        pathlib.Path(tmp_path).unlink(missing_ok=True)


# ----- P4-C: Detector does not crash on arbitrary bytes -----
@given(st.binary(min_size=0, max_size=4096))
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_detector_no_crash(arbitrary_bytes: bytes):
    """
    P4-C: detect() must not raise on arbitrary bytes.
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(arbitrary_bytes)
        tmp_path = tmp.name

    try:
        result = detect(tmp_path)
        assert result.family in ("csv", "dbf", "mdb", "html_legacy", "unknown"), (
            f"P4-C FAIL: Unknown family '{result.family}'"
        )
        assert 0.0 <= result.confidence <= 1.0, (
            f"P4-C FAIL: Confidence out of range: {result.confidence}"
        )
    except Exception as e:
        pytest.fail(f"P4-C FAIL: detect() raised unhandled exception: {type(e).__name__}: {e}")
    finally:
        pathlib.Path(tmp_path).unlink(missing_ok=True)


# ----- P4-D: Parser result always has typed errors, never bare strings -----
@given(st.binary(min_size=1, max_size=256))
@settings(max_examples=100, deadline=None)
def test_parser_errors_are_typed(arbitrary_bytes: bytes):
    """
    P4-D: All entries in unresolved[] must have 'code' and 'message' keys.
    """
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(arbitrary_bytes)
        tmp_path = tmp.name

    try:
        result = csv_parse(tmp_path)
        for entry in result.get("unresolved", []):
            assert "code" in entry, f"P4-D FAIL: unresolved entry missing 'code': {entry}"
            assert "message" in entry, f"P4-D FAIL: unresolved entry missing 'message': {entry}"
    finally:
        pathlib.Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    print("Running P4-A: CSV parser no crash...")
    test_csv_parser_no_crash()
    print("✅ P4-A passed")

    print("Running P4-B: DBF parser no crash...")
    test_dbf_parser_no_crash()
    print("✅ P4-B passed")

    print("Running P4-C: Detector no crash...")
    test_detector_no_crash()
    print("✅ P4-C passed")

    print("Running P4-D: Typed errors...")
    test_parser_errors_are_typed()
    print("✅ P4-D passed")

    print("\n🎉 All P4 properties passed!")
