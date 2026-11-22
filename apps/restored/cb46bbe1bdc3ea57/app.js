// NEKROMANCER restored app — app.js
// Security: all DOM insertion uses textContent. No innerHTML, no eval.
// CSP: default-src 'none'; script-src 'self'; connect-src 'self'
'use strict';

const FIELDS = ["kode_barang", "nama_barang", "kategori", "stok", "harga_satuan", "supplier", "tanggal_masuk"];

function readInlinePayload() {
  // The page ships with an inert JSON payload so it also runs from file://
  const el = document.getElementById('payload');
  if (!el || !el.textContent) return null;
  try {
    return JSON.parse(el.textContent);
  } catch (err) {
    console.error('Inline payload unreadable:', err.message);
    return null;
  }
}

async function loadData() {
  const inline = readInlinePayload();
  if (inline) return inline;

  try {
    const response = await fetch('data.json');
    if (!response.ok) throw new Error('Failed to load data.json');
    const data = await response.json();
    return data;
  } catch (err) {
    console.error('Data load failed:', err.message);
    return null;
  }
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = String(value ?? '');
}

function renderTable(samples) {
  const tbody = document.getElementById('table-body');
  if (!tbody) return;

  // Clear existing rows
  while (tbody.firstChild) tbody.removeChild(tbody.firstChild);

  samples.forEach((row, i) => {
    const tr = document.createElement('tr');
    tr.setAttribute('tabindex', '0');
    tr.setAttribute('aria-rowindex', i + 2);  // +2 for header row

    FIELDS.forEach(fieldName => {
      const td = document.createElement('td');
      // textContent only — never innerHTML (S-6)
      td.textContent = row[fieldName] ?? '';
      td.setAttribute('data-field', fieldName);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  setText('row-count', `Showing ${samples.length} sample record(s)`);
}

function renderProvenance(dossier) {
  setText('prov-artifact', dossier?.artifact?.name ?? '');
  setText('prov-sha256', dossier?.artifact?.sha256 ?? '');
  setText('prov-detected-by', dossier?.format?.detected_by ?? '');
  setText('format-family', dossier?.format?.family ?? '');
  setText('confidence', ((dossier?.format?.confidence ?? 0) * 100).toFixed(1) + '%');
  setText('field-count', (dossier?.structure ?? []).length);
}

async function init() {
  const data = await loadData();
  if (!data) {
    setText('row-count', 'Failed to load data.');
    return;
  }
  renderProvenance(data.dossier);
  renderTable(data.dossier?.samples ?? []);
}

document.addEventListener('DOMContentLoaded', init);
