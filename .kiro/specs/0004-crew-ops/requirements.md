# Spec 0004 — Crew Operations

## Overview

Pipeline NEKROMANCER berjalan sebagai kru agen Kiro yang bisa dijadwalkan dan dipicu via webhook. WATCHER mengorkestrasi semua agen dengan gerbang persetujuan manusia sebelum commit.

## Requirements (EARS Style)

### FR-20 · Pipeline sebagai Kru
- **WHEN** run dijadwalkan, **THE SYSTEM SHALL** menjalankan seluruh pipeline (ingest → verify) tanpa intervensi manusia, kecuali di gerbang persetujuan.
- **THE SYSTEM SHALL** melaporkan status setiap tahap ke Forge UI secara real-time.

### FR-21 · Webhook Trigger
- **WHEN** webhook diterima di endpoint `/ingest`, **THE SYSTEM SHALL** memvalidasi payload dan memulai pipeline untuk artefak yang diterima.

### FR-22 · Gerbang Persetujuan
- **WHEN** Gate 2 tercapai (semua properti P0 lulus, PII clear), **THE SYSTEM SHALL** menahan semua commit dan menunggu persetujuan manusia.
- **WHEN** persetujuan diberikan, **THE SYSTEM SHALL** melakukan commit ke branch sementara dan membuat PR.
- **WHEN** persetujuan ditolak, **THE SYSTEM SHALL** mencatat penolakan di ledger dan membiarkan run dalam status `rejected`.

### FR-Kill Switch
- **WHEN** kredit run > 300, **THE SYSTEM SHALL** menghentikan seluruh run dan melaporkan.
- **WHEN** kredit run > 400, **THE SYSTEM SHALL** mematikan semua sesi Crew aktif.

## Acceptance Criteria

- [ ] Run dijadwalkan bisa berjalan dari ingest ke Gate 2 tanpa intervensi
- [ ] Webhook `/ingest` memulai pipeline dengan payload artefak
- [ ] Gate 2 menahan commit sampai ada persetujuan eksplisit
- [ ] Kill switch berjalan saat kredit > 300
- [ ] Semua event pipeline tercatat di ledger
