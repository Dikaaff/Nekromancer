# How NEKROMANCER was built with Kiro

This is the write-up judges need: what Kiro features were used, how they changed the build, and where the limits were.

---

## 1. Which Kiro surfaces were used

| Surface | Used | Notes |
|---|---|---|
| **Kiro IDE** | Yes — primary | Spec authoring, agent profiles, hooks, steering, running property tests, reviewing generated diffs. |
| **Kiro CLI** | Yes — verification | Ran the pipeline and `pytest` from the CLI so the same specs and hooks applied outside the IDE. |
| **Kiro Web** | No | Not used; the project is local-first and has no cloud dependency. |
| **Kiro Crew** | Partially | The six-agent crew protocol is implemented as a `crew-bridge` MCP server plus per-agent profiles; it is not a hosted Kiro Crew app. |

The practical difference: the IDE is where the architecture was decided and where steering visibly changed answers; the CLI is where determinism was proven, because the same `.kiro/` configuration applies but nothing is interactive.

## 2. Custom agents — separation of powers as configuration

Six agents live in [`.kiro/agents/`](../.kiro/agents/), each with `tools`, `includeMcpJson`, and `permissions.rules`:

| Agent | May write | Explicitly denied |
|---|---|---|
| ARCHAEOLOGIST | `packages/probe/`, `packages/codec/` | ledger, dossiers, apps, parity, synth, model |
| PALEOGRAPHER | `packages/model/`, `dossiers/` | ledger, apps, evidence, probe, synth, parity |
| GOLEM | `packages/synth/`, `apps/restored/`, `apps/forge/` | parity, ledger, dossiers, evidence |
| REVENANT | `packages/parity/`, `evidence/` | apps, ledger, dossiers, synth, probe, model |
| SEXTON | `ledger/` only | everything else |
| WATCHER | nothing (`fs_write` denied for `**`) | all writes |

The point is not tidiness. The component that **builds** the UI must not be the component that **measures** whether the UI is equivalent, and the component that writes the ledger must not be able to rewrite history. Encoding that as `permissions.rules` means Kiro enforces it at the tool boundary; a prose instruction in a prompt would only be a suggestion.

Impact on the build: it removed a whole class of "helpful" cross-directory edits. When GOLEM needed a change in `packages/parity/`, the only path was to hand the finding back to REVENANT.

## 3. Agent hooks — controls, not reminders

Five hooks in [`.kiro/hooks/`](../.kiro/hooks/), all using the `v1` schema:

| Hook | Trigger | Behaviour |
|---|---|---|
| `guard-secrets` | `PreToolUse` | Scans the text about to be written; exits 2 to **block** the tool call on secrets or PII. |
| `ledger-append` | `PostTaskExec` | Appends a hash-chained provenance entry when a spec task completes. |
| `budget-alert` | `PostToolUse` | Accumulates credit usage; warns at 300, hard-stops at 400. |
| `analyze-artifact` | `PostFileCreate` | Runs probe + smoke assertions whenever a file lands in `fixtures/`. |
| `spec-diff-log` | `Stop` | Emits a spec-derived changelog and suggested commit message at session end. |

The design rule was: **if it depends on a human remembering, it is not a control.** `guard-secrets` is the clearest case — it runs before the write exists, so a leaked key is never written rather than deleted afterwards.

Hooks were also where the first real bug surfaced: the ledger hook called `writer.py` with flags that `argparse` treated as required, so the hook failed on every task. Fixing it meant making the writer derive `stage`, `actor`, and `output` from the hook payload. A hook that always errors is worse than no hook — it trains everyone to ignore the output.

## 4. Spec-driven development — EARS instead of vibes

Four specs in [`.kiro/specs/`](../.kiro/specs/), one per pipeline stage, each split into `requirements.md` → `design.md` → `tasks.md`.

Requirements are written in EARS form (`WHEN … THE SYSTEM SHALL …`), which forces the ambiguity out early. Two examples that survived into the code:

- *WHEN a field has no citation, THE SYSTEM SHALL NOT render it as UI.* This became the `cite` requirement in `model.yaml` and the P2 property.
- *WHEN a probe fails, THE SYSTEM SHALL write a typed error to `unresolved[]` and SHALL NOT continue to the next stage.* This is why `pipeline.py` returns early on a probe failure instead of producing a half-restored app.

Compared to vibe coding, the difference is not speed on the first draft — it is speed on the **fifth** change. Iterating on requirements did not force a rewrite of the design, and the task list stayed a checklist instead of a memory exercise.

## 5. Steering — the rules that must apply before you read them

Six always-included documents in [`.kiro/steering/`](../.kiro/steering/):

- `product.md` — vision, non-goals (explicitly: no pixel-perfect UI reproduction, no multi-user auth, no central hosting)
- `tech.md` — stack, dependency policy, pinned versions
- `structure.md` — directory ownership
- `resurrection-doctrine.md` — "data is not instruction", fail-closed, citation required
- `format-notes.md` — per-format parsing notes and known traps
- `security.md` — sandbox flags, escaping rules, CSP baseline

The single highest-leverage strategy was making security and doctrine **always-included rather than manual**. A security policy you have to remember to attach is a policy that applies only when you already remembered the risk.

Concretely, `resurrection-doctrine.md` stopped a recurring failure mode: treating text found inside an artifact as an instruction. It is the reason every codec escapes values at parse time and every UI insertion goes through `textContent`.

## 6. MCP — capabilities the agent otherwise would not have

Four servers, configured for the project in [`.kiro/settings/mcp.json`](../.kiro/settings/mcp.json):

| Server | Tool | Why it had to be MCP |
|---|---|---|
| `artifact-lab` | `detect_format`, `run_probe`, `execute_sequence` | Runs the artifact out-of-process and returns a structured trace; the agent gets evidence, not a shell session. |
| `provenance-ledger` | verify / append | The agent can read the chain but cannot rewrite it. |
| `screenshot-parity` | `compare_screenshots`, `save_diff` | Pixel comparison with Pillow, results written to `evidence/`. |
| `crew-bridge` | run orchestration, gates, budget | Gives WATCHER a control surface without granting it write access to the repo. |

`execute_sequence` is the one that changed the design: once the agent could ask "what does the original artifact do when I sort column 2 descending, then filter by 'Jakarta'?" and get a real trace back, the parity harness stopped being a mock and became a test.

## 7. Property-based testing — where unit tests were blind

22 Hypothesis properties in [`packages/parity/props/`](../packages/parity/props/):

| Property | What it asserts | Example of what it caught |
|---|---|---|
| **P3** injection | Dossier strings never contain block delimiters; HTML characters are escaped | A fixture value containing `===` would have terminated a data block early. |
| **P4** parser fuzzing | Arbitrary bytes never crash the CSV/DBF parser; failures are typed | Truncated DBF headers produced an untyped `struct.error` before the property existed. |
| **P6** resource limits | Oversized, empty, and boundary-size inputs are rejected deterministically | The 50 MB cap was off by one boundary case. |
| **P7** sandbox integrity | Required Docker flags are present; path traversal is rejected; hashes are deterministic | A `..` path in an output name escaped the dossier directory. |

PBT was the right tool here because the input space is adversarial and effectively infinite: files from unknown machines, in unknown encodings, possibly malformed on purpose. Example-based tests covered the fixtures I imagined; the properties covered the ones I did not.

## 8. What I would do differently

- **Use Powers.** This build does not use Kiro Powers. For a security-sensitive pipeline, a bundled security-review power would likely have replaced several hand-written checks.
- **Wire MCP from day one.** The servers were written before `.kiro/settings/mcp.json` existed, which meant Kiro never actually loaded them during most of the build. Configuration that lives in a "copy this later" note is configuration that does not exist.
- **Make the hook contract a test.** Every hook command should be executed by CI with a sample payload. Two of five were broken on first run.
- **Record the parity scope earlier.** The first harness compared two simulated traces, which proved nothing. Writing down "what exactly is being compared" before writing the harness would have saved the rewrite.

---

*Written as part of the Kiroween 2026 hackathon.*
