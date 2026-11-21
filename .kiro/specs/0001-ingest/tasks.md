# Spec 0001 — Tasks

- [ ] Buat `packages/dossier/schema.json` — JSON Schema untuk dossier.json
- [ ] Buat `packages/dossier/validate.py` — CLI validator
- [ ] Buat `packages/probe/sandbox.sh` — Docker wrapper dengan semua flag isolasi
- [ ] Buat `packages/probe/runner.py` — orchestrate probe, timeout, hash
- [ ] Buat `packages/codec/detector.py` — deteksi format dari magic bytes
- [ ] Buat `packages/codec/csv.py` — parser CSV/TSV dengan encoding detection
- [ ] Buat `packages/codec/dbf.py` — parser dBase/DBF
- [ ] Buat 3 fixture sintetis di `fixtures/synthetic/`
- [ ] Tulis smoke test: CSV 1MB → dossier valid
- [ ] Tulis smoke test: file 51MB → FILE_TOO_LARGE
- [ ] Tulis smoke test: format unknown → FORMAT_UNKNOWN, repo tidak berubah
