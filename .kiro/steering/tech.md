---
inclusion: always
---

# NEKROMANCER — Tech Stack & Constraints

## Tumpukan Teknologi

### Backend / Pipeline
- **Python 3.11+** — semua paket inti (`packages/`)
- **Hypothesis** — property-based testing (cerminan CLI dari PBT Kiro IDE)
- **Docker** — isolasi sandbox eksekusi artefak
- **jsonschema** — validasi dossier.json
- **hashlib (sha256)** — rantai hash ledger

### Frontend / Output
- **HTML5 + CSS3 + Vanilla JS** — situs statis hasil restorasi (tanpa framework)
- **Jinja2** — template engine deterministik untuk GOLEM
- Tidak ada React, Vue, atau framework lain di output — portabilitas maksimal

### MCP Servers
- Ditulis dalam **Python** dengan FastMCP atau implementasi manual
- Empat server: `artifact-lab`, `provenance-ledger`, `screenshot-parity`, `crew-bridge`

### Forge UI (apps/forge/)
- **HTML + CSS + Vanilla JS** — bisa dibuka tanpa build step
- Aksesibel WCAG 2.2 AA
- Keyboard-navigable penuh

## Batasan Teknis

| Batasan | Nilai | Alasan |
|---|---|---|
| Ukuran artefak maks | 50 MB | Mencegah DoS |
| Rasio dekompresi maks | 100:1 | Mencegah zip bomb |
| Entri maks per artefak | 10.000 | Batas memori probe |
| Waktu probe maks | 120 detik | SLA performa |
| Waktu verifikasi maks | 180 detik | SLA performa |
| Total waktu per artefak | 15 menit | Kill switch |
| Anggaran kredit per run | 300 kredit | Kontrol biaya |
| Anggaran kredit per hari | 1.000 kredit | Kontrol biaya |

## Dependensi yang Dipatok

Semua dependensi menggunakan versi yang dipatok di lockfile (`requirements.txt` atau `uv.lock`). Tidak ada `>=` tanpa batas atas untuk dependensi keamanan-kritis.

## CI/CD

- `npm audit` / `pip-audit` wajib di CI
- SBOM dihasilkan per rilis
- Properti PBT dijalankan di CI (via Hypothesis)

## Output Requirements

- Semua output adalah berkas statis (HTML, CSS, JS, JSON, JSONL)
- Tidak ada backend yang dibutuhkan untuk menjalankan hasil restorasi
- Pipeline berjalan di Linux, macOS, dan WSL
