// NEKROMANCER Forge — app.js
// Security: ALL DOM insertion uses textContent. No innerHTML, no eval, no document.write.
// CSP: default-src 'none'; script-src 'self'
'use strict';

// ─── State ───────────────────────────────────────────────────────────────────
let runs = [];
let selectedIndex = -1;
let activeTab = 'dossier';

// ─── Helpers ─────────────────────────────────────────────────────────────────
function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = String(value ?? '');
}

function setAttr(id, attr, value) {
  const el = document.getElementById(id);
  if (el) el.setAttribute(attr, value);
}

function show(id)  { const el = document.getElementById(id); if (el) el.hidden = false; }
function hide(id)  { const el = document.getElementById(id); if (el) el.hidden = true;  }

function makeEl(tag, text, cls) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (cls) el.className = cls;
  return el;
}

function statusBadge(status) {
  const map = {
    done: 'badge-done', running: 'badge-running',
    failed: 'badge-failed', pending: 'badge-pending', gate: 'badge-gate'
  };
  return map[status] || 'badge-pending';
}

function statusLabel(status) {
  const map = {
    done: '✅ Done', running: '🔄 Running',
    failed: '❌ Failed', pending: '⏳ Pending', gate: '⛩ Gate 2'
  };
  return map[status] || status;
}

function formatBytes(n) {
  if (n < 1024) return n + ' B';
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
  return (n / (1024 * 1024)).toFixed(1) + ' MB';
}

// ─── Data loading ─────────────────────────────────────────────────────────────
async function fetchJSON(url) {
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    return await r.json();
  } catch {
    return null;
  }
}

async function loadRuns() {
  const data = await fetchJSON('./data/runs.json');
  if (!data || !Array.isArray(data.runs)) {
    runs = getDemoRuns();
  } else {
    runs = data.runs;
  }
  renderRunList();
  setText('run-count', `${runs.length} run${runs.length !== 1 ? 's' : ''}`);
}

// ─── Render: Run List ─────────────────────────────────────────────────────────
function renderRunList() {
  const ul = document.getElementById('run-list');
  while (ul.firstChild) ul.removeChild(ul.firstChild);

  if (runs.length === 0) {
    const li = makeEl('li', 'No runs yet.', 'run-placeholder');
    ul.appendChild(li);
    return;
  }

  runs.forEach((run, i) => {
    const li = document.createElement('li');
    li.className = 'run-item' + (i === selectedIndex ? ' active' : '');
    li.setAttribute('role', 'button');
    li.setAttribute('tabindex', '0');
    li.setAttribute('aria-label', `Run: ${run.name}, status: ${run.status}`);
    li.setAttribute('aria-pressed', i === selectedIndex ? 'true' : 'false');
    li.dataset.index = i;

    const name = makeEl('span', run.name || run.artifact_id, 'run-name');
    const badge = makeEl('span', statusLabel(run.status), `run-badge ${statusBadge(run.status)}`);

    li.appendChild(name);
    li.appendChild(badge);

    li.addEventListener('click', () => selectRun(i));
    li.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectRun(i); }
    });

    ul.appendChild(li);
  });
}

// ─── Render: Detail ───────────────────────────────────────────────────────────
async function selectRun(index) {
  selectedIndex = index;
  renderRunList();

  const run = runs[index];
  if (!run) return;

  hide('no-selection');
  show('detail-content');

  // Load dossier + parity + ledger data
  const [dossier, parity, ledger] = await Promise.all([
    run.dossier_path ? fetchJSON(run.dossier_path) : Promise.resolve(run.dossier || null),
    run.parity_path  ? fetchJSON(run.parity_path)  : Promise.resolve(run.parity || null),
    run.ledger_path  ? fetchJSON(run.ledger_path)  : Promise.resolve(run.ledger || null),
  ]);

  renderDetailHeader(run);
  if (dossier) renderDossier(dossier);
  if (parity)  renderParity(parity);
  if (ledger)  renderLedger(ledger);

  // Gate 2 panel
  if (run.status === 'gate') {
    show('gate-panel');
  } else {
    hide('gate-panel');
  }

  // Links
  const restoredEl = document.getElementById('link-restored');
  const parityEl   = document.getElementById('link-parity');
  if (restoredEl) restoredEl.href = run.restored_path || '#';
  if (parityEl)   parityEl.href   = run.parity_path   || '#';

  switchTab('dossier');
}

function renderDetailHeader(run) {
  setText('detail-title',  run.name || run.artifact_id);
  const statusEl = document.getElementById('detail-status');
  const formatEl = document.getElementById('detail-format');
  if (statusEl) {
    statusEl.textContent = statusLabel(run.status);
    statusEl.className = `badge ${statusBadge(run.status)}`;
  }
  if (formatEl) {
    formatEl.textContent = run.format || 'unknown';
    formatEl.className = 'badge badge-format';
  }
}

function renderDossier(dossier) {
  const artifact = dossier.artifact || {};
  const format   = dossier.format   || {};
  const structure = dossier.structure || [];

  setText('d-name',        artifact.name  || '');
  setText('d-sha256',      artifact.sha256 || '');
  setText('d-size',        formatBytes(artifact.size || 0));
  setText('d-format',      format.family  || '');
  setText('d-confidence',  ((format.confidence || 0) * 100).toFixed(1) + '%');
  setText('d-detected-by', format.detected_by || '');
  setText('d-field-count', structure.length);

  // Structure table
  const tbody = document.getElementById('structure-body');
  if (tbody) {
    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
    structure.forEach((f, i) => {
      const tr = document.createElement('tr');
      [i + 1, f.field, f.type, f.nullable ? 'Yes' : 'No', f.byte_offset].forEach(v => {
        const td = makeEl('td', v);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }

  // Warnings
  const warnings = dossier.warnings || [];
  if (warnings.length > 0) {
    show('warnings-section');
    const ul = document.getElementById('warnings-list');
    if (ul) {
      while (ul.firstChild) ul.removeChild(ul.firstChild);
      warnings.forEach(w => {
        const li = makeEl('li', `[${w.code}] ${w.message}`);
        ul.appendChild(li);
      });
    }
  } else {
    hide('warnings-section');
  }

  // Unresolved
  const unresolved = dossier.unresolved || [];
  if (unresolved.length > 0) {
    show('unresolved-section');
    const ul = document.getElementById('unresolved-list');
    if (ul) {
      while (ul.firstChild) ul.removeChild(ul.firstChild);
      unresolved.forEach(u => {
        const li = makeEl('li', `[${u.code}] ${u.message}`);
        ul.appendChild(li);
      });
    }
  } else {
    hide('unresolved-section');
  }
}

function renderParity(parity) {
  setText('p-sequences', parity.sequences_run ?? 0);
  setText('p-seed',      parity.seed ?? '');
  setText('p-elapsed',   (parity.elapsed_seconds ?? 0) + 's');
  setText('p-policy',    JSON.stringify(parity.normalization_policy || {}));

  const propList = document.getElementById('properties-list');
  if (propList) {
    while (propList.firstChild) propList.removeChild(propList.firstChild);
    (parity.properties || []).forEach(p => {
      const li = document.createElement('li');
      const icon = p.status === 'pass' ? '✅' : '❌';
      const cls  = p.status === 'pass' ? 'prop-pass' : 'prop-fail';
      const span = makeEl('span', `${icon} ${p.name}`, cls);
      li.appendChild(span);
      if (p.sequences_run) {
        li.appendChild(makeEl('span', ` (${p.sequences_run}/${p.required})`, ''));
      }
      propList.appendChild(li);
    });
  }

  const cxs = parity.counterexamples || [];
  if (cxs.length > 0) {
    show('counterexamples-section');
    const ul = document.getElementById('counterexamples-list');
    if (ul) {
      while (ul.firstChild) ul.removeChild(ul.firstChild);
      cxs.forEach((cx, i) => {
        const li = makeEl('li',
          `#${i+1}: ${cx.cause} (${cx.minimal_sequence_length}/${cx.original_sequence_length} steps)`);
        ul.appendChild(li);
      });
    }
  } else {
    hide('counterexamples-section');
  }
}

function renderLedger(ledger) {
  const entries = Array.isArray(ledger) ? ledger : (ledger.entries || []);
  const valid   = ledger.valid !== false;

  setText('ledger-chain-status', valid
    ? `✅ Chain valid — ${entries.length} entries`
    : `❌ Chain broken — see entries for details`);

  const tbody = document.getElementById('ledger-body');
  if (!tbody) return;
  while (tbody.firstChild) tbody.removeChild(tbody.firstChild);

  entries.forEach(e => {
    const tr = document.createElement('tr');
    [e.seq, e.stage, e.actor, e.timestamp,
     (e.output_hash || '').slice(0, 16) + '…'].forEach(v => {
      tr.appendChild(makeEl('td', v ?? ''));
    });
    tbody.appendChild(tr);
  });
}

// ─── Tabs ─────────────────────────────────────────────────────────────────────
function switchTab(name) {
  activeTab = name;
  ['dossier', 'parity', 'ledger'].forEach(t => {
    const btn   = document.getElementById(`tab-${t}`);
    const panel = document.getElementById(`panel-${t}`);
    const active = t === name;
    if (btn)   { btn.classList.toggle('active', active); btn.setAttribute('aria-selected', active); }
    if (panel) { panel.hidden = !active; }
  });
}

// ─── Keyboard navigation ─────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  // 1/2/3 → switch tabs (FR-27)
  if (!e.ctrlKey && !e.altKey && !e.metaKey) {
    if (e.key === '1') { e.preventDefault(); switchTab('dossier'); }
    if (e.key === '2') { e.preventDefault(); switchTab('parity');  }
    if (e.key === '3') { e.preventDefault(); switchTab('ledger');  }
  }

  // ↑/↓ → navigate run list
  if (document.activeElement?.closest('.run-list') || e.target.id === 'run-list') {
    if (e.key === 'ArrowDown' && selectedIndex < runs.length - 1) {
      e.preventDefault(); selectRun(selectedIndex + 1);
    }
    if (e.key === 'ArrowUp' && selectedIndex > 0) {
      e.preventDefault(); selectRun(selectedIndex - 1);
    }
  }
});

// Tab keyboard navigation (role=tablist)
document.querySelector('.tabs')?.addEventListener('keydown', e => {
  const tabs = ['dossier', 'parity', 'ledger'];
  const idx  = tabs.indexOf(activeTab);
  if (e.key === 'ArrowRight' && idx < tabs.length - 1) {
    e.preventDefault(); switchTab(tabs[idx + 1]);
    document.getElementById(`tab-${tabs[idx + 1]}`)?.focus();
  }
  if (e.key === 'ArrowLeft' && idx > 0) {
    e.preventDefault(); switchTab(tabs[idx - 1]);
    document.getElementById(`tab-${tabs[idx - 1]}`)?.focus();
  }
});

// Tab click
['dossier', 'parity', 'ledger'].forEach(t => {
  document.getElementById(`tab-${t}`)?.addEventListener('click', () => switchTab(t));
});

// Refresh
document.getElementById('refresh-btn')?.addEventListener('click', loadRuns);

// Gate buttons
document.getElementById('approve-btn')?.addEventListener('click', () => {
  if (selectedIndex < 0) return;
  runs[selectedIndex].status = 'done';
  renderRunList();
  renderDetailHeader(runs[selectedIndex]);
  hide('gate-panel');
  console.log('[forge] Run approved:', runs[selectedIndex].artifact_id);
});

document.getElementById('reject-btn')?.addEventListener('click', () => {
  if (selectedIndex < 0) return;
  runs[selectedIndex].status = 'failed';
  renderRunList();
  renderDetailHeader(runs[selectedIndex]);
  hide('gate-panel');
  console.log('[forge] Run rejected:', runs[selectedIndex].artifact_id);
});

// ─── Demo data (fallback when data/runs.json not found) ───────────────────────
function getDemoRuns() {
  return [
    {
      artifact_id: 'a3f1e2d4',
      name: 'sample_contacts.csv',
      status: 'done',
      format: 'csv',
      restored_path: '../restored/a3f1e2d4/index.html',
      parity_path: '../restored/a3f1e2d4/parity-report.json',
      dossier: {
        schema_version: '1.0',
        artifact: { id: 'a3f1e2d4', sha256: 'a3f1e2d4b5c6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2', size: 512, name: 'sample_contacts.csv' },
        format: { family: 'csv', detected_by: 'delimiter_heuristic', confidence: 0.91, encoding: 'utf-8', delimiter: ',' },
        structure: [
          { record: 'row', field: 'id',               type: 'integer', byte_offset: 0, nullable: false },
          { record: 'row', field: 'nama',             type: 'string',  byte_offset: 0, nullable: false },
          { record: 'row', field: 'kota',             type: 'string',  byte_offset: 0, nullable: false },
          { record: 'row', field: 'telepon',          type: 'string',  byte_offset: 0, nullable: false },
          { record: 'row', field: 'email',            type: 'string',  byte_offset: 0, nullable: false },
          { record: 'row', field: 'tahun_bergabung',  type: 'integer', byte_offset: 0, nullable: false },
        ],
        samples: [
          { id: '1', nama: 'Budi Santoso', kota: 'Jakarta', telepon: '021-5551234', email: 'budi@example.com', tahun_bergabung: '1998' },
          { id: '2', nama: 'Siti Rahayu', kota: 'Bandung', telepon: '022-5559876', email: 'siti@example.com', tahun_bergabung: '1999' },
        ],
        unresolved: [],
        warnings: [],
      },
      parity: {
        schema_version: '1.0',
        artifact_id: 'a3f1e2d4',
        sequences_run: 1000,
        seed: 42,
        elapsed_seconds: 3.14,
        properties: [
          { name: 'P1_sequences_run', status: 'pass', sequences_run: 1000, required: 1000 },
          { name: 'CSV-parity', status: 'pass', failures: 0 },
        ],
        counterexamples: [],
        normalization_policy: { ignore_presentation_differences: true, ignore_whitespace_differences: true },
      },
      ledger: {
        valid: true,
        entries: [
          { seq: 1, stage: 'GENESIS', actor: 'HUMAN', timestamp: '2026-11-20T22:00:00Z', output_hash: 'a3f1e2d4b5c6a7b8' },
          { seq: 2, stage: 'ingest',  actor: 'ARCHAEOLOGIST', timestamp: '2026-11-20T22:01:00Z', output_hash: 'b4c5d6e7f8a9b0c1' },
          { seq: 3, stage: 'probe',   actor: 'ARCHAEOLOGIST', timestamp: '2026-11-20T22:01:30Z', output_hash: 'c5d6e7f8a9b0c1d2' },
          { seq: 4, stage: 'model',   actor: 'PALEOGRAPHER',  timestamp: '2026-11-20T22:02:00Z', output_hash: 'd6e7f8a9b0c1d2e3' },
          { seq: 5, stage: 'synth',   actor: 'GOLEM',         timestamp: '2026-11-20T22:03:00Z', output_hash: 'e7f8a9b0c1d2e3f4' },
          { seq: 6, stage: 'parity',  actor: 'REVENANT',      timestamp: '2026-11-20T22:04:00Z', output_hash: 'f8a9b0c1d2e3f4a5' },
        ],
      },
    },
    {
      artifact_id: 'b5c6d7e8',
      name: 'sample_inventory.csv',
      status: 'gate',
      format: 'csv',
      restored_path: '../restored/b5c6d7e8/index.html',
      dossier: {
        schema_version: '1.0',
        artifact: { id: 'b5c6d7e8', sha256: 'b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6', size: 648, name: 'sample_inventory.csv' },
        format: { family: 'csv', detected_by: 'delimiter_heuristic', confidence: 0.89, encoding: 'utf-8', delimiter: ',' },
        structure: [
          { record: 'row', field: 'kode_barang',   type: 'string',  byte_offset: 0, nullable: false },
          { record: 'row', field: 'nama_barang',   type: 'string',  byte_offset: 0, nullable: false },
          { record: 'row', field: 'kategori',      type: 'string',  byte_offset: 0, nullable: false },
          { record: 'row', field: 'stok',          type: 'integer', byte_offset: 0, nullable: false },
          { record: 'row', field: 'harga_satuan',  type: 'integer', byte_offset: 0, nullable: false },
          { record: 'row', field: 'supplier',      type: 'string',  byte_offset: 0, nullable: false },
          { record: 'row', field: 'tanggal_masuk', type: 'date',    byte_offset: 0, nullable: false },
        ],
        samples: [],
        unresolved: [],
        warnings: [],
      },
      parity: null,
      ledger: { valid: true, entries: [
        { seq: 1, stage: 'ingest', actor: 'ARCHAEOLOGIST', timestamp: '2026-11-20T22:10:00Z', output_hash: 'b5c6d7e8f9a0b1c2' },
      ]},
    },
    {
      artifact_id: 'c7d8e9f0',
      name: 'old_records.dbf',
      status: 'pending',
      format: 'dbf',
      dossier: null,
      parity: null,
      ledger: null,
    },
  ];
}

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', loadRuns);
