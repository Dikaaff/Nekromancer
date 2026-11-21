# 🔮 NEKROMANCER

> **sesuatu yang terkubur tidak harus tetap terkubur.**

NEKROMANCER mengubah artefak digital mati menjadi aplikasi web statis yang bisa dijalankan — dan **membuktikan** bahwa hasil pemulihan berperilaku setara dengan aslinya.

**Kategori:** Resurrection — Kiro Skills Idea Hackathon

---

## Apa yang Membedakan Ini dari Konverter Biasa

Semua konverter bekerja sama: baca struktur → tebak maksud → tulis ulang → berharap. Tidak ada yang membandingkan perilaku lama dengan perilaku baru.

NEKROMANCER menambahkan satu langkah yang tidak ada di tempat lain: **verifikasi paritas otomatis**. ≥1.000 urutan aksi dijalankan pada artefak asli dan pada hasil restorasi. Setiap perbedaan dicatat, disusutkan ke counterexample minimal, dan dilaporkan. Hasilnya bisa diaudit.

---

## Arsitektur Singkat

```
Artefak masuk
  → ARCHAEOLOGIST (probe + dossier)
  → PALEOGRAPHER (model semantik + sitasi)
  → GOLEM (situs statis dari template)
  → REVENANT (1000+ urutan aksi, laporan paritas)
  → SEXTON (ledger provenans)
  → Gate 2 (persetujuan manusia)
  → Publish
```

6 agen · 4 MCP server · 5 hook · 4 spec · 6 steering files

---

## Cara Pakai (Demo)

```bash
# 1. Jatuhkan artefak ke folder fixtures/
cp my-old-database.dbf fixtures/drop/

# 2. WATCHER mendeteksi dan memulai pipeline otomatis
# 3. Buka Forge UI untuk melihat progress
open apps/forge/index.html

# 4. Setelah Gate 2, approve dari Forge UI
# 5. Aplikasi hasil tersedia di:
open apps/restored/{artifact_id}/index.html
```

---

## Format yang Didukung

| Format | Status | Codec |
|---|---|---|
| CSV / TSV | ✅ P0 | `packages/codec/csv.py` |
| dBase / DBF | ✅ P0 | `packages/codec/dbf.py` |
| Microsoft Access MDB | 🔄 P2 | `packages/codec/mdb.py` |
| HTML lama | 🔄 P2 | `packages/codec/html_legacy.py` |

---

## Keamanan

Semua eksekusi artefak terjadi dalam sandbox Docker yang terisolasi penuh (`--network none`, `--read-only`, `--cap-drop ALL`). Teks dari artefak tidak pernah menjadi instruksi — lihat [resurrection-doctrine.md](.kiro/steering/resurrection-doctrine.md).

---

## Struktur Proyek

```
.kiro/           ← steering, agents, hooks, specs
packages/        ← 7 paket inti
apps/            ← Forge UI + hasil restorasi
mcp/             ← 4 MCP server
fixtures/        ← artefak untuk testing
evidence/        ← laporan paritas + counterexample
dossiers/        ← dossier hasil probe
ledger/          ← rantai hash provenans
```

Lihat [structure.md](.kiro/steering/structure.md) untuk aturan kepemilikan direktori.

---

## Progress

Lihat [progress.md](progress.md) untuk status task per hari.

## Jurnal Kiro

Lihat [KIRO_JOURNAL.md](KIRO_JOURNAL.md) untuk log keputusan integrasi Kiro.

---

## Lisensi

MIT — lihat [LICENSE](LICENSE)

> Data artefak yang dipulihkan bukan milik proyek ini. NEKROMANCER hanya mendistribusikan skrip pemulihan, bukan kontennya.
