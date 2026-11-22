# NEKROMANCER — Build Status

> Last updated: 2026-11-22. Status: 🟢 done · 🟡 in progress · 🔴 not started

## Milestones

| Milestone | Status | Evidence |
|---|---|---|
| 0–1 · Repo, license, `.kiro/` foundation, six agents | 🟢 | `.kiro/agents/`, `LICENSE` |
| 2–4 · Dossier schema, probe, codecs, synthetic fixtures | 🟢 | `packages/dossier/`, `packages/codec/`, `fixtures/synthetic/` |
| 5–7 · Semantic model, template engine, Forge v0, first live artifact | 🟢 | `packages/model/`, `packages/synth/`, `apps/forge/` |
| 8–9 · Sandbox wrapper, resource limits, security hooks, four PBT properties | 🟢 | `packages/probe/`, `packages/parity/props/` |
| 10 · Parity harness, action grammars, 1,000 sequences, shrinker | 🟢 | `packages/parity/`, `evidence/` |
| 11 · Six agent profiles, MCP servers, approval gate, ledger | 🟢 | `mcp/`, `ledger/`, `.kiro/settings/mcp.json` |
| 12 · Video, deploy, blog, social, Devpost draft | 🟡 | `docs/devpost-submission.md` |
| 13–14 · Five-gate audit, tag, submit | 🔴 | — |

## Verified numbers

| Metric | Value |
|---|---|
| Artifacts restored end to end | 2 |
| Action sequences per artifact | 1,000 |
| Parity properties passing | 4/4 per artifact |
| Property-based tests | 22 passed, 1 skipped |
| Provenance chain | valid, append-only |
| Formats with a working codec | 2 (CSV/TSV, DBF) |
| Release gates passed | 0/5 (audit scheduled) |

## Remaining work

- [ ] **T-070** Record the demo video (under 3 minutes, public on YouTube)
- [ ] **T-071** Publish the static demo (GitHub Pages: repo root)
- [ ] **T-072** Fill in the Devpost form from `docs/devpost-submission.md`
- [ ] **T-073** Social post — hashtag `#KiroweenHackathon26` must be first
- [ ] **T-074** Blog post — must mention Kiroween 2026
- [ ] **T-080** Gate 1 audit: artifact size, ratio, entry count, naming
- [ ] **T-081** Gate 2 audit: dossier schema, confidence thresholds
- [ ] **T-082** Gate 3 audit: all parity properties passing
- [ ] **T-083** Gate 4 audit: PII clear or permission recorded
- [ ] **T-084** Gate 5 audit: CSP, escaping, license
- [ ] **T-085** Final commit, tag `v1.0.0`
- [ ] **T-086** Submit on Devpost

## Log

```
[2026-11-20] Foundation, codecs, model, synth, parity, ledger, MCP, Forge.
[2026-11-21] Two artifacts restored; 15 property tests passing.
[2026-11-22] Critical fixes:
             - CSP: added connect-src 'self' (fetch was blocked by default-src 'none')
             - Restored apps now inline their payload and run from file://
             - Parity harness rewritten: executes the original artifact and the
               restored payload for real (previously both sides were simulated)
             - MCP wired at .kiro/settings/mcp.json; agents gained permissions.rules
             - Hook schema fixed (timeout at hook level); broken commands repaired
             - Ledger writer accepts hook payloads; budget guard implemented
             - README, Kiro write-up, and Devpost draft rewritten in English
```

## Design decisions worth remembering

- **Builders must not measure their own work.** GOLEM writes the UI; REVENANT measures it. Enforced by agent permissions.
- **Data is not instruction.** Artifact text is escaped at parse time and inserted with `textContent` only.
- **Fail closed.** A failed probe writes a typed error and stops; it does not produce a half-restored app.
- **Append-only history.** The ledger writer verifies the chain before appending and never edits old entries.
- **State the scope.** The parity harness proves data-model parity, not pixel parity. Saying so is part of the product.
