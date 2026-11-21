#!/usr/bin/env python3
"""
packages/dossier/validate.py
Validate a dossier.json file against schema v1.0.
Exit 0 = valid. Exit 1 = invalid (details on stderr).
"""
import sys
import json
import pathlib
import argparse

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

SCHEMA_PATH = pathlib.Path(__file__).parent / "schema.json"


def load_schema() -> dict:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def validate(dossier_path: str) -> tuple[bool, list[str]]:
    """Return (is_valid, list_of_errors)."""
    schema = load_schema()
    try:
        with open(dossier_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"JSON parse error: {e}"]
    except FileNotFoundError:
        return False, [f"File not found: {dossier_path}"]

    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))

    if not errors:
        return True, []

    messages = []
    for err in errors:
        path = " -> ".join(str(p) for p in err.absolute_path) or "(root)"
        messages.append(f"  [{path}] {err.message}")
    return False, messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a NEKROMANCER dossier.json")
    parser.add_argument("dossier", help="Path to dossier.json")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    is_valid, errors = validate(args.dossier)

    if args.json:
        print(json.dumps({"valid": is_valid, "errors": errors}))
    else:
        if is_valid:
            print(f"✅ VALID: {args.dossier}")
        else:
            print(f"❌ INVALID: {args.dossier}", file=sys.stderr)
            for e in errors:
                print(e, file=sys.stderr)

    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
