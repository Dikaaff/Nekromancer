# Spec 0003 — Forge UI

## Overview

Forge adalah dashboard utama yang menampilkan status setiap run, dossier, laporan paritas, dan ledger. Bisa dioperasikan sepenuhnya dengan keyboard dan memenuhi WCAG 2.2 AA.

## Requirements (EARS Style)

### FR-25 · Status & Data
- **WHEN** Forge dibuka, **THE SYSTEM SHALL** menampilkan daftar run dengan status (pending, in-progress, done, failed).
- **WHEN** run dipilih, **THE SYSTEM SHALL** menampilkan dossier, laporan paritas, dan entri ledger untuk run tersebut.

### FR-26 · Tautan Hasil
- **WHEN** restorasi selesai, **THE SYSTEM SHALL** menyediakan tautan langsung ke `apps/restored/{artifact_id}/index.html`.
- **WHEN** laporan paritas tersedia, **THE SYSTEM SHALL** menyediakan tautan ke `evidence/{artifact_id}/parity-report.json`.

### FR-27 · Aksesibilitas (WAJIB)
- **THE SYSTEM SHALL** memenuhi WCAG 2.2 level AA.
- **THE SYSTEM SHALL** memungkinkan navigasi keyboard penuh tanpa perangkap fokus.
- **THE SYSTEM SHALL** memiliki rasio kontras minimal 4.5:1 untuk semua teks.
- **THE SYSTEM SHALL** menghormati `prefers-reduced-motion`.
- **THE SYSTEM SHALL** menyediakan label ARIA yang bermakna untuk semua elemen interaktif.

## Acceptance Criteria

- [ ] Semua fungsi bisa diakses tanpa mouse
- [ ] Kontras > 4.5:1 diverifikasi dengan axe atau Lighthouse
- [ ] Tidak ada perangkap fokus
- [ ] Forge bisa dibuka sebagai file HTML lokal tanpa server
- [ ] Semua tautan ke dossier, laporan, dan ledger berfungsi
