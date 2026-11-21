# Spec 0002 — Parity Verification

## Overview

Verifikasi paritas adalah fitur yang membedakan NEKROMANCER dari konverter biasa. REVENANT membuktikan bahwa aplikasi hasil restorasi berperilaku setara dengan artefak asli untuk ≥ 1.000 urutan aksi.

## Requirements (EARS Style)

### FR-14 · Grammar Aksi
- **WHEN** format artefak teridentifikasi, **THE SYSTEM SHALL** memuat grammar aksi yang sesuai dari `packages/parity/grammar/{format}.yaml`.
- **WHEN** grammar tidak tersedia untuk format tersebut, **THE SYSTEM SHALL** mencatat sebagai `unresolved` dan melewati verifikasi paritas untuk artefak itu.

### FR-15 · Urutan Acak
- **WHEN** harness paritas dijalankan, **THE SYSTEM SHALL** menghasilkan minimal 1.000 urutan aksi acak dari grammar.
- **THE SYSTEM SHALL** menyimpan seed generator sehingga urutan bisa direproduksi.

### FR-16 · Normalisasi Trace
- **WHEN** dua trace dibandingkan, **THE SYSTEM SHALL** menormalisasi keduanya sesuai kebijakan di `resurrection-doctrine.md` sebelum membandingkan.
- **THE SYSTEM SHALL** mencatat kebijakan normalisasi yang diterapkan di `parity-report.json#normalization_policy`.

### FR-17 · Penyusutan Kegagalan
- **WHEN** urutan aksi menghasilkan perbedaan, **THE SYSTEM SHALL** menyusutkannya ke counterexample minimal yang masih mereproduksi kegagalan.
- **THE SYSTEM SHALL** mencatat counterexample di `parity-report.json#counterexamples`.

### FR-18 · Laporan Paritas
- **WHEN** semua urutan selesai dijalankan, **THE SYSTEM SHALL** menulis laporan ke `evidence/{artifact_id}/parity-report.json` dengan format yang sesuai kontrak data.
- **THE SYSTEM SHALL** menyebut setiap properti dengan status `pass` atau `fail`, kebijakan normalisasi, dan penyebab setiap kegagalan.

## Acceptance Criteria

- [ ] 1.000 urutan dijalankan dan dilaporkan untuk artefak CSV pertama
- [ ] Counterexample yang ditemukan disusutkan ke urutan terpendek yang mereproduksi kegagalan
- [ ] parity-report.json valid terhadap kontrak data
- [ ] Kebijakan normalisasi tercatat di laporan
- [ ] Seed generator tercatat sehingga run bisa direproduksi
