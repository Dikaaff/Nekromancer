# Devpost submission — working draft

Copy the relevant blocks into the Devpost form. Replace every `TODO` before submitting.

---

## Basics

- **Project name:** NEKROMANCER
- **Tagline:** Dead data should not stay dead — and a restoration should be provable.
- **Category:** Resurrection
- **Repo:** https://github.com/Dikaaff/Nekromancer
- **Demo URL:** `TODO` — GitHub Pages root (Forge UI + both restored apps)
- **Video:** `TODO` — YouTube, public, under 3 minutes
- **Blog post:** `TODO`
- **Social post:** `TODO`

## Description

**The problem.** Migrating a dead format is a leap of faith. Tools read the structure, guess the intent, rewrite the data, and stop. Nobody checks whether the rebuilt application actually behaves like the original. For an archivist or an IT team inheriting a 1990s database, "the file opened" is not the same as "the data still works".

**What NEKROMANCER does.** It takes an obsolete artifact, reconstructs a runnable static web application from it, and then proves the reconstruction is equivalent by replaying randomized action sequences against both sides.

1. **Probe** — the format is detected from content, not extension; the artifact is hashed, parsed with limits, and described in a cited dossier.
2. **Model** — every field in the semantic model must cite the dossier line it came from. A field without a citation is not allowed to become UI.
3. **Synthesize** — deterministic templates produce a static site with a strict CSP, `textContent`-only rendering, and an inlined data payload that runs from `file://`.
4. **Verify** — 1,000 randomized sequences (`sort`, `filter`, `search`, `clear`, `paginate`, `select`, `view detail`) run against the original artifact and against the payload the restored app renders. Divergences are shrunk to minimal counterexamples and written to an auditable report.
5. **Provenance** — every stage appends a hash-chained ledger entry; the chain is verified before each append.

**Why it is different.** Converters sell output. NEKROMANCER sells evidence. The parity report is the product: it states exactly what was compared, over how many sequences, with which normalization policy, and what failed.

**Verified in this build:** 2 artifacts restored end to end, 1,000 sequences each, 4/4 parity properties passing, 22 property-based tests passing, provenance chain verified.

## Built with

Python 3.10+, Kiro (IDE + CLI), Hypothesis, JSON Schema, MCP, vanilla HTML/CSS/JS, Docker (sandbox wrapper).

## How Kiro was used

Full write-up: [`docs/kiro-writeup.md`](kiro-writeup.md).

- **Custom agents** — six role-separated profiles with `permissions.rules`, so the component that builds the UI cannot write to the component that measures it, and the ledger writer cannot rewrite history.
- **Hooks** — a `PreToolUse` secret/PII gate that blocks writes (exit 2), `PostTaskExec` ledger append, `PostToolUse` credit budget guard, `PostFileCreate` auto-probe, `Stop` spec-diff changelog.
- **Specs** — four EARS-format specs, one per pipeline stage.
- **Steering** — six always-included documents, including the doctrine that artifact text is data, never instruction.
- **MCP** — four project-scoped servers (sandbox probing, ledger verification, screenshot diffing, crew orchestration).
- **PBT** — 22 Hypothesis properties across parser fuzzing, injection escaping, resource limits, and sandbox integrity.
- **Powers** — not used in this build.

## Testing instructions

No login, no setup required.

1. Open the demo URL. The landing page links to the Forge console and both restored applications.
2. **Forge console** (`/apps/forge/`) — pipeline runs, stage status, Gate 2 approval state, budget.
3. **Restored application** (`/apps/restored/44bcc0c95acee61e/`) — the artifact's rows rendered as a working table, with a provenance block (artifact id, SHA-256, detection method) and a downloadable parity report.
4. **Parity evidence** — `/evidence/44bcc0c95acee61e/parity-report.json` shows the sequences run, the properties, the normalization policy, and the exact sources compared.

To reproduce locally:

```bash
pip install -r requirements.txt
python pipeline.py fixtures/synthetic/sample_contacts.csv
python -m pytest -q
```

## Bonus prize checklist

| Bonus | Status | What is needed |
|---|---|---|
| Best Student Project | `TODO` | LinkedIn, student email, year, degree, school for **every** team member |
| Best Startup Project | `TODO` | Founder confirmation, LinkedIn, startup website |
| Best Ghost of Kiroween Past | `TODO` | Only if registered for Kiroween 2025 |
| Bonus Blog Prize | `TODO` | Public post during the submission period, must mention Kiroween 2026 |
| Social Blitz | `TODO` | Post starting with `#KiroweenHackathon26` |
| Best Kiro Crew App | Not applicable | Requires a separate Kiro Crew app repo |
| Best Demo | Automatic | Scored on the Presentation criterion |

## 3-minute video script

| Time | Shot | Voice-over |
|---|---|---|
| 0:00–0:15 | A dead file on disk, terminal cursor | "This is a 1990s database export. Every migration tool will convert it. None of them will prove the result still works." |
| 0:15–0:40 | `python pipeline.py fixtures/synthetic/sample_contacts.csv` running | "NEKROMANCER detects the format from the bytes, builds a cited model, and generates a runnable app." |
| 0:40–1:10 | Restored app in the browser, scrolling, provenance block | "Every field is cited back to the probe. Every value is rendered as text, under a strict CSP." |
| 1:10–1:50 | Parity report JSON, properties, counterexample shrink | "Then it proves equivalence: one thousand action sequences, replayed against the original artifact and against the payload the app renders. Divergences shrink to a minimal counterexample." |
| 1:50–2:20 | Forge UI, Gate 2, ledger chain verification | "A six-agent crew with enforced directory permissions, a hash-chained ledger, and a human approval gate." |
| 2:20–2:45 | Kiro config: agents, hooks, specs, steering, MCP | "Built with Kiro: six permissioned agents, five hooks, four specs, six steering documents, four MCP servers." |
| 2:45–3:00 | Title card | "Dead data should not stay dead. And a restoration should be provable." |

Constraints: no third-party trademarks, no copyrighted music, public on YouTube, under three minutes.

## Social post draft

```
#KiroweenHackathon26 The thing that changed how I build: Kiro's steering files are
always-on, so the security doctrine applied before I remembered the risk. I stopped
writing "don't do X" in prompts and started encoding it as permissions and hooks —
a PreToolUse hook that blocks a write is a control; a sentence in a prompt is a wish.
```

Hashtag must be the **first** thing in the post.
