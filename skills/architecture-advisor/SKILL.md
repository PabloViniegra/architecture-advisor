---
name: architecture-advisor
description: >
  MANUAL USE ONLY — only invoke this skill when the user explicitly asks for it by name
  or says something like "run the architecture advisor", "use the architecture skill",
  or "help me choose an architecture with the advisor". Do NOT trigger automatically
  when architecture topics come up in conversation. When invoked: recommends and persists
  the best software architecture for a project by auto-detecting the stack, running a
  scored quiz, recommending a compatible architecture composition by dimension, and writing the decision into AGENTS.md / CLAUDE.md (whichever exists,
  defaulting to AGENTS.md as the open standard) plus a numbered ADR in /adr. Covers the full spectrum (Modular Monolith, Clean, Hexagonal, Screaming, DDD,
  CQRS, Event-Driven, Microservices, Layered, Serverless, MVC/MVP/MVVM, Pipeline,
  Space-Based, hybrids). Can also audit an existing codebase and propose an incremental
  migration plan.
---

# Architecture Advisor

A structured decision engine: **detect → quiz → score by dimension → compose → persist**. It works for greenfield projects and for auditing existing codebases, and it always leaves behind enforceable rules and an ADR so the decision doesn't erode over time.

---

## Phase 0 — Auto-detect project context

**Before asking anything**, inspect the project to pre-fill the quiz. Keep detection fast and bounded — the goal is provisional context, not exhaustive analysis.

**Scope limit:** read at most 20 files total across all categories below. Prioritise root-level files first; go one level deeper only if root gives insufficient signal. If a project is too large to infer from this sample, say so in the pre-fill and leave those fields blank rather than guessing.

Look for and read what's relevant:
- **Language & deps** (root only): `package.json`, `go.mod`, `pyproject.toml`/`requirements.txt`, `pom.xml`, `Cargo.toml`, `composer.json`
- **Existing structure**: list top-level folders only (`src/`, `modules/`, `domain/`, `cmd/`, `internal/`, `services/`, `functions/`) — do not recurse
- **Deployment signals** (root only): `Dockerfile`, `docker-compose.yml`, `serverless.yml`, one `*.tf` file if present, `vercel.json`
- **Scale/team signals**: `nx.json`, `turbo.json`, `pnpm-workspace.yaml` — count top-level service/app folders in a monorepo, no deeper
- **Existing decisions**: check for `/adr`, `/docs/adr`, `/docs/decisions` folders and read only `README.md` or the most recent ADR if present; read `## Architecture` section in `AGENTS.md`/`CLAUDE.md` (check both) if either exists

From this, infer provisional answers (e.g. "Go + Chi + Redis, single `cmd/` + `internal/`, Dockerfile present → likely a single-team service on containers"). Present these inferences alongside the quiz so the user just adjusts them.

If a prior architecture decision already exists, say so and offer to **revise/supersede** it rather than duplicate (see Phase 4 on ADR superseding).

---

## Phase 0.5 — Greenfield or audit?

Decide the branch based on detection:

- **Little/no code** → greenfield path: quiz → recommend → scaffold (optional) → persist.
- **Substantial existing code** → offer the **audit path**: analyse the current architecture, detect violations, and propose an incremental migration. Ask the user which they want:
  - "Recommend an architecture for this project from scratch", or
  - "Audit the architecture you already have and plan a migration."

The audit path is covered in Phase 5.

---

## Phase 1 — Quiz Interview

Present all questions **at once**, pre-filled with Phase 0 inferences shown in brackets. The user replies with letters or just confirms (`looks right` / `2 should be C, rest ok`).

Use this exact question set:

**Q1 — What type of system is this?** *(pick one)* `[detected: ...]`
- A) Customer-facing web/mobile product (SaaS, marketplace, app)
- B) Internal tool or back-office system
- C) API / platform consumed by other teams or third parties
- D) Data pipeline, ETL, or analytics system
- E) Embedded system, IoT, or hardware integration

**Q2 — How complex is the business domain?** *(pick one)*
- A) Simple CRUD — mostly read/write records, few rules
- B) Moderate — some rules, a few workflows, a handful of entities
- C) Complex — rich domain logic, many edge cases, rules change often
- D) Very complex — multiple subdomains, compliance/audit, financial or legal rules

**Q3 — Team size and structure?** *(pick one)* `[detected: ...]`
- A) Solo or pair
- B) 2–5 engineers, single team
- C) 6–15 engineers, single or two teams
- D) 15+ engineers, multiple autonomous teams

**Q4 — Top priorities?** *(pick up to 3)*
- A) Ship fast — time to market
- B) Easy to change — maintainability
- C) High test coverage — tests non-negotiable
- D) Scale parts independently
- E) Fault isolation
- F) Team autonomy — independent deploys
- G) Low infrastructure cost

**Q5 — Project stage?** *(pick one)* `[detected: ...]`
- A) Greenfield — from scratch
- B) Early product — small, may change direction
- C) Established — refactoring/evolving existing
- D) Legacy migration — extracting from a monolith/old system

**Q6 — Which constraints apply?** *(pick any, then add optional free text)* `[detected, not yet confirmed: ...]`
- A) Independent deployments are required (`independent_deployments`)
- B) Strict audit history is required (`strict_auditability`)
- C) Reads and writes have very different scale or models (`asymmetric_reads_writes`)
- D) Workflows are asynchronous or event-led (`asynchronous_workflows`)
- E) Traffic is highly variable (`variable_traffic`)
- F) Workloads are long-running or stateful (`long_running_stateful`)
- G) DevOps capacity is limited (`limited_devops`)
- H) The same core needs multiple inbound or outbound adapters (`multiple_adapters`)
- I) Domain experts are available (`domain_experts_available`)
- J) Extreme real-time scale is a proven requirement (`extreme_realtime_scale`)
- K) None of these

The user may add stack, infrastructure, deadline, or other context after the selected letters. Free text informs the explanation and folder examples, but **never changes a score directly**. Only confirmed Q6 tags may affect scoring. Detection may propose tags, but the user must confirm them first.

If answers are contradictory (e.g. Q3:A + Q4:F), flag it in one sentence before scoring.

---

## Phase 2 — Transparent scoring by dimension + recommendation

Don't force unrelated architecture concepts into one ranking. Score candidates within their dimension, show the work, then compose a compatible recommendation.

### 2.1 Show the scoreboard

Produce one compact table with the winner and runner-up in each relevant dimension. Include the numeric score, star rating, and a one-line reason tied to confirmed answers.

**Scoring rubric — apply mechanically, not by feel:**

Each candidate starts at 0. Compare candidates only within the same dimension. Score every candidate against the user's answers using this table:

| Signal | Points |
|---|---|
| Q1 matches a "best-fit" signal for this pattern | +1 |
| Q2 matches a "best-fit" signal | +1 |
| Q3 matches a "best-fit" signal | +1 |
| At least one selected Q4 priority matches this candidate's best-fit signals | +1 |
| Q5 matches a "best-fit" signal | +1 |
| A confirmed Q6 tag matches this candidate's best-fit signals | +1 |
| Any answer matches an "avoid when" condition | −2 (cap: −2 per pattern total) |

Maximum: 6 points. Convert to stars: 6=★★★★★, 5=★★★★☆, 3–4=★★★☆☆, 1–2=★★☆☆☆, 0 or below=★☆☆☆☆. Always show the numeric score in parentheses so the rating is auditable.

In the catalogue, ranges such as `Q3:A-B` mean A or B. A `+` between signals means all are required. Commas separate independent scoring signals or avoid conditions.

Deployment topology and internal boundaries are baseline dimensions: select one winner in each. Domain model, presentation, data and integration, and runtime are optional overlays: include a non-default candidate only when it scores at least 3 without an avoid-condition hit. Evaluate each data and integration candidate independently because CQRS, EDA, and Pipeline may coexist.

For ties, prefer in this order: fewer avoid-condition hits, lower operational complexity, then the earlier candidate in the dimension table. State the tie-break used.

Example output for `Q1:A, Q2:D, Q3:C, Q4:B/C/D, Q5:A, Q6:D/E/H/I`:

```
## Architecture fit (based on your answers)

| Dimension | Winner | Score | Runner-up | Why |
|---|---|---:|---|---|
| Deployment topology | Modular Monolith | 3/6 ★★★☆☆ | Single deployable (2/6) | Q3:C, Q4:B and Q5:A favour explicit module boundaries in one deployable |
| Internal boundaries | Clean Architecture | 3/6 ★★★☆☆ | Hexagonal (2/6) | Q2:D, Q4:B-C and Q5:A favour inward dependencies; Hexagonal matches Q4 and confirmed Q6:H |
| Domain model | DDD | 3/6 ★★★☆☆ | Screaming (2/6) | Q2:D, Q4:B-C and confirmed Q6:I justify DDD |
| Presentation pattern | None | — | MVC (-1/6) | Q1:A matches MVC, but Q2:D triggers its avoid condition |
| Data and integration | None | — | EDA (2/6) | Q4:D and confirmed Q6:D are insufficient to reach the optional-overlay threshold |
| Runtime model | Conventional runtime | — | Serverless (2/6) | Q4:D and confirmed Q6:D/E are insufficient to reach the optional-overlay threshold |
```

### 2.2 Architecture dimensions and catalogue

Choose at most one candidate from each dimension except data and integration, where independently justified patterns may be combined. "None" or the stated default is a valid result. Patterns from different dimensions may be composed.

| Dimension | Candidate | Best-fit signals | Avoid when |
|---|---|---|---|
| **Deployment topology** | Single deployable (default) | Q3:A-B, Q4:A-G, Q5:A-B | Q3:D + Q6:`independent_deployments` |
| | Modular Monolith | Q3:B-C, Q4:B, Q5:A-C | Q3:D + Q6:`independent_deployments` |
| | Microservices | Q3:D, Q4:D-F, Q6:`independent_deployments` | Q3:A-B, Q5:A-B, Q6:`limited_devops` |
| | Space-Based | Q4:D-E, Q6:`extreme_realtime_scale` | Q3:A-C, Q6:J not confirmed |
| **Internal boundaries** | Layered (N-Tier) | Q1:B, Q2:A, Q3:A-B, Q4:A | Q2:C-D |
| | Clean Architecture | Q2:C-D, Q4:B-C, Q5:A-C | Q2:A + Q5:A |
| | Hexagonal / Ports & Adapters | Q1:C, Q4:B-C, Q6:`multiple_adapters` | Q2:A + Q3:A + Q6:H not confirmed |
| **Domain model** | No additional domain pattern (default) | Q2:A-B | No avoid condition |
| | Screaming Architecture | Q2:C-D, Q4:B | Q2:A |
| | DDD | Q2:D, Q4:B-C, Q6:`domain_experts_available` | Q2:A, Q6:I not confirmed |
| **Presentation pattern** | None (default) | Q1:B-E | No avoid condition |
| | MVC / MVP / MVVM | Q1:A, Q2:A-B | Q2:C-D |
| **Data and integration** | None (default) | Default; no score required | No avoid condition |
| | CQRS | Q4:D, Q6:`asymmetric_reads_writes`, Q6:`strict_auditability` | Q2:A-B, Q3:A-B + neither Q6:B nor Q6:C confirmed |
| | Event-Driven / EDA | Q1:C, Q4:D-F, Q6:`asynchronous_workflows` | Q3:A-B + Q6:D not confirmed |
| | Pipeline / Pipes & Filters | Q1:D | Q1:A-B |
| **Runtime model** | Conventional runtime (default) | Default; no score required | No avoid condition |
| | Serverless | Q4:D-G, Q6:`variable_traffic`, Q6:`asynchronous_workflows` | Q6:`long_running_stateful` |

**Common compositions**
- **Modular Monolith + Clean** — single team, growing, complex-ish domain, wants optionality
- **DDD + Hexagonal** — complex domain that must stay infra-agnostic
- **DDD + CQRS + Event Sourcing** — audit-heavy financial/legal
- **Microservices + Event-Driven** — large org, autonomous teams
- **Screaming + Clean** — domain visibility without losing testability

### 2.3 Recommendation

After the dimension scoreboard, commit to one compatible composition with this structure:

```
## Recommendation: [Composition name]

### Decisions by dimension
- Deployment topology: [winner]
- Internal boundaries: [winner]
- Domain model: [winner or none]
- Presentation pattern: [winner or none]
- Data and integration: [winner or none]
- Runtime model: [winner]

### Why this wins for you
[Reference their explicit Q1–Q5 answers and confirmed Q6 tags]

### In practice
[Code organisation, where logic lives, test strategy]

### Trade-offs you're accepting
[Be direct]

### Watch out for
[Failure modes + mitigations]

### Evolution path
[What to adopt when you outgrow this — ties to the ADR review triggers]

### Folder structure
[Concrete tree using domain language from detected code and the user's free-text context — never UserService/OrderRepo placeholders]
```

---

## Phase 3 — Persist the decision

After the user confirms, write everything **without asking permission** (except scaffolding + linter, see 3.4). This is the expected output of the skill.

### 3.1 Detect the agent config file
Scan for all of: `AGENTS.md`, `CLAUDE.md`, `.cursor/rules`/`CURSOR_RULES.md`, `COPILOT.md`, `.github/copilot-instructions.md`.

- **If multiple exist** → write the `## Architecture` section into **every one of them**. Keep the content identical across files.
- **If exactly one exists** → write into that one.
- **If none exist** → create `AGENTS.md` — it is the most tool-agnostic format (recognised by Claude, Codex, Gemini CLI, Amp, and others).

### 3.2 Write the `## Architecture` section

Apply this check **per file** (each target file is checked independently):

- **No `## Architecture` section exists in this file** → add it directly, no confirmation needed.
- **`## Architecture` section already exists in this file** → show the user what's there and ask for explicit confirmation before replacing it. Example:

> "I found an existing `## Architecture` section in AGENTS.md (pattern: Layered, dated 2024-03-10). Replace it with the new decision (Modular Monolith + Clean, today)? This will also create ADR-002 superseding ADR-001."

When writing to multiple files, batch the confirmation into a single question if more than one has an existing section. Never delete unrelated content in any file.

```markdown
## Architecture

**Architecture composition:** [Name(s)]
**Decision date:** [YYYY-MM-DD]  
**Status:** Accepted  
**ADR:** /adr/NNN-[slug].md

### Guiding principles
- [Principle 1]
- [Principle 2]

### Folder structure
[Concrete tree, real domain names]

### Rules for contributors
[ENFORCEABLE rules — copy from references/enforceable-rules.md for the chosen pattern,
adapted to the user's folders. e.g. "domain/ must never import infrastructure/"]

### Why we chose this
[1-2 sentences matching the ADR]
```

**The rules must be enforceable, not vague prose.** Read `references/enforceable-rules.md` and copy the dependency + placement rules for the chosen architecture (merge rule sets for hybrids). Every architecture in that file has a matching rule set — use it.

### 3.3 ADR — always created
See Phase 4. The ADR is mandatory; `/adr` is created if absent.

### 3.4 Optional scaffolding + linter (ASK first)
Ask the user two yes/no questions:

1. **"Want me to scaffold the empty folder structure?"** — if yes, create the folder tree with `.gitkeep` files and a short `README.md` in each layer/module explaining what belongs there. Use their real domain names.
2. **"Want a dependency linter wired up so these rules are enforced in CI?"** — if yes, generate the matching config from `references/enforceable-rules.md`:
   - TS/JS → `.dependency-cruiser.js`
   - Python → `import-linter` config (`.importlinter` / `setup.cfg`)
   - Go → `.go-arch-lint.yml`
   Add a one-line run command (e.g. `npx depcruise --config .dependency-cruiser.js src`).

### 3.5 Confirmation summary
```
✅ Architecture decision persisted:
- [list every file written, e.g. AGENTS.md ✓, CLAUDE.md ✓] — ## Architecture section written (with enforceable rules)
- /adr/NNN-[slug].md — ADR created [folder + index created ✓ if new]
- [scaffold: created N folders ✓ / skipped]
- [linter: .dependency-cruiser.js created ✓ / skipped]

Commitment: [one sentence — composition, why this team, what it buys them]
```

---

## Phase 4 — ADR handling (robust numbering + index)

**Always create an ADR. Create `/adr` if it doesn't exist — do not ask.**

Folder preference: if `/docs/adr` or `/docs/decisions` already exist, use them; otherwise default to `/adr`.

**Numbering:** list existing `*.md` ADRs, find the highest `NNN` prefix, use the next integer zero-padded to 3 digits. Empty/new folder → `001`. Never reuse or collide.

**Filename:** `NNN-[architecture-name-slug].md` (e.g. `003-modular-monolith-clean.md`).

**Index:** maintain `/adr/README.md` as a table of all ADRs (number, title, status, date). Create it if missing; append the new row.

**Superseding:** if an accepted architecture ADR already exists and this decision changes it, set the old ADR's status to `Superseded by ADR-NNN` and set the new one's `Supersedes: ADR-MMM`. Don't silently duplicate.

**ADR structure — write it as a `.md` file with these exact sections:**

`# ADR-[NNN]: [Architecture Name]` — top-level heading.

Frontmatter block (bold key/value pairs):
- `**Date:**` YYYY-MM-DD
- `**Status:**` Accepted
- `**Deciders:**` from the user's free-text context, or "Project team"
- `**Supersedes:** ADR-MMM` — include only if replacing a prior decision

`## Context` — synthesise Q1–Q6 + Phase 0 detection into one paragraph: what the system does, team size, domain complexity, scale expectations, stack, constraints.

`## Decision` — list the selected result for each dimension, then state "We adopt **[Composition]**." Follow with 1–2 paragraphs on what this means concretely for this project.

`## Considered alternatives` — table with columns Dimension / Alternative / Score / Reason not chosen. Compare alternatives only inside their dimension. Use the scores from Phase 2 and tie the reasoning to confirmed answers.

`## Consequences` — two sub-lists: Positive (tied to Q4 priorities) and Negative (trade-offs accepted).

`## Implementation notes` — enforceable rules summary + folder structure + naming conventions, copied and adapted from `references/enforceable-rules.md`. If the audit path was used, include the `## Migration plan` subsection here with steps in `todo/in progress/done` status.

`## Architecture diagram` — a Mermaid `graph TD` or `flowchart TD` block showing layers/contexts and the direction of dependencies. Make it faithful to the chosen pattern (e.g. for Clean, arrows point inward; for Modular Monolith, show module boundaries and the shared kernel). This section is mandatory — a diagram communicates dependency direction far better than a folder tree. If the user has the Excalidraw MCP connected and prefers a richer visual, offer to generate one there instead.

`## Review triggers` — bulleted list of concrete conditions that should prompt revisiting this decision (e.g. "Team passes 10 engineers → reconsider service split", "Read/write ratio exceeds 20:1 → add CQRS on read side").

---

## Phase 5 — Audit existing codebase (migration path)

When the user picks the audit branch (Phase 0.5):

1. **Map the current architecture.** Read the folder structure and a sample of imports. Identify the de-facto pattern (or lack of one).
2. **Detect violations** against the target architecture's rules in `references/enforceable-rules.md`:
   - Business logic living in controllers/handlers
   - `domain`/`core` importing infrastructure
   - Circular dependencies between modules
   - Cross-module reach-ins bypassing public surfaces
   - Database shared across would-be service boundaries
   List each violation with file references and severity.
3. **Propose an incremental migration**, not a rewrite. Order steps by leverage and risk:
   - Quick wins first (move misplaced files, introduce interfaces at the worst seams)
   - Then structural moves (extract a module, invert a dependency)
   - Defer the expensive/risky ones, with the trigger that would justify them
4. **Persist** the *target* architecture exactly as in Phases 3–4, plus a `## Migration plan` section in the ADR's implementation notes listing the ordered steps and their current status (`todo`/`in progress`/`done`).
5. Offer to wire the linter now so new violations are caught immediately even before the migration completes.

---

## Tone and approach
- Always run Phase 0 detection first — pre-filled quizzes respect the user's time.
- Show the scoreboard before the verdict; a justified decision is a trusted decision.
- Be opinionated and commit to one recommendation.
- Rules you write must be enforceable, tied to `references/enforceable-rules.md`.
- Use the user's real domain language everywhere — never generic placeholders.
- For early-stage projects, push back on over-engineering: a clean modular monolith beats a premature microservices disaster.
