<div align="center">

# Architecture Advisor

A skill for resolving a concrete architectural decision with project evidence and
the smallest useful change. For existing systems and greenfield projects.

**Frame → inspect → compare → recommend → validate. Persist only on request.**

[![Validate skill contracts](https://github.com/PabloViniegra/architecture-advisor/actions/workflows/validate-skill.yml/badge.svg)](https://github.com/PabloViniegra/architecture-advisor/actions/workflows/validate-skill.yml)
![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-6f42c1)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![Markdown](https://img.shields.io/badge/Markdown-000000?logo=markdown&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=githubactions&logoColor=white)

</div>

## What you get

- A decision tied to a real workflow, not a quiz-selected architecture label.
- Evidence from relevant code and tests, separated from assumptions.
- Up to three options, including keeping the current approach.
- Hard constraints treated as requirements, not points that preferences can outweigh.
- A bounded next step, its trade-offs, a validation check, and a reason to revisit it.

“Do not migrate” and “measure this before deciding” are valid recommendations.
Patterns explain options; they do not dictate folders or introduce mechanisms by default.

## Install

```bash
npx skills add PabloViniegra/architecture-advisor
```

Use an agent supporting `SKILL.md` skills and repository inspection. Installation
through `npx` requires Node.js. The skill itself has no runtime dependencies.

## Usage

Invoke explicitly by name; architecture discussions alone do not activate the skill.

```text
/architecture-advisor
Our invoice rule changes touch HTTP and scheduled jobs. Help find the smallest fix.

Use architecture-advisor to decide whether notifications need independent releases.

Run architecture-advisor on this new internal tool. The first workflow is approving
expenses; we have one developer and must use the existing database and deployment.
```

For a broad audit, the skill starts with one representative workflow rather than
judging the whole application from its folder names. If the goal is unclear, it asks
a focused question instead of presenting a fixed questionnaire.

## Changes to your repository

**Advice and audits do not write files by default.** Accepting advice does not authorize
implementation or persistence. You can explicitly request an ADR, an implementation,
or a scoped change to agent instructions or enforcement tooling.

When recording a decision, the skill follows existing conventions, distinguishes the
current state from the target and active rules, and edits only the requested files.
It does not copy a policy into every agent config or create scaffolding automatically.

## Validation

Run the offline checks with Python 3.12 or newer:

```bash
python -B -m unittest discover -s tests -v
```

They check the skill's structure, local references, explicit safety contracts, and
evaluation-case integrity. No packages, credentials, or model calls are needed.
GitHub Actions runs the same command on pushes and pull requests.

**These checks do not demonstrate agent compliance or recommendation quality.**
Behavioral cases live in [tests/scenarios.json](tests/scenarios.json), with a repeatable
agent evaluation and blind comparison procedure in [tests/cases.md](tests/cases.md).
They cover restraint, hard constraints, evidence, uncertainty, transitions, consent,
and greenfield decisions. Agent evaluations must be run separately; no measured
usefulness improvement is claimed from passing the offline suite.

## Version 2

Version 2 replaces the fixed quiz, architecture scores, mandatory ADRs, and generic
rule catalogue with decision-oriented advice. Previously generated ADRs and agent
instructions are not automatically migrated or removed.

## Author

![Pablo Viniegra's stack, rendered by GitSkins](https://www.gitskins.com/api/section/stack?username=PabloViniegra&theme=frosted&style=aura)

Cards rendered by [GitSkins](https://www.gitskins.com/) from public GitHub data.
