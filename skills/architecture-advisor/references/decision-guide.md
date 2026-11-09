# Decision guide

Use only the section relevant to the current decision. These are diagnostic prompts,
not a catalogue to score or rules to copy into a project.

## Find the cost before choosing a boundary

Trace a representative change: which files, tests, owners, releases, or data contracts
must change together? Ask for a recent example if that cost is not visible in code.
Separate accidental coupling from coordination required by a genuine business invariant.

| Observed difficulty | Small experiment to consider | What to check |
|---|---|---|
| One business rule is duplicated across entry points | Extract that rule behind an existing local abstraction | Both entry points exercise the same rule; unrelated code stays untouched |
| Tests of a rule require an unrelated external service | Isolate the specific external interaction | The rule can be tested without that service; integration coverage remains |
| Another module's internals repeatedly change callers | Introduce one stable entry surface at that seam | A representative internal change no longer changes those callers |
| Releases block each other despite a required independent cadence | Trace build, runtime, and data coupling before splitting a release unit | One component can change and deploy without rebuilding or releasing the other |
| A slow read is reported | Inspect its query and measure a representative workload first | A query/index change meets the measured need before adding another data model |

These are hypotheses to test. Do not claim improvement solely because files moved
or an interface was added. An extra abstraction can cost more than the coupling.

## Separate mechanisms

- **Code boundaries versus deployment boundaries:** module encapsulation can improve
  local changes without introducing network calls. It does not itself provide independent releases.
- **Independent releases versus microservice reorganization:** inspect the actual release
  requirement and candidate seam. Splitting the whole application is not the default next step.
- **Command/query separation versus read projections:** separate functions can use the
  same transactional database. A denormalized model needs its own justification.
- **Read projections versus asynchronous propagation:** justify lag tolerance, rebuilds,
  and failure recovery before introducing asynchronous synchronization.
- **Audit history versus event sourcing:** first establish what must be recorded,
  retained, and reconstructed. An audit trail does not by itself require rebuilding
  all state from events. Do not promise legal compliance from a pattern choice.
- **Event delivery versus decoupling:** account for contracts, retries, duplicate
  delivery, ordering, and operations only if that mechanism is actually proposed.

## Make transitions safe

For each migration step specify the affected boundary, preserved behavior, check,
and rollback or stopping condition. Separate:

1. **Current state:** what the code and deployment do today, with evidence.
2. **Proposed or accepted target:** the change being considered or agreed.
3. **Active rules:** what contributors must follow now, including legacy exceptions.

Prefer a rule for a new boundary or “no new violations” over applying an idealized
architecture globally. A baseline must identify existing exceptions rather than
disable the check. Verify that new violations are still detected. Do not fabricate
a linter configuration or claim it runs based on an illustrative snippet.

## Example of a bounded recommendation

User-reported problem: HTTP and scheduled invoice creation disagree on rounding.
After verifying both paths, cite their actual files and the duplicated calculation.
Compare keeping the duplication with extracting just the rounding rule; consider
a larger service split only if another confirmed requirement makes it relevant.

Recommend a shared calculation with tests for the reported discrepancy, leaving
deployment and persistence unchanged. Validate both entry points against those
cases. Revisit the boundary if their business rules intentionally diverge.

This example supplies a reasoning shape, not evidence to reuse in another repository.
