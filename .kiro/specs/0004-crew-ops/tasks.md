# Spec 0004 — Tasks

- [ ] Buat `mcp/crew-bridge/server.py` — MCP server skeleton
- [ ] Buat `mcp/crew-bridge/webhook.py` — HTTP handler /ingest
- [ ] Buat `mcp/crew-bridge/gate.py` — evaluasi Gate 1 dan Gate 2
- [ ] Buat `mcp/crew-bridge/budget.py` — tracking kredit per run
- [ ] Implementasi kill switch di budget.py (> 300 → stop run, > 400 → kill all)
- [ ] Implementasi gerbang persetujuan manual (Forge UI menampilkan tombol Approve/Reject)
- [ ] Test: run yang melebihi 300 kredit dihentikan
- [ ] Test: Gate 2 menahan commit sampai ada persetujuan
