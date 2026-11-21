---
inclusion: always
---

# Format Notes — Quirk per Format

Catatan ini berisi hal-hal yang sering mengejutkan parser untuk setiap format yang didukung. Baca sebelum menulis codec baru.

---

## CSV / TSV (Format Prioritas 1)

**Quirk:**
- Header baris pertama tidak dijamin ada — deteksi dari konsistensi tipe kolom
- Delimiter bisa koma, titik koma, atau tab — deteksi dari sampel 10 baris pertama
- Encoding sering Windows-1252 atau Latin-1, bukan UTF-8 — selalu coba decode dengan fallback
- Nilai yang mengandung delimiter dibungkus quotes, tapi quotes bisa juga `'` atau tidak ada
- Baris kosong di tengah file sering berarti record yang dihapus, bukan akhir file
- Nomor sering diformat dengan titik ribuan (`1.000.000`) atau koma desimal (`3,14`)

**Strategi deteksi:**
```
magic bytes: tidak ada
fallback: buka sebagai teks, cari pola delimiter berulang
confidence: jumlah kolom konsisten / total baris
```

**Batas aman:**
- Jangan muat seluruh file ke memori — stream per baris
- Maksimum 10.000 baris untuk sampling — sisanya lewat streaming

---

## dBase / DBF (Format Prioritas 1)

**Quirk:**
- Header berisi metadata field yang berguna — nama, tipe, panjang, offset
- Tipe field: C (karakter), N (numerik), D (tanggal), L (logis), M (memo)
- Field memo disimpan di berkas `.dbt` atau `.fpt` terpisah — cek keberadaannya
- Tanggal dalam format `YYYYMMDD` tanpa separator
- Karakter padding dengan spasi atau null byte
- Record yang dihapus ditandai dengan byte `0x2A` di awal, bukan dihapus fisik
- Encoding sering tidak terdokumentasi — coba OEM 850, 437, lalu Latin-1

**Strategi deteksi:**
```
magic bytes: 0x03, 0x83, 0x8B, 0xF5 (byte pertama)
fallback: cari pola header DBF di 32 byte pertama
confidence: tinggi bila magic byte cocok + header valid
```

**Batas aman:**
- Verifikasi jumlah record dari header vs. ukuran file
- Bila tidak cocok, laporkan sebagai `unresolved` dengan batas yang diketahui
- Jangan ikuti pointer memo ke luar batas file

---

## Microsoft Access MDB (Format Prioritas 2)

**Quirk:**
- Format biner proprietary — gunakan `mdbtools` sebagai parser eksternal
- Bisa berisi banyak tabel, query, form, dan laporan — fokus ke tabel dan data
- Password protection di versi lama sering bisa dilewati dengan tools; catat sebagai temuan keamanan, jangan lewati
- Kolom AutoNumber sering dipakai sebagai primary key — pertahankan sebagai ID
- Tipe Memo bisa berisi RTF atau HTML — escape semua sebelum rendering

**Strategi deteksi:**
```
magic bytes: 0x00 0x01 0x00 0x00 'Standard Jet DB' atau 'Standard ACE DB'
confidence: tinggi bila magic byte cocok
```

---

## HTML Lama (Format Prioritas 2)

**Quirk:**
- Tag tidak ditutup, atribut tanpa quotes, case-insensitive — gunakan parser toleran (html.parser bukan lxml strict)
- `<font>`, `<center>`, `<marquee>` — elemen presentasi yang tidak semantik
- Frame dan frameset — arsitektur multi-dokumen yang perlu diresolusi
- Tabel dipakai untuk layout, bukan data — bedakan tabel data vs. tabel layout via heuristik (header, colspan/rowspan, kedalaman)
- JavaScript inline sering fungsional — catat sebagai unresolved, jangan eksekusi
- Gambar sering berupa path lokal yang rusak — catat sebagai unresolved

**Strategi deteksi:**
```
magic bytes: '<html', '<!DOCTYPE', '<HEAD' (case-insensitive, 100 byte pertama)
confidence: tinggi bila ada tag HTML valid
```

---

## Aturan Universal untuk Semua Format

1. **Deteksi dari isi, bukan ekstensi** — ekstensi berkas tidak dipercaya
2. **Confidence wajib dilaporkan** — 0.0 sampai 1.0, threshold default 0.7
3. **Encoding wajib dideteksi dan dicatat** — jangan asumsikan UTF-8
4. **Sampling dulu, baru full parse** — jangan muat file besar sebelum yakin format cocok
5. **Record yang rusak** — catat di `unresolved[]`, jangan lewati diam-diam
6. **Karakter kontrol** — escape semua karakter < 0x20 kecuali tab, LF, CR
