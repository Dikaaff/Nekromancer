# Spec 0004 — Design

## Komponen

```
mcp/crew-bridge/
  server.py        ← MCP server: terima perintah dari WATCHER
  webhook.py       ← HTTP handler untuk /ingest
  scheduler.py     ← jadwal run berkala
  gate.py          ← implementasi Gate 1 dan Gate 2
  budget.py        ← tracking kredit per run
```

## Alur Gate

```
Gate 1 (otomatis):
  - dossier.format.confidence >= 0.7
  - dossier.unresolved.length <= ambang (default 10)
  - dossier valid terhadap skema
  → LULUS: lanjut ke PALEOGRAPHER
  → GAGAL: tulis ke ledger, lapor, berhenti

Gate 2 (menunggu manusia):
  - semua properti P0 lulus di parity-report.json
  - PII sniffer: tidak ada temuan aktif
  - CSP terpasang di semua halaman output
  → MENUNGGU: tampilkan di Forge, kirim notifikasi
  → APPROVE: commit ke branch, buat PR
  → REJECT: catat di ledger, status = rejected
```

## Budget Tracking

```python
# Setiap tool call dicatat
credits_used = 0

def track_tool_call(tool_name, estimated_cost):
    global credits_used
    credits_used += estimated_cost
    if credits_used > 300:
        raise BudgetExceeded(f"Run stopped: {credits_used} credits used")
    if credits_used > 400:
        kill_all_crew_sessions()
```
