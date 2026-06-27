# Architecture Advisor

A Claude Code skill that recommends and persists the right software architecture for your project — or audits the one you already have.

## What it does

**detect → quiz → score → recommend → persist**

1. **Detects** your stack, team size, and deployment signals automatically before asking anything.
2. **Interviews** you with 6 targeted questions (pre-filled from detection — just correct what's wrong).
3. **Scores** the candidate architectures transparently: you see the table, not just the verdict.
4. **Recommends** one architecture with folder structure, trade-offs, and evolution path — using your real domain language.
5. **Persists** the decision into `CLAUDE.md`/`AGENTS.md` + a numbered ADR in `/adr`, with enforceable dependency rules and an optional dependency linter config.

Works for greenfield projects and for **auditing existing codebases** — detecting violations and generating an incremental migration plan.

## Architectures covered

Modular Monolith, Clean, Hexagonal/Ports & Adapters, Screaming, DDD, CQRS, Event-Driven, Microservices, Layered, Serverless, MVC/MVP/MVVM, Pipeline, Space-Based, and common hybrids.

## Install

```bash
npx skills add PabloViniegra/architecture-advisor
```

## Usage

Invoke explicitly — this skill does not trigger on architecture topics in passing:

```
/architecture-advisor
run the architecture advisor
help me choose an architecture
audit my current architecture
```

## What gets written to your repo

- `CLAUDE.md` — `## Architecture` section with pattern, folder structure, and enforceable rules
- `/adr/NNN-[slug].md` — ADR with context, decision, alternatives considered, Mermaid diagram, and review triggers
- `/adr/README.md` — ADR index (created or updated)
- *(optional)* Empty folder scaffold with per-layer READMEs
- *(optional)* Dependency linter config (`.dependency-cruiser.js` / `.importlinter` / `.go-arch-lint.yml`) wired to CI

## Requirements

- Claude Code with skills support
- `npx` (Node.js)
