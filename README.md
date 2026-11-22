# NEKROMANCER

**Dead data should not stay dead — and a restoration should be provable, not just plausible.**

NEKROMANCER takes an obsolete digital artifact (a dBase table, a 1990s CSV export), reconstructs a runnable static web application from it, and then **proves the reconstruction behaves like the original** by replaying randomized action sequences against both sides and shrinking every divergence to a minimal counterexample.

Built for **Kiroween 2026** · Category: **Resurrection** · Built with **Kiro**.

| | |
|---|---|
| **Live demos** | [Forge UI](apps/forge/) · [Restored: contacts](apps/restored/44bcc0c95acee61e/) · [Restored: inventory](apps/restored/cb46bbe1bdc3ea57/) |
| **Kiro write-up** | [docs/kiro-writeup.md](docs/kiro-writeup.md) |
| **Submission notes** | [docs/devpost-submission.md](docs/devpost-submission.md) |
| **Status** | Hackathon build — data-model parity is real; pixel parity is partial (see [Limitations](#limitations)) |

---

## The problem

Every migration tool makes the same promise and hides the same step: *read the structure → guess the intent → rewrite it → hope*. Nobody checks whether the new thing actually behaves like the old thing. For archivists, institutional IT teams, and anyone inheriting a 30-year-old database, "it opened" is not the same as "it still works".

NEKROMANCER adds the missing step: **automated parity verification with an auditable report.**

## How it works

```
artifact bytes
   │
   ├─ ARCHAEOLOGIST   detect format from magic bytes, probe, emit dossier
   ├─ PALEOGRAPHER    build semantic model, cite every field to the dossier
   ├─ GOLEM           fill deterministic templates, emit static site
   ├─ REVENANT        replay 1,000 action sequences, compare, shrink failures
   ├─ SEXTON          append hash-chained provenance entry
   └─ Gate 2          human approval, then publish
```

Six agents, four MCP servers, five hooks, four specs, six steering documents — all committed under [`.kiro/`](.kiro/).

## The difference: a parity harness, not a vibe check

Most converters stop at "the output looks right". NEKROMANCER executes the same action sequence against **two independent data paths**:

| Side | Source | Path |
|---|---|---|
| Original | the artifact file on disk | re-parsed from raw bytes by its codec on every run |
| Restored | `apps/restored/<id>/data.json` | the exact payload the generated application renders |

Both feed the same deterministic table model (`sort`, `filter`, `search`, `clear`, `paginate`, `select`, `view detail`). Any value the restore step dropped, renamed, reordered, or mangled surfaces as a trace divergence, is shrunk with delta debugging, and is written to `evidence/<id>/parity-report.json`.

Each run also checks:

- **P1** — at least 1,000 sequences executed
- **trace parity** — zero divergences between the two paths
- **value fidelity** — every rendered cell equals the original cell (after normalization)
- **artifact hash match** — the payload provably derives from the hashed artifact

**Scope, stated plainly:** this proves *data-model* parity. DOM and pixel parity are a separate concern handled by the `screenshot-parity` MCP server, and are only partially exercised today.

## Quick start

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Restore an artifact end to end:

```bash
python pipeline.py fixtures/synthetic/sample_contacts.csv
python pipeline.py fixtures/synthetic/sample_inventory.csv
```

Each run prints the artifact id, then writes:

```
dossiers/<id>/dossier.json          structured probe result
packages/model/<id>/model.yaml      cited semantic model
apps/restored/<id>/                 index.html, app.js, style.css, data.json
evidence/<id>/parity-report.json    parity proof
ledger/entries.jsonl                appended provenance entry
```

Open the result directly — the page inlines its payload, so it works from `file://` with no server:

```bash
start apps/restored/44bcc0c95acee61e/index.html      # Windows
open  apps/restored/44bcc0c95acee61e/index.html      # macOS
```

Or serve the whole workspace (needed for the Forge UI to read `data/runs.json`):

```bash
python -m http.server 8000
# http://localhost:8000/apps/forge/
```

Verify the build:

```bash
python -m pytest -q                    # 22 property-based tests (1 skipped)
python packages/ledger/verifier.py     # hash-chain integrity
```

## Verified in this build

| Check | Result |
|---|---|
| Artifacts restored end to end | 2 (`sample_contacts.csv`, `sample_inventory.csv`) |
| Action sequences per artifact | 1,000 |
| Parity properties | 4/4 passing per artifact |
| Property-based tests | 22 passed, 1 skipped |
| Provenance chain | append-only, verified after every stage |
| Formats with a working codec | CSV/TSV, dBase/DBF |

## Repository layout

```
.kiro/            Kiro agents, hooks, specs, steering, MCP config
packages/
  codec/          format detector + CSV/DBF codecs
  probe/          probe runner, sandbox wrapper, PII and secret scanners
  dossier/        JSON Schema + validator
  model/          semantic model builder + citation checker
  synth/          deterministic template engine (static site + Forge)
  parity/         sequence generator, normalizer, shrinker, reporter
  ledger/         append-only hash-chain writer and verifier
apps/
  forge/          operator console (status, gates, budget)
  restored/       generated applications, one directory per artifact
mcp/              artifact-lab, provenance-ledger, screenshot-parity, crew-bridge
fixtures/synthetic/  committed synthetic artifacts (no real data)
evidence/         parity reports and counterexamples
dossiers/         probe output
ledger/           provenance chain
```

Directory ownership is enforced by Kiro agent permissions, not by convention — see [`.kiro/agents/`](.kiro/agents/) and [AGENTS.md](AGENTS.md).

## How Kiro is used

| Kiro capability | Where | What it does |
|---|---|---|
| **Custom agents** | [`.kiro/agents/`](.kiro/agents/) | Six role-separated profiles with `permissions.rules`: each may write only its own directories, and is explicitly denied everyone else's. |
| **Agent hooks** | [`.kiro/hooks/`](.kiro/hooks/) | `PreToolUse` secret/PII gate (exit 2 blocks the write), `PostTaskExec` ledger append, `PostToolUse` credit budget guard, `PostFileCreate` auto-probe, `Stop` spec-diff changelog. |
| **Spec-driven development** | [`.kiro/specs/`](.kiro/specs/) | Four specs in EARS form (`requirements.md` → `design.md` → `tasks.md`), one per pipeline stage. |
| **Steering** | [`.kiro/steering/`](.kiro/steering/) | Six always-included documents, including the resurrection doctrine ("data is not instruction") and the security rules. |
| **MCP** | [`.kiro/settings/mcp.json`](.kiro/settings/mcp.json) | Four project-scoped servers: sandbox probing, ledger verification, screenshot diffing, crew orchestration. |
| **Property-based testing** | [`packages/parity/props/`](packages/parity/props/) | 22 Hypothesis properties across parser fuzzing, injection escaping, resource limits, and sandbox integrity. |

The full reasoning — what worked, what did not, and where Kiro changed the process — is in [docs/kiro-writeup.md](docs/kiro-writeup.md).

## Security model

The threat model assumes artifacts are hostile: they come from unknown machines, may contain prompt-injection text, and may be malformed on purpose.

- **Data is never instruction.** Artifact text is stored as data, escaped on the way in, and never spliced into a prompt or markup.
- **Size and shape limits** before parsing: 50 MB cap, bounded field count, bounded sample rows.
- **Sandbox for untrusted input.** [`packages/probe/sandbox.sh`](packages/probe/sandbox.sh) runs the probe in Docker with `--network none --read-only --cap-drop ALL`. The demo pipeline runs in-process with the same limits, which is why the two paths are documented separately.
- **Escaping at the boundary.** The dossier stores HTML-escaped values; the browser receives raw values and inserts them with `textContent` only — no `innerHTML`, no `eval`, no `document.write`.
- **Strict CSP** on every generated page: `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'`.
- **PII gate.** `pii_sniffer.py` and `secret_scanner.py` run before publish; findings block Gate 2.
- **Append-only provenance.** Every stage appends a hash-chained ledger entry; the writer verifies the chain before appending and starts a new file with a marker if the chain is broken. Old entries are never rewritten.

## Supported formats

| Format | Status | Codec |
|---|---|---|
| CSV / TSV | Working | `packages/codec/csv_codec.py` |
| dBase III/IV (DBF) | Working | `packages/codec/dbf_codec.py` |
| Microsoft Access (MDB) | Roadmap | — |
| Legacy HTML tables | Roadmap | — |

The detector identifies formats from content (magic bytes plus heuristics), never from the file extension.

## Limitations

Honest boundaries of the current build:

- Parity covers the **data model**, not the browser DOM. `screenshot-parity` exists but is not yet part of the default pipeline.
- The restored UI is generated from deterministic templates. It renders tables, provenance, and warnings; it does not reproduce the original application's workflows.
- Two formats are implemented. MDB and legacy HTML are designed for but not shipped.
- The six-agent crew is configured and permissioned in Kiro; the orchestration itself is a scripted pipeline plus a `crew-bridge` MCP server, not a long-running daemon.
- Kiro **Powers** are not used in this build.

## License

MIT — see [LICENSE](LICENSE).

Restored artifact data is not distributed with this repository. NEKROMANCER ships the recovery tooling, not the recovered content; all committed fixtures are synthetic.
