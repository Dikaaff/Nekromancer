#!/usr/bin/env python3
"""
packages/model/builder.py
Build semantic model from dossier (PALEOGRAPHER).

Resurrection Doctrine enforced:
- Never create fields not in dossier (FR-7)
- Every model element must cite its dossier source
- Unresolvable fields → unresolved[], never guessed
"""
import json
import pathlib
import sys
import yaml

ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))


def build_model(dossier_path: str | pathlib.Path) -> dict:
    """
    Build model.yaml content from a dossier.json.
    Returns a dict ready to be serialized as YAML.
    """
    dossier_path = pathlib.Path(dossier_path)

    with open(dossier_path, encoding="utf-8") as f:
        dossier = json.load(f)

    artifact_id = dossier["artifact"]["id"]
    artifact_name = dossier["artifact"]["name"]
    format_family = dossier["format"]["family"]
    structure = dossier.get("structure", [])
    unresolved_in = dossier.get("unresolved", [])

    # --- Build entity from structure ---
    entity_name = _entity_name_from_artifact(artifact_name, format_family)
    fields = []
    unresolved_out = list(unresolved_in)  # carry forward existing unresolved

    for idx, field_def in enumerate(structure):
        field_name = field_def.get("field", "")
        field_type = field_def.get("type", "unknown")

        if not field_name:
            unresolved_out.append({
                "code": "UNNAMED_FIELD",
                "message": f"structure[{idx}] has no field name",
                "field": f"structure[{idx}]",
            })
            continue

        if field_type == "unknown":
            unresolved_out.append({
                "code": "UNKNOWN_TYPE",
                "message": f"Field '{field_name}' has unknown type — will render as string with warning",
                "field": field_name,
            })
            # Still include but mark as unresolved type
            field_type = "string"

        fields.append({
            "name": field_name,
            "type": field_type,
            "nullable": field_def.get("nullable", True),
            "label": _human_label(field_name),
            "cite": f"dossier.json#structure[{idx}]",  # MANDATORY cite (FR-7)
        })

    # --- Build screens ---
    screens = []
    if fields:
        screens.append({
            "id": "list",
            "title": f"{entity_name} List",
            "type": "table",
            "entity": entity_name,
            "columns": [f["name"] for f in fields],
            "cite": f"dossier.json#structure[0..{len(fields)-1}]",
        })
        screens.append({
            "id": "detail",
            "title": f"{entity_name} Detail",
            "type": "form",
            "entity": entity_name,
            "fields": [f["name"] for f in fields],
            "cite": f"dossier.json#structure[0..{len(fields)-1}]",
        })

    model = {
        "schema_version": "1.0",
        "artifact_id": artifact_id,
        "artifact_name": artifact_name,
        "format": format_family,
        "entities": [
            {
                "name": entity_name,
                "source": "dossier.json#structure",
                "fields": fields,
            }
        ],
        "screens": screens,
        "rules": _infer_rules(fields),
        "unresolved": unresolved_out,
    }

    return model


def _entity_name_from_artifact(name: str, fmt: str) -> str:
    """Generate a clean entity name from artifact filename."""
    base = pathlib.Path(name).stem
    # Sanitize: keep alphanumeric and underscore
    clean = "".join(c if c.isalnum() or c == "_" else "_" for c in base)
    return clean.strip("_") or f"{fmt}_record"


def _human_label(field_name: str) -> str:
    """Convert field_name to human-readable label."""
    return field_name.replace("_", " ").replace("-", " ").title()


def _infer_rules(fields: list[dict]) -> list[dict]:
    """Infer simple display rules from field types."""
    rules = []
    for f in fields:
        if f["type"] == "date":
            rules.append({
                "field": f["name"],
                "rule": "format_date",
                "cite": f["cite"],
            })
        elif f["type"] in ("integer", "float"):
            rules.append({
                "field": f["name"],
                "rule": "format_number",
                "cite": f["cite"],
            })
    return rules


def save_model(model: dict, output_dir: str | pathlib.Path) -> pathlib.Path:
    """Save model as YAML to output_dir/{artifact_id}/model.yaml."""
    output_dir = pathlib.Path(output_dir)
    artifact_id = model["artifact_id"]
    out_path = output_dir / artifact_id / "model.yaml"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(model, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    print(f"[model] ✅ Model saved: {out_path}", file=sys.stderr)
    return out_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build semantic model from dossier")
    parser.add_argument("dossier", help="Path to dossier.json")
    parser.add_argument("--output", default=str(ROOT / "packages" / "model"), help="Output directory")
    args = parser.parse_args()

    model = build_model(args.dossier)
    out = save_model(model, args.output)
    print(json.dumps(model, indent=2, ensure_ascii=False))
