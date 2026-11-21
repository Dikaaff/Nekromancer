# Synthetic Fixtures

Artefak sintetis untuk testing. Semua data adalah rekaan — bukan data pribadi nyata.

| File | Format | Deskripsi | Dipakai untuk |
|---|---|---|---|
| sample_contacts.csv | CSV | 10 kontak fiktif, era 1996–2001 | Smoke test ingest, codec CSV |
| sample_inventory.csv | CSV | 10 item inventaris fiktif, era 1997–1999 | Smoke test ingest, codec CSV |

## Aturan Fixture

1. **Tidak ada data nyata** — semua nama, alamat, dan nomor adalah rekaan
2. **Frozen setelah Hari 11** — tidak ada perubahan fixture setelah pembekuan fitur
3. **Versi dikontrol** — perubahan fixture harus lewat PR dengan alasan
4. **Corpus regresi** — bila artefak berbahaya ditemukan di lapangan, tambahkan versi sintetisnya ke sini

## Menambahkan Fixture Baru

```bash
# Taruh di fixtures/synthetic/
# Nama file: {deskripsi_singkat}.{ekstensi}
# Update tabel di README ini
# Commit dengan pesan: "fixtures: tambah {nama} untuk {alasan}"
```
