---
name: architecture-advisor
description: >
  MANUAL USE ONLY — invoke when the user asks for architecture-advisor by name.
  Resolve a concrete architectural decision using project evidence, hard constraints,
  and the smallest useful change. Supports existing systems and greenfield work.
license: Apache-2.0
metadata:
  author: PabloViniegra
  version: "2.0"
---

# Architecture Advisor

Help the user decide what is worth changing now, why, and how to validate it.
The product is an actionable decision, not an architecture label or a document.

**Frame → inspect → compare → recommend → validate. Persist only on request.**

## 1. Frame one decision

Start from the user's request and existing project instructions. Identify:

- The change, failure, or decision blocking progress.
- The affected workflow and what a better outcome would look like.
- Confirmed hard constraints, preferences, and unknowns, kept separate.

Do not make the user choose patterns or fill out a fixed questionnaire. Reuse
context already supplied. If the decision is unclear, ask one focused question,
such as: “What recent change was harder than it should have been?” Then wait.
For a broad audit, offer to start with one representative difficult change; if
none is known, inspect one important workflow and report limits, not a global verdict.

Team size, folders, and dependencies are context, not proof of operational needs.
Do not infer traffic, incident history, domain complexity, or team autonomy from them.

For greenfield work, start from the first workflow to deliver and confirmed
deployment, data, and operational constraints. Recommend a minimal starting point;
do not invent code evidence or predict future scale as if it were measured.

## 2. Inspect a representative workflow

Read relevant project instructions and existing decisions before recommending changes.
Start with the manifest, deployment entry point, and the files involved in the
selected workflow. Follow its caller, business rule, persistence or external
boundary, and relevant tests as needed; do not scan the entire repository by default.

Use a first-pass budget of 12 relevant files, excluding instruction files. Search
narrowly before reading. If this is insufficient, state the missing evidence and
either extend the sample for a named reason or narrow the conclusion. A sample
does not justify claims about the whole system.

For each finding, connect:

**Observed problem → evidence → effect on a real task → smallest intervention → check.**

Cite actual file paths and symbols or line ranges. Distinguish observed facts,
user-reported symptoms, and hypotheses. A folder name, logic in a handler, or a
deviation from Clean/DDD is not by itself a defect. Report cycles or coupling only
when you can show the dependency and explain its consequence. Never invent timings,
incident counts, benchmarks, or savings. If measurement is missing, propose it.

Read `references/decision-guide.md` when comparing mechanisms or planning a transition.
It supplies prompts, not mandatory architecture rules.

## 3. Compare feasible options

Compare at most three options, including keeping the current approach. For greenfield,
use the simplest viable starting point as the baseline. Do not fill unused option slots.

**Hard constraints are feasibility gates, not scoring signals.** Reject an option
that violates a confirmed requirement, or mark it infeasible with the reason.
For example, one mandatory release unit cannot satisfy independently releasable
components. A small team does not cancel that requirement. If requirements conflict,
explain the conflict and ask which may change; do not silently relax either.

For each option describe:

- How it addresses the observed problem and satisfies the hard constraints.
- Implementation and ongoing operational cost, qualitatively unless measured.
- Risks, reversibility, and important unknowns.
- Why it is preferable or inferior to the baseline for this decision.

Do not use fit scores, stars, team-size cutoffs, or pattern popularity as evidence.
Patterns may explain a mechanism, but do not choose a complete architecture bundle.
Justify independently deployable services, event delivery, read projections, and
event sourcing separately; adopting one does not imply adopting the others.

## 4. Recommend the smallest useful step

Give a clear recommendation when evidence supports one. “Keep the current design”
and “measure before deciding” are valid outcomes. If evidence is insufficient,
name the uncertainty and the specific check that would resolve it; do not force a winner.

Default response, scaled to the size of the question:

### Decision
One sentence stating the decision and intended outcome.

### Evidence and constraints
Relevant code references or user-reported facts, hard constraints, and material unknowns.

### Options
A compact comparison, including the baseline and why options are rejected.

### Recommendation and next step
The smallest bounded action, its cost and risks, and what stays unchanged.
For a migration, separate the current state, proposed target, and rules effective now.

### Validation and revisit trigger
A concrete check tied to the intended outcome, a rollback or stop condition where
applicable, and an observable condition that would justify reconsidering the decision.
Prefer an existing test or representative change over a speculative benchmark.

Avoid a full folder tree, global migration plan, or diagram unless it clarifies
this particular decision. Do not implement the recommendation merely because the
user asked for advice. Implementation requires a request covering those changes.

## 5. Persist only on explicit request

Advice and audits are read-only by default. Agreeing with a recommendation is not
authorization to edit files. Do not create ADRs, edit agent instructions, scaffold
folders, install tooling, or change CI unless the user explicitly requests that action.
An initial request to record a decision counts; do not ask for permission twice.

When persistence is requested:

- Follow existing decision locations, numbering, and templates. If none exist,
  use `docs/decisions/` for a requested ADR. Ask only if the requested scope is ambiguous.
- Record context, evidence, alternatives, decision status, consequences, validation,
  and review triggers. Mark unresolved decisions Proposed, not Accepted.
- Distinguish current state, accepted target, and active rules. Accepting a target
  does not mean its implementation is complete. Include transition steps when needed.
- Modify only the requested files. Do not replicate a decision across all agent configs.
  Prefer a link to the decision over duplicated policy. Preserve unrelated content;
  show conflicting existing policy before replacing or superseding it.
- Add only rules justified by this decision, expressed in the project's real terms.
  Scope them to new work or a named boundary when legacy violations remain, with
  explicit exceptions or a baseline. Do not label existing debt a new regression.
- If enforcement is requested, inspect the installed tool/version and existing CI.
  Use current documentation, adapt to actual paths, and verify the baseline passes
  while a representative new violation fails. If not verified, say so and do not
  claim the rule is enforced. Do not enable a failing gate as a completed migration.

Finish by reporting what changed and what was actually checked. If no files were
requested, finish with the decision and next action, not a persistence prompt.
