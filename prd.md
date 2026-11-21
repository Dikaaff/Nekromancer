# NEKROMANCER — Product Requirements Document

> **Tagline:** sesuatu yang terkubur tidak harus tetap terkubur.  
> **Kategori lomba:** Resurrection

---

## 1. Ringkasan Produk

NEKROMANCER adalah alat pemulihan artefak digital yang mengubah berkas dari platform mati menjadi aplikasi web statis yang bisa dijalankan, disertai bukti bahwa perangkat lunak hasil pemulihan berperilaku setara dengan aslinya. Masukannya adalah byte mati; keluarannya adalah aplikasi yang hidup, plus berkas bukti yang bisa diaudit.

---

## 2. Masalah dan Pengguna

Kesenjangannya adalah tidak ada yang bisa **membuktikan** bahwa hasil konversi masih berperilaku sama. Semua konverter bekerja dengan cara yang sama: baca struktur, tebak maksud, tulis ulang, lalu berharap. Tidak ada langkah yang membandingkan perilaku lama dengan perilaku baru.

### Pengguna Primer
1. **Arsiparis digital & lembaga GLAM** — menyimpan artefak sebagai berkas mati, butuh aksesibilitas publik tanpa risiko salah tafsir.
2. **Tim TI institusional** — masih menjalankan basis data era 90-an, tidak berani menyentuhnya.
3. **Individu pemilik warisan digital** — disket atau direktori lama berisi kenangan, butuh sesuatu yang bisa dibuka di laptop modern.

### Pengguna Sekunder
- Pengembang pipeline migrasi yang butuh langkah verifikasi otomatis.

### Alternatif Saat Ini & Kelemahannya
| Alternatif | Kelemahan |
|---|---|
| Emulator manual + penampil berkas mentah | Data bisa dilihat, bukan aplikasi yang bisa dipakai |
| Penulisan ulang secara manual | Mahal, tetap tanpa verifikasi |
| Konverter satu arah | Tidak menyisakan jejak asumsi |

---

## 3. Sasaran dan Non-Sasaran

### Sasaran
- Memulihkan artefak ke aplikasi statis yang jalan
- Demonstrasi minimal 3 artefak dari minimal 2 format
- Membuktikan paritas perilaku secara otomatis
- Menyisakan ledger provenans yang bisa diaudit
- Beroperasi sebagai kru agen Kiro yang berjalan tanpa diawasi namun berhenti pada gerbang persetujuan

### Non-Sasaran (sengaja tertulis)
- ❌ Bukan emulator dengan kesetiaan penuh piksel-demi-piksel
- ❌ Bukan layanan hosting pusat untuk data pribadi
- ❌ Bukan mesin yang menerima format apa pun tanpa batas
- ❌ Bukan alat yang menyentuh konten artefak secara semantik

---

## 4. Metrik Keberhasilan

| Metrik | Target | Cara Ukur |
|---|---|---|
| Waktu restorasi per artefak | < 5 menit untuk berkas < 5 MB | Timer di Forge, ditulis ke laporan |
| Urutan aksi diuji per artefak | ≥ 1.000 | parity-report.json |
| Elemen UI tanpa sitasi | 0 | Properti P2, gagal build bila > 0 |
| Temuan PII yang terpublikasi | 0 | Gerbang deploy, dihitung sebagai insiden |
| Artefak yang berhasil dipulihkan | ≥ 3 dari ≥ 2 format | Korpus fixture |
| Batas biaya per artefak | ≤ 300 kredit | Hook anggaran, log per run |

---

## 5. Persona dan User Story

| Persona | Kebutuhan |
|---|---|
| Arsiparis | Serahkan artefak → terima aplikasi yang bisa ditautkan, tanpa tahu formatnya |
| Pengembang pipeline | Verifikasi paritas di CI tanpa membuka IDE |
| Pemilik warisan digital | Jatuhkan satu berkas → lihat hidup, tanpa baca dokumentasi |
| Auditor | Pastikan tidak ada yang diubah setelah bukti ditulis |

### Kriteria Penerimaan (EARS)
- **WHEN** pengguna menjatuhkan berkas dengan format tidak dikenali, **THE SYSTEM SHALL** berhenti dengan galat bertipe dan tidak mengubah state repo.
- **WHEN** probe selesai, **THE SYSTEM SHALL** menulis dossier tanpa memuat instruksi apa pun dari artefak sebagai perintah.
- **WHEN** sebuah elemen UI dihasilkan, **THE SYSTEM SHALL** menyertakan minimal satu sitasi ke dossier.
- **WHEN** urutan aksi ditemukan memecah paritas, **THE SYSTEM SHALL** menyusutkannya sampai minimal dan menulisnya ke `parity-report.json`.
- **WHEN** sniff PII menemukan data pribadi, **THE SYSTEM SHALL** memblokir deployment sampai diizinkan eksplisit.
- **WHEN** anggaran kredit sebuah run terlampaui, **THE SYSTEM SHALL** menghentikan seluruh agen run tersebut.

---

## 6. Arsitektur

**8 paket inti · 2 aplikasi · 4 server MCP · 6 agen**

| Paket | Tanggung Jawab | Pemilik (agen) | Boleh Menulis Ke |
|---|---|---|---|
| packages/dossier | Skema dossier.json, validasi, versi | Manusia | Semua |
| packages/probe | Deteksi format, orchestrate sandbox | ARCHAEOLOGIST | probe/ saja |
| packages/codec | Parser per format | ARCHAEOLOGIST | codec/ saja |
| packages/model | Model semantik + sitasi | PALEOGRAPHER | model/, dossiers/ |
| packages/synth | Generator dan template | GOLEM | synth/, apps/restored/ |
| packages/parity | Harness, grammar, generator urutan | REVENANT | parity/, evidence/ |
| packages/ledger | Rantai hash provenans | SEXTON | ledger/ saja |
| apps/forge | UI utama | GOLEM | apps/forge/ |

---

## 7. Kontrak Data

### dossier.json
```json
{
  "schema_version": "1.0",
  "artifact": { "id": "", "sha256": "", "size": 0, "name": "" },
  "format": { "family": "", "detected_by": "", "confidence": 0.0 },
  "structure": [{ "record": "", "field": "", "type": "", "byte_offset": 0 }],
  "samples": [],
  "unresolved": [],
  "warnings": []
}
```

### model.yaml
```yaml
entities: []
fields: []
labels: []
relations: []
rules: []
screens: []
# cite per elemen wajib
```

### parity-report.json
```json
{
  "sequences_run": 0,
  "properties": [{ "name": "", "status": "" }],
  "counterexamples": [{ "sequence": [], "cause": "" }],
  "normalization_policy": ""
}
```

### ledger/entries.jsonl
```
{"seq":1,"stage":"","input_hash":"","output_hash":"","prev_hash":"","actor":"","timestamp":""}
```

---

## 8. Alur End-to-End

```
[Ingest] → [Probe] → [Dossier] → ⛩ GATE 1 → [Model] → [Synth] → [Verify] → ⛩ GATE 2 → [Deploy]
```

1. **Ingest** — berkas diterima via drop/webhook, hash dihitung, korpus dicatat
2. **Probe** — sandbox deteksi + parsing berbatas waktu
3. **Dossier** — normalisasi ke skema
4. **Gate 1** — confidence < ambang atau unresolved terlalu besar → STOP
5. **Model** — PALEOGRAPHER menyusun model semantik + sitasi
6. **Synth** — GOLEM mengisi template (bukan free-write)
7. **Verify** — REVENANT jalankan ≥1.000 urutan, susutkan kegagalan, tulis laporan
8. **Gate 2** — persetujuan manusia sebelum commit & deploy

---

## 9. Kebutuhan Fungsional

### Ingest & Probe
| ID | P | Deskripsi |
|---|---|---|
| FR-1 | P0 | Terima berkas lokal dan folder drop |
| FR-2 | P0 | Deteksi format dari isi, bukan ekstensi |
| FR-3 | P0 | Jalankan probe dalam sandbox berbatas waktu dan memori |
| FR-4 | P0 | Validasi hasil terhadap skema, tolak yang tidak sesuai |
| FR-5 | P1 | Terima pemicu webhook dari release atau issue baru |

### Pemodelan
| ID | P | Deskripsi |
|---|---|---|
| FR-6 | P0 | Hasilkan model semantik dengan sitasi per elemen |
| FR-7 | P0 | Tolak menghasilkan UI untuk field tanpa dasar |
| FR-8 | P0 | Catat seluruh unresolved ke dossier dan README |
| FR-9 | P1 | Gabungkan dua dossier dari format berbeda menjadi satu model |

### Sintesis
| ID | P | Deskripsi |
|---|---|---|
| FR-10 | P0 | Hasilkan situs statis yang bisa dibuka tanpa server |
| FR-11 | P0 | Hasilkan dari template deterministik, LLM hanya mengisi slot teks |
| FR-12 | P0 | Ekspor lapisan data sebagai berkas terpisah |
| FR-13 | P1 | Sediakan tema yang bisa dipilih per artefak |

### Verifikasi
| ID | P | Deskripsi |
|---|---|---|
| FR-14 | P0 | Definisikan tata bahasa aksi per format |
| FR-15 | P0 | Jalankan minimal 1.000 urutan acak |
| FR-16 | P0 | Normalisasi trace sebelum membandingkan |
| FR-17 | P0 | Susutkan setiap kegagalan menjadi counterexample minimal |
| FR-18 | P0 | Serahkan laporan dengan properti, kebijakan normalisasi, dan penyebab |
| FR-19 | P1 | Simpan screenshot pembeda untuk kegagalan visual |

### Operasi Kru
| ID | P | Deskripsi |
|---|---|---|
| FR-20 | P0 | Kemas pipeline sebagai bot Crew dengan jadwal |
| FR-21 | P0 | Terima drop folder sebagai webhook |
| FR-22 | P0 | Tahan semua penulisan repo di balik gerbang persetujuan |
| FR-23 | P1 | Jalankan dua restorasi paralel |
| FR-24 | P1 | Ingat koreksi manusia sebagai pelajaran |

### Forge UI
| ID | P | Deskripsi |
|---|---|---|
| FR-25 | P0 | Tampilkan status run, dossier, laporan paritas, dan ledger |
| FR-26 | P0 | Sediakan tautan hasil |
| FR-27 | P0 | Sepenuhnya bisa dioperasikan dengan keyboard |
| FR-28 | P1 | Ekspor paket bukti sebagai satu arsip |

### Integrasi Kiro
| ID | P | Deskripsi |
|---|---|---|
| FR-29 | P0 | Sertakan /.kiro berisi steering, agents, hooks, specs, powers |
| FR-30 | P0 | Muat minimal satu property PBT yang dijalankan di IDE beserta tangkapan layar |
| FR-31 | P0 | Muat KIRO_JOURNAL.md |
| FR-32 | P1 | Kemas template menjadi Kiro power |

---

## 10. Kebutuhan Non-Fungsional

| Dimensi | Target |
|---|---|
| Probe selesai | < 120 detik untuk berkas 5 MB |
| Verifikasi selesai | < 180 detik |
| Forge responsif | < 200 ms untuk interaksi lokal |
| Total waktu per artefak | < 15 menit (lalu dibatalkan, state dibersihkan) |
| WCAG | 2.2 level AA |
| Navigasi keyboard | Penuh tanpa perangkap fokus |
| Kontras | Minimal 4.5:1 |
| Target sentuh | 24 piksel |
| Portabilitas | Linux, macOS, WSL |
| Anggaran per run | 300 kredit |
| Anggaran per hari | 1.000 kredit |

---

## 11. Integrasi Kiro

### Steering Files
| File | Isi |
|---|---|
| product.md | Visi dan non-sasaran |
| tech.md | Tumpukan teknologi dan batasan |
| structure.md | Peta paket dan aturan kepemilikan |
| resurrection-doctrine.md | Larangan penciptaan, kebijakan normalisasi, kewajiban sitasi |
| format-notes.md | Quirk tiap format |
| security.md | Ringkasan kontrol keamanan |

### Specs
- `0001-ingest` — Ingest & Probe
- `0002-parity` — Verifikasi Paritas
- `0003-forge-ui` — Forge UI
- `0004-crew-ops` — Operasi Kru

### Hooks
| Hook | Pemicu | Tindakan |
|---|---|---|
| analyze-artifact | PostFileCreate di fixtures/ | Jalankan probe + smoke test |
| guard-secrets | PreToolUse | Pindai rahasia & PII, blokir bila ketemu |
| ledger-append | PostTaskExec | Tambah entri ledger + hash |
| budget-alert | PostToolUse | Hitung kredit, hentikan bila lewat |
| spec-diff-log | Stop | Changelog dan pesan commit dari selisih spec |

### MCP Servers
| Server | Fungsi |
|---|---|
| artifact-lab | Jalankan emulator headless, kembalikan trace terstruktur |
| provenance-ledger | Baca dan verifikasi rantai hash |
| screenshot-parity | Bandingkan tangkapan layar |
| crew-bridge | Jembatani perintah Crew dengan repositori |

---

## 12. Keamanan

> **Prinsip:** NEKROMANCER tidak menerima data, ia menerima kode asing yang menyamar sebagai data.

### 5 Prinsip Pengikat
1. Tidak ada yang tepercaya secara default
2. Data bukan perintah (mutlak untuk semua teks dari artefak)
3. Hak paling sedikit untuk setiap agen
4. Bukti tidak bisa diubah setelah ditulis
5. Gagal tertutup — bila ragu, berhenti dan laporkan

### Kontrol Keamanan
| Kode | Ancaman | Kontrol | Bukti/Uji |
|---|---|---|---|
| S-1 | Kode jahat lewat artefak | Sandbox: tanpa jaringan, non-root, rootfs read-only, batas CPU/memori/waktu | Properti P7 |
| S-2 | Kerentanan parser | Fuzzing byte-level, timeout, batas kedalaman | Properti P4 |
| S-3 | DoS lewat berkas | Batas ukuran, rasio dekompresi, jumlah entri | Properti P6 |
| S-4 | Path traversal | Kanonikalisasi dan penolakan nama absolut | Uji P8 |
| S-5 | Prompt injection | Kutipan berbingkai, data tidak pernah jadi perintah | Properti P3 |
| S-6 | XSS dari data lama | Escape default, tanpa eval, CSP ketat | Uji P9 |
| S-7 | Agen menulis di luar hak | Batas direktori, allowlist tool, gerbang persetujuan | Audit log |
| S-8 | MCP jahat atau salah pakai | Skema argumen, tanpa shell, allowlist server | Uji P10 |
| S-9 | Kebocoran rahasia | Pindai pre-write, .env diabaikan, sanitasi log | Hook guard-secrets |
| S-10 | Publikasi data pribadi | Sniff PII, blokir deploy, korpus wajib sintetis | Gerbang deploy |
| S-11 | Bukti diubah | Rantai hash + tanda tangan Ed25519 | Verifikasi ledger |
| S-12 | Pelanggaran lisensi | Deteksi header hak cipta, catat SPDX, blokir redistribusi | Laporan provenans |
| S-13 | Denial of wallet | Anggaran per run, hook budget-alert, kill switch | Log biaya |

### Konfigurasi Sandbox (S-1, S-3, S-4)
```
--network none
--read-only
--tmpfs /tmp:size=64m
--cap-drop ALL
--security-opt no-new-privileges
--pids-limit 128
--memory 512m
--cpus 1
--user non-root
```
- Ukuran maksimum berkas: **50 MB**
- Rasio dekompresi maksimum: **100:1**
- Jumlah entri maksimum: **10.000**
- Batas waktu keras: **120 detik**

### 5 Gerbang Rilis
1. **Gerbang artefak** — ukuran, rasio, jumlah entri, nama
2. **Gerbang dossier** — skema valid, confidence di atas ambang
3. **Gerbang paritas** — semua properti P0 lulus
4. **Gerbang PII** — tidak ada data pribadi, atau izin eksplisit di ledger
5. **Gerbang publikasi** — CSP terpasang, semua ter-escape, lisensi lengkap

---

## 13. Risiko dan Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Ambisi format berlebihan | Demo setengah matang | Dua format utama + satu varian lite |
| Paritas terlalu ketat | Semua test merah | Tiga kategori perbedaan ditetapkan sejak hari kedua |
| Kredit bocor pada pekerjaan paralel | Pembangunan berhenti | Anggaran per run, mode model otomatis, kill switch |
| Parser rapuh pada berkas nyata | Pipeline gagal di demo | Korpus fixture dibekukan, jalur lite untuk berkas sulit |
| Waktu habis di bab keamanan | Submission tidak lengkap | Enam kontrol P0 selesai sebelum bab polish UI dimulai |

---

## 14. Milestone 14 Hari

| Hari | Target |
|---|---|
| 0–1 | Repo, LICENSE, .kiro/steering lengkap, enam berkas agen |
| 2–4 | Skema dossier, probe, codec format pertama, korpus fixture sintetis |
| 5–7 | Model semantik, generator template, Forge v0, artefak pertama hidup |
| 8–9 | Sandbox, batas sumber daya, hook keamanan, empat properti PBT |
| 10 | Harness paritas, grammar aksi, 1.000 urutan, penyusutan |
| 11 | Enam bot Crew, jadwal, webhook, gerbang persetujuan, ledger, pembekuan fitur |
| 12 | Video, deploy, blog, post sosial, draft Devpost |
| 13–14 | Audit kelima gerbang, pengiriman dini |

---

## 15. Definisi Selesai

Sebuah artefak disebut **selesai dipulihkan** bila:
1. Aplikasi hasil dapat dibuka tanpa server dan tanpa login
2. Tidak ada elemen UI tanpa sitasi
3. Minimal 1.000 urutan aksi dijalankan, setiap kegagalan dinyatakan sebagai counterexample atau unresolved
4. Seluruh alur tercatat di ledger dan tercermin di KIRO_JOURNAL.md

**Submission selesai** bila:
- Repo publik memuat `/.kiro` di root
- Lisensi terdeteksi di bagian About
- Video publik di bawah 3 menit
- Write-up 8 pertanyaan Kiro terisi
- Kelima gerbang rilis lulus

---

## 16. Yang Sengaja Tidak Dibangun

- Reproduksi setia piksel demi piksel dari aplikasi asal
- Dukungan lima format sekaligus
- Antarmuka multi-pengguna dengan autentikasi
- Layanan hosting pusat yang menyimpan artefak pengguna
- Mesin pembelajaran ulang yang memodifikasi parser secara otomatis

> Semua item di atas masuk **peta jalan**, bukan dikerjakan diam-diam dan berakhir setengah jadi.
