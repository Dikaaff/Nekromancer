# Spec 0001 — Ingest & Probe

## Overview

Ingest adalah pintu masuk NEKROMANCER. Semua artefak masuk lewat sini, diidentifikasi, divalidasi batasnya, dan dijalankan dalam sandbox untuk menghasilkan dossier.

## Requirements (EARS Style)

### FR-1 · Penerimaan Berkas
- **WHEN** pengguna menjatuhkan berkas ke folder `fixtures/` atau mengirim webhook, **THE SYSTEM SHALL** menghitung SHA-256 berkas, mencatatnya, dan memulai pipeline.
- **WHEN** berkas yang sama (SHA-256 identik) sudah ada di corpus, **THE SYSTEM SHALL** mengembalikan dossier yang ada tanpa memproses ulang.

### FR-2 · Deteksi Format
- **WHEN** berkas diterima, **THE SYSTEM SHALL** mendeteksi format dari byte isi berkas, bukan dari ekstensi nama berkas.
- **WHEN** format tidak dikenali, **THE SYSTEM SHALL** berhenti dengan galat bertipe `FORMAT_UNKNOWN` dan tidak mengubah state repo.
- **WHEN** confidence deteksi di bawah 0.7, **THE SYSTEM SHALL** mencatat sebagai `unresolved` dan menunggu konfirmasi manusia.

### FR-3 · Sandbox Probe
- **WHEN** format terdeteksi, **THE SYSTEM SHALL** menjalankan probe dalam kontainer Docker dengan flag: `--network none --read-only --tmpfs /tmp:size=64m --cap-drop ALL --memory 512m --cpus 1`.
- **WHEN** probe melebihi 120 detik, **THE SYSTEM SHALL** mematikan kontainer dan melaporkan `PROBE_TIMEOUT`.
- **WHEN** probe selesai, **THE SYSTEM SHALL** menulis dossier ke `dossiers/{artifact_id}/dossier.json`.

### FR-4 · Validasi Dossier
- **WHEN** dossier ditulis, **THE SYSTEM SHALL** memvalidasinya terhadap `packages/dossier/schema.json`.
- **WHEN** validasi gagal, **THE SYSTEM SHALL** berhenti dengan galat bertipe `DOSSIER_INVALID` dan tidak melanjutkan ke tahap model.

### FR-5 · Batas Keamanan (P0)
- **WHEN** ukuran berkas > 50 MB, **THE SYSTEM SHALL** menolak dengan `FILE_TOO_LARGE`.
- **WHEN** rasio dekompresi > 100:1, **THE SYSTEM SHALL** menolak dengan `DECOMPRESSION_BOMB`.
- **WHEN** jumlah entri > 10.000, **THE SYSTEM SHALL** menolak dengan `ENTRY_LIMIT_EXCEEDED`.
- **WHEN** nama berkas dari ekstraksi mengandung path traversal (`..`, path absolut, symlink ke luar), **THE SYSTEM SHALL** menolak entri itu dan mencatat sebagai `PATH_TRAVERSAL_ATTEMPT`.

## Acceptance Criteria

- [ ] Berkas CSV 1 MB berhasil diproses dan menghasilkan dossier valid dalam < 120 detik
- [ ] Berkas dengan ekstensi `.csv` tapi isi DBF terdeteksi sebagai DBF
- [ ] Berkas 51 MB ditolak dengan `FILE_TOO_LARGE`
- [ ] Zip bomb (rasio > 100:1) ditolak dengan `DECOMPRESSION_BOMB`
- [ ] Berkas dengan format tidak dikenali berhenti dengan `FORMAT_UNKNOWN`, tidak ada perubahan di repo
- [ ] Probe yang berjalan > 120 detik dihentikan dengan `PROBE_TIMEOUT`
