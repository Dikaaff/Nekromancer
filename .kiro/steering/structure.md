---
inclusion: always
---

# NEKROMANCER — Package Structure & Ownership Rules

## Peta Direktori

```
NEKROMANCER/
├── .kiro/
│   ├── steering/          # Konteks selalu dimuat
│   ├── specs/             # 4 spec fitur inti
│   ├── agents/            # Konfigurasi 6 agen
│   └── hooks/             # 5 hook otomasi
├── packages/
│   ├── dossier/           # Skema + validator (dimiliki: Manusia)
│   ├── probe/             # Deteksi format + sandbox (dimiliki: ARCHAEOLOGIST)
│   ├── codec/             # Parser per format (dimiliki: ARCHAEOLOGIST)
│   ├── model/             # Model semantik + sitasi (dimiliki: PALEOGRAPHER)
│   ├── synth/             # Generator template (dimiliki: GOLEM)
│   ├── parity/            # Harness PBT + grammar (dimiliki: REVENANT)
│   └── ledger/            # Rantai hash provenans (dimiliki: SEXTON)
├── apps/
│   ├── forge/             # Forge UI (dimiliki: GOLEM)
│   └── restored/          # Aplikasi hasil restorasi (dimiliki: GOLEM)
├── mcp/
│   ├── artifact-lab/      # MCP: emulator headless
│   ├── provenance-ledger/ # MCP: verifikasi rantai hash
│   ├── screenshot-parity/ # MCP: perbandingan screenshot
│   └── crew-bridge/       # MCP: jembatan perintah Crew
├── fixtures/
│   └── synthetic/         # Artefak sintetis untuk testing
├── evidence/              # Output PBT dan laporan paritas
├── dossiers/              # Dossier hasil probe per artefak
├── ledger/                # entries.jsonl — rantai hash provenans
├── agents.md              # Roster agen (dokumen ini)
├── prd.md                 # PRD lengkap
├── progress.md            # Progress tracker
├── KIRO_JOURNAL.md        # Jurnal integrasi Kiro
└── README.md
```

## Aturan Kepemilikan (WAJIB DIPATUHI)

Agen hanya boleh menulis ke direktori yang tertulis di baris mereka. Hook `guard-secrets` (PreToolUse) menegakkan ini.

| Paket/Direktori | Pemilik | Agen Lain |
|---|---|---|
| packages/dossier/ | Manusia | Semua boleh baca |
| packages/probe/ | ARCHAEOLOGIST | Hanya baca |
| packages/codec/ | ARCHAEOLOGIST | Hanya baca |
| packages/model/ | PALEOGRAPHER | Hanya baca |
| dossiers/ | PALEOGRAPHER | Hanya baca |
| packages/synth/ | GOLEM | Hanya baca |
| apps/restored/ | GOLEM | Hanya baca |
| apps/forge/ | GOLEM | Hanya baca |
| packages/parity/ | REVENANT | Hanya baca |
| evidence/ | REVENANT | Hanya baca |
| ledger/ | SEXTON | Hanya baca |

## Aturan Tambahan

1. **Tidak ada agen yang menulis ke direktori root** — hanya manusia
2. **Tidak ada cross-writes** — GOLEM tidak boleh menulis ke `packages/parity/`, dll.
3. **WATCHER hanya membaca** — tidak ada penulisan langsung dari orchestrator
4. **Semua perubahan ke branch sementara** — tidak ada commit langsung ke `main` tanpa persetujuan manusia
5. **Ledger hanya append** — tidak ada update atau delete entri lama
