#!/usr/bin/env python3
"""
packages/synth/engine.py
Template engine for static site synthesis (GOLEM).

Security rules (FR-11, S-6):
- LLM only fills text slots; structure is from templates.
- All values rendered via textContent, never innerHTML.
- CSP header added to every page.
- No eval(), no new Function(), no document.write().
"""
import html
import json
import pathlib
import sys
import yaml

ROOT = pathlib.Path(__file__).parent.parent.parent
TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"
RESTORED_DIR = ROOT / "apps" / "restored"

CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; "
       "img-src 'self' data:; connect-src 'self'")


def _safe_text(value) -> str:
    """Escape value for safe HTML text insertion."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def render_site(model_path: str | pathlib.Path, dossier_path: str | pathlib.Path) -> pathlib.Path:
    """
    Render static site from model + dossier.
    Returns path to generated index.html.
    """
    model_path = pathlib.Path(model_path)
    dossier_path = pathlib.Path(dossier_path)

    with open(model_path, encoding="utf-8") as f:
        model = yaml.safe_load(f)
    with open(dossier_path, encoding="utf-8") as f:
        dossier = json.load(f)

    artifact_id = model["artifact_id"]
    out_dir = RESTORED_DIR / artifact_id
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = _display_payload(model, dossier)

    # Write data layer as separate JSON (FR-12) — data only, never executed
    data_file = out_dir / "data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Render index.html
    index_html = _render_index(model, dossier, payload)
    index_path = out_dir / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)

    # Copy CSS
    _write_css(out_dir)
    # Copy JS
    _write_js(out_dir, model)

    print(f"[synth] ✅ Site rendered: {index_path}", file=sys.stderr)
    return index_path


def _display_payload(model: dict, dossier: dict) -> dict:
    """
    Build the data payload the browser renders.

    The dossier stores HTML-escaped values on purpose (S-5/S-6): it is an
    interchange format that may be quoted into prompts or embedded in markup.
    The browser receives raw values instead, because the generated app inserts
    every cell with textContent — escaping again would show entities literally.
    """
    payload = json.loads(json.dumps({"dossier": dossier, "model": model}, ensure_ascii=False))
    for row in payload["dossier"].get("samples", []) or []:
        for key, value in list(row.items()):
            if isinstance(value, str):
                row[key] = html.unescape(value)
    return payload


def _render_index(model: dict, dossier: dict, payload: dict) -> str:
    """Render index.html from model."""
    artifact_name = _safe_text(model.get("artifact_name", "Artifact"))
    artifact_id   = _safe_text(model.get("artifact_id", "unknown"))
    format_family = _safe_text(model.get("format", ""))
    confidence    = dossier.get("format", {}).get("confidence", 0)
    entity        = model.get("entities", [{}])[0]
    entity_name   = _safe_text(entity.get("name", "Records"))
    fields        = entity.get("fields", [])
    samples       = dossier.get("samples", [])
    unresolved    = dossier.get("unresolved", [])
    warnings      = dossier.get("warnings", [])

    # Build field headers (all with cite attribute for P2 audit)
    headers_html = "".join(
        f'<th data-cite="{_safe_text(f.get("cite",""))}">'
        f'{_safe_text(f.get("label", f.get("name","")))}</th>'
        for f in fields
    )

    # Build sample rows
    rows_html = ""
    for sample in samples[:10]:
        cells = "".join(
            f'<td data-field="{_safe_text(fname)}"></td>'
            for fname in (f["name"] for f in fields)
            if fname in sample or True
        )
        rows_html += f"<tr>{cells}</tr>\n"

    # Warnings banner
    warn_items = "".join(
        f'<li class="warning-item" data-code="{_safe_text(w["code"])}">'
        f'{_safe_text(w["message"])}</li>'
        for w in warnings
    )
    warn_html = f'<ul class="warnings" role="list">{warn_items}</ul>' if warnings else ""

    # Unresolved
    unres_items = "".join(
        f'<li class="unresolved-item"><strong>{_safe_text(u["code"])}</strong>: {_safe_text(u["message"])}</li>'
        for u in unresolved
    )
    unres_html = (
        f'<section aria-label="Unresolved items"><h2>Unresolved</h2>'
        f'<ul role="list">{unres_items}</ul></section>'
        if unresolved else ""
    )

    # Inline payload so the page also works from file:// with no server.
    # type="application/json" is inert data — it is never executed as script.
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="{CSP}">
  <title>{artifact_name} — NEKROMANCER Restored</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <a href="#main" class="skip-link">Skip to content</a>

  <header role="banner">
    <h1 id="page-title">{artifact_name}</h1>
    <p class="meta">
      Format: <span id="format-family"></span> |
      Confidence: <span id="confidence"></span> |
      Fields: <span id="field-count"></span>
    </p>
    <p class="provenance">
      Artifact ID: <code>{artifact_id}</code> |
      <a href="data.json" download>Download raw data</a> |
      <a href="parity-report.json" download>Parity report</a>
    </p>
  </header>

  <main id="main">
    {warn_html}

    <section aria-label="{entity_name} records">
      <h2>{entity_name}</h2>
      <div class="table-wrapper" role="region" aria-label="Data table" tabindex="0">
        <table id="data-table" aria-describedby="page-title">
          <thead>
            <tr>{headers_html}</tr>
          </thead>
          <tbody id="table-body">
            <!-- Rows populated by app.js from data.json — never innerHTML -->
          </tbody>
        </table>
      </div>
      <p id="row-count" aria-live="polite"></p>
    </section>

    {unres_html}

    <section aria-label="Provenance">
      <h2>Provenance</h2>
      <dl>
        <dt>Artifact</dt><dd id="prov-artifact"></dd>
        <dt>SHA-256</dt><dd id="prov-sha256" class="monospace"></dd>
        <dt>Detected by</dt><dd id="prov-detected-by"></dd>
        <dt>Restored by</dt><dd>NEKROMANCER v1.0</dd>
      </dl>
    </section>
  </main>

  <footer>
    <p>Restored by <strong>NEKROMANCER</strong> — sesuatu yang terkubur tidak harus tetap terkubur.</p>
    <p>All data displayed from <a href="data.json">data.json</a>. No server required.</p>
  </footer>

  <script type="application/json" id="payload">{payload_json}</script>
  <script src="app.js"></script>
</body>
</html>
"""


def _write_css(out_dir: pathlib.Path):
    css = """:root {
  --bg: #0d1117;
  --surface: #161b22;
  --border: #30363d;
  --text: #e6edf3;
  --muted: #8b949e;
  --accent: #58a6ff;
  --warn: #d29922;
  --error: #f85149;
  --success: #3fb950;
  --radius: 6px;
  --font: system-ui, -apple-system, sans-serif;
  --mono: 'SFMono-Regular', Consolas, monospace;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}

body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  font-size: 1rem;
  min-height: 100vh;
}

.skip-link {
  position: absolute;
  left: -9999px;
  top: 0;
  background: var(--accent);
  color: var(--bg);
  padding: 0.5rem 1rem;
  z-index: 100;
  border-radius: var(--radius);
  font-weight: 600;
}
.skip-link:focus { left: 1rem; top: 1rem; }

header[role="banner"] {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 1.5rem 2rem;
}

header h1 { font-size: 1.5rem; color: var(--accent); margin-bottom: 0.5rem; }
.meta { color: var(--muted); font-size: 0.875rem; }
.provenance { color: var(--muted); font-size: 0.8rem; margin-top: 0.25rem; }
.provenance a { color: var(--accent); }

main { padding: 2rem; max-width: 1400px; margin: 0 auto; }

.warnings {
  background: rgba(210, 153, 34, 0.1);
  border: 1px solid var(--warn);
  border-radius: var(--radius);
  padding: 1rem 1.5rem;
  margin-bottom: 1.5rem;
  list-style: none;
}
.warning-item { color: var(--warn); padding: 0.25rem 0; }

h2 { font-size: 1.1rem; color: var(--text); margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }

.table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  outline-offset: 2px;
}
.table-wrapper:focus { outline: 2px solid var(--accent); }

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
th {
  background: var(--surface);
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
td {
  padding: 0.5rem 1rem;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(88, 166, 255, 0.05); }
tr:focus-within td { outline: 2px solid var(--accent); outline-offset: -2px; }

#row-count { color: var(--muted); font-size: 0.8rem; margin-top: 0.5rem; }

section { margin-bottom: 2rem; }

dl { display: grid; grid-template-columns: max-content 1fr; gap: 0.25rem 1.5rem; font-size: 0.875rem; }
dt { color: var(--muted); font-weight: 600; }
dd { color: var(--text); }

.monospace { font-family: var(--mono); font-size: 0.75rem; word-break: break-all; }

.unresolved-item { margin-bottom: 0.5rem; color: var(--error); }

footer {
  background: var(--surface);
  border-top: 1px solid var(--border);
  padding: 1rem 2rem;
  font-size: 0.8rem;
  color: var(--muted);
  text-align: center;
}

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
a:focus { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 2px; }

/* Minimum touch target 24px (NF-accessibility) */
button, a, [role="button"] { min-height: 24px; min-width: 24px; display: inline-flex; align-items: center; }
"""
    with open(out_dir / "style.css", "w", encoding="utf-8") as f:
        f.write(css)


def _write_js(out_dir: pathlib.Path, model: dict):
    """Write app.js — uses textContent only, never innerHTML."""
    entity = model.get("entities", [{}])[0]
    fields_json = json.dumps([f["name"] for f in entity.get("fields", [])], ensure_ascii=False)

    js = f"""// NEKROMANCER restored app — app.js
// Security: all DOM insertion uses textContent. No innerHTML, no eval.
// CSP: default-src 'none'; script-src 'self'; connect-src 'self'
'use strict';

const FIELDS = {fields_json};

function readInlinePayload() {{
  // The page ships with an inert JSON payload so it also runs from file://
  const el = document.getElementById('payload');
  if (!el || !el.textContent) return null;
  try {{
    return JSON.parse(el.textContent);
  }} catch (err) {{
    console.error('Inline payload unreadable:', err.message);
    return null;
  }}
}}

async function loadData() {{
  const inline = readInlinePayload();
  if (inline) return inline;

  try {{
    const response = await fetch('data.json');
    if (!response.ok) throw new Error('Failed to load data.json');
    const data = await response.json();
    return data;
  }} catch (err) {{
    console.error('Data load failed:', err.message);
    return null;
  }}
}}

function setText(id, value) {{
  const el = document.getElementById(id);
  if (el) el.textContent = String(value ?? '');
}}

function renderTable(samples) {{
  const tbody = document.getElementById('table-body');
  if (!tbody) return;

  // Clear existing rows
  while (tbody.firstChild) tbody.removeChild(tbody.firstChild);

  samples.forEach((row, i) => {{
    const tr = document.createElement('tr');
    tr.setAttribute('tabindex', '0');
    tr.setAttribute('aria-rowindex', i + 2);  // +2 for header row

    FIELDS.forEach(fieldName => {{
      const td = document.createElement('td');
      // textContent only — never innerHTML (S-6)
      td.textContent = row[fieldName] ?? '';
      td.setAttribute('data-field', fieldName);
      tr.appendChild(td);
    }});
    tbody.appendChild(tr);
  }});

  setText('row-count', `Showing ${{samples.length}} sample record(s)`);
}}

function renderProvenance(dossier) {{
  setText('prov-artifact', dossier?.artifact?.name ?? '');
  setText('prov-sha256', dossier?.artifact?.sha256 ?? '');
  setText('prov-detected-by', dossier?.format?.detected_by ?? '');
  setText('format-family', dossier?.format?.family ?? '');
  setText('confidence', ((dossier?.format?.confidence ?? 0) * 100).toFixed(1) + '%');
  setText('field-count', (dossier?.structure ?? []).length);
}}

async function init() {{
  const data = await loadData();
  if (!data) {{
    setText('row-count', 'Failed to load data.');
    return;
  }}
  renderProvenance(data.dossier);
  renderTable(data.dossier?.samples ?? []);
}}

document.addEventListener('DOMContentLoaded', init);
"""
    with open(out_dir / "app.js", "w", encoding="utf-8") as f:
        f.write(js)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("model", help="Path to model.yaml")
    parser.add_argument("dossier", help="Path to dossier.json")
    args = parser.parse_args()
    out = render_site(args.model, args.dossier)
    print(f"Site rendered to: {out}")
