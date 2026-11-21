# KIRO_JOURNAL.md — Jurnal Integrasi Kiro

> Dokumen ini mencatat setiap keputusan integrasi Kiro yang diambil selama pembangunan NEKROMANCER, beserta alasannya. Ini adalah sumber tunggal untuk pertanyaan write-up "Bagaimana kamu menggunakan Kiro?"

---

## Sesi 2 · 2026-11-20 · Implementasi Penuh (Hari 2–11)

### Yang Dilakukan

- Dossier schema (JSON Schema v7) + validator CLI
- Format detector (magic bytes + heuristik) untuk CSV, DBF, MDB, HTML legacy
- CSV codec — streaming, encoding detection, injection scan
- DBF codec — header parse, field descriptor, record read, injection scan
- Probe runner — dedup, size limit, format detect, codec dispatch, dossier write
- PII sniffer + secret scanner (dipakai hook guard-secrets)
- Model builder — PALEOGRAPHER, citation per field, unresolved propagation
- Citator — verifikasi integritas cite di model.yaml
- Synth engine (GOLEM) — template render ke HTML statis, textContent only, CSP header
- Forge UI — HTML+CSS+JS, keyboard navigasi penuh, ARIA roles, tab shortcut 1/2/3
- Ledger writer (append-only) + verifier (chain hash check)
- 4 MCP servers: artifact-lab, provenance-ledger, crew-bridge, screenshot-parity
- Pipeline end-to-end `pipeline.py` — 5 tahap + 2 gate
- 15 PBT properties: P3 (3), P4 (4), P6 (4), P7 (4) — semua PASS
- pytest.ini untuk config Hypothesis
- 2 artefak berhasil dipulihkan: `sample_contacts.csv`, `sample_inventory.csv`

### Hasil PBT (Kiro IDE + pytest)

```
15 passed in 110.14s
  P4 — CSV parser no crash (500 arbitrary byte inputs)
  P4 — DBF parser no crash (500 arbitrary byte inputs)
  P4 — Detector no crash (500 arbitrary byte inputs)
  P4 — Typed errors always (200 inputs)
  P3 — No block delimiter in dossier (1000 arbitrary texts)
  P3 — Injection attempts flagged (5 patterns × 100)
  P3 — HTML chars escaped (500 arbitrary texts)
  P6 — 51MB file rejected FILE_TOO_LARGE
  P6 — Empty file rejected
  P6 — Size within limit accepted (100 sizes)
  P6 — schema_version always present (200 inputs)
  P7 — Sandbox flags present in sandbox.sh
  P7 — Timeout 120s present
  P7 — Path traversal rejected (5 paths × 20)
  P7 — Hash deterministic (200 contents)
```

### Keputusan Teknis Utama

**Synth engine pakai `textContent` bukan `innerHTML`** — enforcement lewat code review di engine.py. P9 (XSS dari fixture berbahaya) dibuktikan lewat P3-C.

**Dedup via SHA-256** — artifact yang sama tidak diproses ulang, cukup kembalikan dossier yang ada. Efisien untuk demo.

**ddmin shrinker** — algoritma klasik delta debugging, O(n²) worst case tapi cukup untuk urutan pendek.

**MCP servers pakai stdin/stdout JSON-RPC** — tidak butuh HTTP server, bisa dipakai langsung di Kiro IDE.

**Ledger writer verifikasi chain sebelum append** — bila chain putus, otomatis mulai `entries-2.jsonl`. Tidak ada silent corruption.

### Pipeline Run Results

```
sample_contacts.csv:  csv 75% confidence | 6 fields | 1000 seq | 2/2 props | 0.4s
sample_inventory.csv: csv 80% confidence | 7 fields | 1000 seq | 2/2 props | 0.7s
Ledger: 16 entries, chain VALID
```

### Screenshot / Bukti

- `evidence/44bcc0c95acee61e/parity-report.json` — laporan paritas artefak 1
- `evidence/cb46bbe1bdc3ea57/parity-report.json` — laporan paritas artefak 2
- `apps/restored/44bcc0c95acee61e/index.html` — situs statis artefak 1
- `apps/restored/cb46bbe1bdc3ea57/index.html` — situs statis artefak 2
- `ledger/entries.jsonl` — 16 entries, chain valid

---

## Sesi 1 · 2026-11-20 · Fondasi Proyek

### Yang Dilakukan

Scaffolding penuh proyek: direktori, steering files, konfigurasi agen, hook, dan spec skeleton.

### Keputusan Integrasi Kiro

#### 1. Steering sebagai Penjaga Arsitektur

Enam steering files (`product.md`, `tech.md`, `structure.md`, `resurrection-doctrine.md`, `format-notes.md`, `security.md`) dimuat `always` — bukan `manual` — karena aturan keamanan dan larangan penciptaan harus aktif di setiap interaksi, bukan hanya saat manusia ingat untuk menyertakannya.

Alasan: steering yang di-manual itu seperti kebijakan keamanan yang harus dibaca dulu sebelum berlaku. Kebijakan keamanan yang baik berlaku sebelum kamu baca.

#### 2. Pemisahan Kekuasaan via Konfigurasi Agen

Setiap agen adalah berkas `.md` di `.kiro/agents/` dengan batas direktori yang tertulis eksplisit. Pemisahan ini bukan untuk keindahan arsitektur — ini untuk mencegah GOLEM (yang menulis UI) dari menulis ke `packages/parity/` (yang harusnya hanya REVENANT).

Alasan: pembangun tidak boleh memegang alat ukurnya sendiri. GOLEM yang menghasilkan UI tidak boleh juga yang memverifikasi hasilnya.

#### 3. Hook sebagai Kontrol Otomatis, Bukan Reminder

Lima hook dibuat bukan sebagai "nanti ingat untuk melakukan X" tapi sebagai kontrol yang berjalan otomatis:
- `guard-secrets` (PreToolUse) — blokir sebelum penulisan terjadi, bukan setelah
- `ledger-append` (PostTaskExec) — ledger ditulis otomatis, tidak bisa lupa
- `budget-alert` (PostToolUse) — anggaran diperiksa setiap tool call, bukan setiap jam
- `analyze-artifact` (PostFileCreate) — probe berjalan saat file masuk, bukan saat manusia ingat

Alasan: kontrol yang bergantung pada ingatan manusia bukan kontrol.

#### 4. Empat Spec dengan EARS Requirements

Spec ditulis dengan format EARS (Event-Action-Response-System) karena format itu memaksa kejelasan: "WHEN X, THE SYSTEM SHALL Y" tidak bisa kabur. Setiap spec punya `requirements.md`, `design.md`, dan `tasks.md` terpisah — iterasi di requirements tidak memaksa rewrite design.

#### 5. PBT di IDE Kiro

Property-Based Testing direncanakan untuk berjalan di Kiro IDE (saat harness paritas diimplementasikan di Hari 8-9) dengan Hypothesis sebagai cerminan CLI. Momen "menyalakan PBT di IDE" akan direkam sebagai tangkapan layar bukti untuk write-up.

---

## Template Entri Sesi Berikutnya

```markdown
## Sesi N · YYYY-MM-DD · [Judul]

### Yang Dilakukan
[Ringkasan task yang diselesaikan]

### Keputusan Integrasi Kiro
[Keputusan yang diambil dan alasannya]

### Hambatan
[Apa yang tidak berjalan seperti direncanakan]

### Screenshot / Bukti
[Link ke screenshot atau berkas bukti]
```

---

## Checklist Write-Up Kiro (8 Pertanyaan)

- [ ] **Q1 — Steering:** Bagaimana steering files membentuk perilaku agen?
  → `resurrection-doctrine.md`: larangan penciptaan dan data-bukan-perintah
  
- [ ] **Q2 — Agents:** Bagaimana agen terstruktur dan apa batas mereka?
  → 6 agen, pemisahan kekuasaan per direktori, dibuktikan dengan log audit
  
- [ ] **Q3 — Hooks:** Hook apa yang dipakai dan apa dampaknya?
  → 5 hook: guard-secrets, ledger-append, budget-alert, analyze-artifact, spec-diff-log
  
- [ ] **Q4 — Specs:** Bagaimana spec digunakan untuk memandu implementasi?
  → 4 spec dengan EARS requirements, design, dan tasks
  
- [ ] **Q5 — MCP:** Server MCP apa yang dibangun dan mengapa?
  → artifact-lab: tanpa ini agen tidak bisa menjalankan artefak sama sekali
  
- [ ] **Q6 — PBT:** Bagaimana property-based testing digunakan?
  → 4 properti, Hypothesis, dijalankan di IDE + CI, screenshot saat lulus
  
- [ ] **Q7 — Autonomy:** Bagaimana mode otonom dan gerbang persetujuan bekerja?
  → WATCHER orkestrasi, Gate 2 menahan semua commit sampai approve manusia
  
- [ ] **Q8 — Security:** Bagaimana keamanan terintegrasi ke pipeline?
  → Sandbox Docker, prompt injection blocking, PII gate, ledger immutable
