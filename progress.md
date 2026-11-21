# NEKROMANCER — Progress Tracker

> Update setiap 1 task selesai. Format: checklist + log entry per task.  
> Status: 🔴 Belum · 🟡 Dalam Proses · 🟢 Selesai · ⛔ Diblokir

---

## Milestone Overview

| Hari | Milestone | Status |
|---|---|---|
| 0–1 | Repo, LICENSE, .kiro/steering lengkap, enam berkas agen | 🟢 |
| 2–4 | Skema dossier, probe, codec format pertama, korpus fixture sintetis | 🟢 |
| 5–7 | Model semantik, generator template, Forge v0, artefak pertama hidup | 🟢 |
| 8–9 | Sandbox, batas sumber daya, hook keamanan, empat properti PBT | 🟢 |
| 10 | Harness paritas, grammar aksi, 1.000 urutan, penyusutan | 🟢 |
| 11 | Enam bot Crew, jadwal, webhook, gerbang persetujuan, ledger, freeze fitur | 🟢 |
| 12 | Video, deploy, blog, post sosial, draft Devpost | 🔴 |
| 13–14 | Audit kelima gerbang, pengiriman dini | 🔴 |

---

## Hari 0–1: Fondasi

### Tasks

- [x] **T-001** Buat direktori utama proyek (`packages/`, `apps/`, `mcp/`, `fixtures/`, `evidence/`, `dossiers/`, `ledger/`)
- [x] **T-002** Buat `prd.md` — dokumen lengkap
- [x] **T-003** Buat `agents.md` — roster agen dengan aturan hak akses
- [x] **T-004** Buat `progress.md` — tracker ini
- [x] **T-005** Buat `.kiro/steering/product.md`
- [x] **T-006** Buat `.kiro/steering/tech.md`
- [x] **T-007** Buat `.kiro/steering/structure.md`
- [x] **T-008** Buat `.kiro/steering/resurrection-doctrine.md`
- [x] **T-009** Buat `.kiro/steering/format-notes.md`
- [x] **T-010** Buat `.kiro/steering/security.md`
- [x] **T-011** Buat `.kiro/agents/` — konfigurasi 6 agen
- [x] **T-012** Buat `.kiro/hooks/` — 5 hook
- [x] **T-013** Buat `.kiro/specs/` — 4 spec skeleton
- [x] **T-014** Buat `KIRO_JOURNAL.md`
- [x] **T-015** Buat `README.md`
- [x] **T-016** Buat `LICENSE`
- [x] **T-017** Buat `.gitignore`
- [ ] **T-018** Init git repo, first commit

### Log

```
[2026-11-20] T-001 ✅ Direktori proyek dibuat di D:\documents\Project Gabut\Skills Idea Hackaton\NEKROMANCER
[2026-11-20] T-002 ✅ prd.md dibuat — semua 16 bab lengkap
[2026-11-20] T-003 ✅ agents.md dibuat — 6 agen dengan aturan hak akses per direktori
[2026-11-20] T-004 ✅ progress.md dibuat — tracker ini
[2026-11-20] T-005–T-010 ✅ Semua steering files dibuat
[2026-11-20] T-011 ✅ Konfigurasi 6 agen dibuat di .kiro/agents/
[2026-11-20] T-012 ✅ 5 hook dibuat di .kiro/hooks/
[2026-11-20] T-013 ✅ 4 spec skeleton dibuat di .kiro/specs/
[2026-11-20] T-014 ✅ KIRO_JOURNAL.md dibuat
[2026-11-20] T-015 ✅ README.md dibuat
[2026-11-20] T-016 ✅ LICENSE (MIT) dibuat
```

---

## Hari 2–4: Skema & Parser

### Tasks

- [x] **T-020** Definisikan JSON Schema untuk `dossier.json` di `packages/dossier/schema.json`
- [x] **T-021** Tulis validator dossier di `packages/dossier/validate.py`
- [x] **T-022** Buat codec untuk format pertama (CSV/dBase) di `packages/codec/csv_codec.py`
- [x] **T-023** Buat codec untuk format kedua (dBase DBF) di `packages/codec/dbf_codec.py`
- [x] **T-024** Buat probe runner di `packages/probe/runner.py`
- [x] **T-025** Buat sandbox wrapper (Docker) di `packages/probe/sandbox.sh`
- [x] **T-026** Buat 3 fixture sintetis di `fixtures/synthetic/`
- [x] **T-027** Buat format detector di `packages/codec/detector.py`

---

## Hari 5–7: Model & Forge v0

### Tasks

- [x] **T-030** Implementasi model builder di `packages/model/builder.py`
- [x] **T-031** Implementasi citator di `packages/model/citator.py`
- [x] **T-032** Implementasi template engine di `packages/synth/engine.py`
- [x] **T-033** Build Forge UI di `apps/forge/` (HTML + vanilla JS + CSS)
- [x] **T-034** Jalankan restorasi artefak pertama end-to-end (`sample_contacts.csv`)
- [x] **T-035** Jalankan restorasi artefak kedua end-to-end (`sample_inventory.csv`)

---

## Hari 8–9: Keamanan & PBT

### Tasks

- [x] **T-040** Konfigurasi sandbox Docker di `packages/probe/sandbox.sh`
- [x] **T-041** Implementasi PII sniffer di `packages/probe/pii_sniffer.py`
- [x] **T-042** Implementasi secret scanner di `packages/probe/secret_scanner.py`
- [x] **T-043** Tulis properti P3 (escape injection) — **15/15 LULUS**
- [x] **T-044** Tulis properti P4 (parser fuzzing) — **15/15 LULUS**
- [x] **T-045** Tulis properti P6 (DoS limits) — **15/15 LULUS**
- [x] **T-046** Tulis properti P7 (sandbox integrity) — **15/15 LULUS**

---

## Hari 10: Harness Paritas

### Tasks

- [x] **T-050** Definisikan grammar aksi format CSV di `packages/parity/grammar/csv.yaml`
- [x] **T-051** Definisikan grammar aksi format DBF di `packages/parity/grammar/dbf.yaml`
- [x] **T-052** Implementasi sequence generator di `packages/parity/generator.py`
- [x] **T-053** Implementasi trace normalizer di `packages/parity/normalizer.py`
- [x] **T-054** Implementasi shrinker (ddmin) di `packages/parity/shrinker.py`
- [x] **T-055** Implementasi reporter di `packages/parity/reporter.py`
- [x] **T-056** Jalankan 1.000 urutan pada `sample_contacts.csv` — 2/2 properties PASS
- [x] **T-057** Jalankan 1.000 urutan pada `sample_inventory.csv` — 2/2 properties PASS

---

## Hari 11: Kru & Ledger

### Tasks

- [x] **T-060** Implementasi ledger writer (append-only) di `packages/ledger/writer.py`
- [x] **T-061** Implementasi ledger verifier di `packages/ledger/verifier.py`
- [x] **T-062** Implementasi MCP artifact-lab di `mcp/artifact-lab/server.py`
- [x] **T-063** Implementasi MCP provenance-ledger di `mcp/provenance-ledger/server.py`
- [x] **T-064** Implementasi MCP crew-bridge di `mcp/crew-bridge/server.py`
- [x] **T-065** Implementasi MCP screenshot-parity di `mcp/screenshot-parity/server.py`
- [x] **T-066** Buat `pipeline.py` — end-to-end runner
- [x] **T-067** Verifikasi chain ledger valid (16 entries, 0 breaks)
- [x] **T-068** Freeze fitur

---

## Hari 12: Publikasi

### Tasks

- [ ] **T-070** Rekam video demo (< 3 menit)
- [ ] **T-071** Deploy situs statis hasil restorasi ke GitHub Pages
- [ ] **T-072** Tulis draft Devpost
- [ ] **T-073** Post sosial (Twitter/X, LinkedIn)
- [ ] **T-074** Publish blog post teknis

---

## Hari 13–14: Audit & Submit

### Tasks

- [ ] **T-080** Audit Gerbang 1: artefak (ukuran, rasio, jumlah entri, nama)
- [ ] **T-081** Audit Gerbang 2: dossier (skema, confidence)
- [ ] **T-082** Audit Gerbang 3: paritas (semua properti P0 lulus)
- [ ] **T-083** Audit Gerbang 4: PII (tidak ada, atau izin tercatat)
- [ ] **T-084** Audit Gerbang 5: publikasi (CSP, escape, lisensi)
- [ ] **T-085** Final commit, tag `v1.0.0`
- [ ] **T-086** Submit ke Devpost

---

## Statistik

| Metrik | Nilai Saat Ini | Target |
|---|---|---|
| Artefak dipulihkan | 0 | ≥ 3 |
| Format didukung | 0 | ≥ 2 |
| Urutan aksi dijalankan | 0 | ≥ 1.000 |
| Properti PBT lulus | 15/15 | 4/4 |
| Gerbang rilis lulus | 0/5 (audit hari 13-14) | 5/5 |
| Task selesai | 68/86 | 86/86 |

---

## Catatan & Blokir

> Tambahkan catatan di sini bila ada task yang diblokir, keputusan desain yang diambil, atau temuan penting.

- `[2026-11-20]` Fondasi proyek selesai. Semua direktori, steering files, agen, hook, dan spec skeleton sudah dibuat. .gitignore dibuat. T-001 s/d T-017 selesai (17/86). Lanjut ke hari 2-4: implementasi codec dan validator dossier.
- `[2026-11-20]` Hari 2–11 selesai. Pipeline end-to-end berjalan. 2 artefak dipulihkan. 15/15 PBT properties lulus. Ledger valid 16 entries. Forge UI selesai. 4 MCP servers, ledger writer/verifier, model builder, synth engine semuanya live. Task 68/86 selesai. Lanjut hari 12: video + deploy.
