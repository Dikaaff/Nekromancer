#!/usr/bin/env python3
"""
packages/model/citator.py
Verify citation integrity: every rendered model element must cite dossier.
Property P2 implementation — used by PALEOGRAPHER and test suite.
"""
import json
import pathlib
import sys
import yaml


def verify_all_elements_cited(model: dict) -> tuple[bool, list[str]]:
    """
    Returns (all_cited, list_of_uncited_paths).
    Checks every field and screen for a 'cite' key.
    """
    uncited = []

    for entity in model.get("entities", []):
        for i, field in enumerate(entity.get("fields", [])):
            if not field.get("cite"):
                uncited.append(f"entities[{entity['name']}].fields[{i}].{field.get('name', '?')}")

    for i, screen in enumerate(model.get("screens", [])):
        if not screen.get("cite"):
            uncited.append(f"screens[{i}].{screen.get('id', '?')}")

    for i, rule in enumerate(model.get("rules", [])):
        if not rule.get("cite"):
            uncited.append(f"rules[{i}].{rule.get('field', '?')}")

    return len(uncited) == 0, uncited


def verify_citations_resolve(model: dict, dossier: dict) -> tuple[bool, list[str]]:
    """
    Verify that cited dossier paths actually exist in the dossier.
    """
    invalid = []
    structure = dossier.get("structure", [])

    for entity in model.get("entities", []):
        for field in entity.get("fields", []):
            cite = field.get("cite", "")
            # Format: dossier.json#structure[N]
            if "structure[" in cite:
                try:
                    idx = int(cite.split("[")[1].split("]")[0])
                    if idx >= len(structure):
                        invalid.append(f"cite '{cite}' → index {idx} out of range (structure has {len(structure)})")
                except (IndexError, ValueError):
                    invalid.append(f"cite '{cite}' → unparseable index")

    return len(invalid) == 0, invalid


def run_citator(model_path: str, dossier_path: str | None = None) -> dict:
    with open(model_path, encoding="utf-8") as f:
        model = yaml.safe_load(f)

    all_cited, uncited = verify_all_elements_cited(model)
    result = {
        "all_elements_cited": all_cited,
        "uncited_paths": uncited,
    }

    if dossier_path:
        with open(dossier_path, encoding="utf-8") as f:
            dossier = json.load(f)
        resolved, invalid = verify_citations_resolve(model, dossier)
        result["citations_resolve"] = resolved
        result["invalid_citations"] = invalid

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Verify model citations")
    parser.add_argument("model", help="Path to model.yaml")
    parser.add_argument("--dossier", help="Path to dossier.json (for cross-validation)")
    args = parser.parse_args()

    result = run_citator(args.model, args.dossier)
    print(json.dumps(result, indent=2))

    if not result["all_elements_cited"] or not result.get("citations_resolve", True):
        sys.exit(1)
