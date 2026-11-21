# Spec 0001 — Design

## Komponen

```
fixtures/
  drop/            ← polling setiap 5 detik
packages/probe/
  runner.py        ← orchestrate sandbox, timeout, hash
  sandbox.sh       ← docker run wrapper dengan flag isolasi
  pii_sniffer.py   ← scan PII sebelum dossier disimpan
packages/codec/
  detector.py      ← magic bytes + heuristik, kembalikan (format, confidence)
  csv.py           ← parser CSV/TSV
  dbf.py           ← parser dBase/DBF
dossiers/
  {sha256[:8]}/
    dossier.json   ← output utama
packages/dossier/
  schema.json      ← JSON Schema validator
  validate.py      ← CLI validator
```

## Alur Data

```
berkas masuk
  → hash SHA-256
  → cek duplikat (dossiers/ sudah ada?)
    → ya: kembalikan dossier lama
    → tidak: lanjut
  → cek batas (ukuran, rasio, entri)
    → gagal: galat bertipe, berhenti
  → detector.py → (format, confidence)
    → confidence < 0.7: unresolved, tunggu konfirmasi
    → format unknown: FORMAT_UNKNOWN, berhenti
  → sandbox.sh → codec/{format}.py
    → timeout: PROBE_TIMEOUT, berhenti
    → sukses: tulis /tmp/output/dossier.json
  → salin dari /tmp/output/ ke dossiers/{sha256[:8]}/
  → validate.py → dossier valid?
    → tidak: DOSSIER_INVALID, berhenti
  → SEXTON: catat entri ledger
  → lanjut ke PALEOGRAPHER
```

## Format dossier.json

Lihat `packages/dossier/schema.json` untuk skema lengkap.

## Keputusan Desain

| Keputusan | Pilihan | Alasan |
|---|---|---|
| Deteksi format | Magic bytes + heuristik | Ekstensi tidak dipercaya |
| Sandbox | Docker | Isolasi terkuat yang tersedia |
| Hash | SHA-256 | Standard, cepat, cukup untuk dedup |
| Polling vs inotify | Polling 5 detik | Portabel di Linux/macOS/WSL |
