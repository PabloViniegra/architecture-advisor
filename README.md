# Architecture Advisor

A skill that recommends and persists a compatible software architecture composition for your project — or audits the one you already have.

## What it does

**detect → quiz → score by dimension → compose → persist**

1. **Detects** your stack, team size, and deployment signals automatically before asking anything.
2. **Interviews** you with 6 targeted questions (pre-filled from detection — just correct what's wrong).
3. **Scores** candidates inside separate dimensions such as deployment topology, internal boundaries, domain model, presentation, integration, and runtime.
4. **Recommends** one compatible composition with folder structure, trade-offs, and evolution path — using your real domain language.
5. **Persists** the decision into every agent-config file found (`AGENTS.md`/`CLAUDE.md`/Cursor/Copilot, else creates `AGENTS.md`) + a numbered ADR in `/adr`, with enforceable dependency rules and an optional dependency linter config.

Works for greenfield projects and for **auditing existing codebases** — detecting violations and generating an incremental migration plan.

## Architectures covered

Modular Monolith, Clean, Hexagonal/Ports & Adapters, Screaming, DDD, CQRS, Event-Driven, Microservices, Layered, Serverless, MVC/MVP/MVVM, Pipeline, Space-Based, and common hybrids.

## Install

```bash
npx skills add PabloViniegra/architecture-advisor
```

## Usage

Invoke explicitly by name — this skill does not trigger on architecture topics in passing:

```
/architecture-advisor
run the architecture advisor
audit my current architecture with the architecture advisor
```

## What gets written to your repo

- `AGENTS.md` and/or `CLAUDE.md` (every existing agent-config file found, else `AGENTS.md` created) — `## Architecture` section with composition, folder structure, and enforceable rules
- `/adr/NNN-[slug].md` — ADR with context, decision, alternatives considered, Mermaid diagram, and review triggers
- `/adr/README.md` — ADR index (created or updated)
- *(optional)* Empty folder scaffold with per-layer READMEs
- *(optional)* Dependency linter config (`.dependency-cruiser.js` / `.importlinter` / `.go-arch-lint.yml`) wired to CI

## Requirements

- Claude Code with skills support
- `npx` (Node.js)

## Validation

Run the offline contract checks from the repository root with Python 3.12 or newer:

```bash
python -B -m unittest discover -s tests -v
```

No packages, credentials, or model calls are needed. Python is only required for contributors running these checks, not for using the skill. GitHub Actions runs the same command on pushes and pull requests.

The suite reads the catalogue, quiz tags and point values directly from `skills/architecture-advisor/SKILL.md`. It checks:

- Candidate scores against [30 hand-calculated reference cases](tests/cases.md), including Q4/Q6 caps, conjunctions and multiple avoid hits. Every catalogue candidate has a case.
- Numeric scores in the published example scoreboard.
- Quiz choices and tags referenced by catalogue conditions, and consistency of the rubric's caps and maximum.
- Referenced rule files and dependency/placement sections for named, non-default patterns.
- Whether every optional candidate has a reachable, explicit catalogue threshold.

These are specification checks, not agent integration tests. The test-only evaluator implements the documented scoring notation; it is not a runtime recommendation engine. Unsupported notation fails rather than being silently ignored. Changes to that notation or the rubric's semantics need corresponding evaluator and case review.

The checks do not verify model compliance, tie-breaking, architectural suitability, generated files, consent, or linter execution. A reachable threshold is necessary but does not prove that a candidate can win with a valid combination of answers. Optional thresholds are deliberately stricter for candidates with fewer scoring signals: a lower threshold still requires all of their available positive categories and no avoid-condition hit.
