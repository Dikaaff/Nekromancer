# Spec 0003 — Design

## Stack

- HTML5 + CSS3 + Vanilla JS (tidak ada framework)
- Bisa dibuka langsung sebagai `file://` tanpa server
- Data dimuat dari JSON files di direktori relatif

## Layout

```
┌─────────────────────────────────────────────────────┐
│  🔮 NEKROMANCER Forge                    [keyboard?] │
├─────────────────────────────────────────────────────┤
│  Run List              │  Detail Panel               │
│  ─────────────         │  ────────────               │
│  ▶ artifact-001 ✅     │  Dossier  Parity  Ledger    │
│  ▶ artifact-002 🔄     │                             │
│  ▶ artifact-003 ❌     │  [konten tab aktif]         │
│                        │                             │
│                        │  [🔗 Buka Aplikasi Hasil]   │
└─────────────────────────────────────────────────────┘
```

## Aksesibilitas

- Tab order: Run List → Detail Panel → Tab Navigation → Konten
- Role: `list`, `listitem`, `tablist`, `tab`, `tabpanel`
- Shortcut: `1`/`2`/`3` untuk tab Dossier/Parity/Ledger
- Skip link: "Langsung ke konten"

## Data Loading

Data dimuat dari berkas JSON relatif:
```js
fetch('./data/runs.json')           // daftar run
fetch(`./data/${id}/dossier.json`)  // dossier per run
fetch(`./data/${id}/parity.json`)   // laporan paritas
fetch(`./data/${id}/ledger.json`)   // entri ledger
```

Forge tidak membutuhkan server — semua data adalah berkas statis.
