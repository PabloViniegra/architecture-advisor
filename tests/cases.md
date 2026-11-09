# Behavioral evaluation

`scenarios.json` contains synthetic cases with initial files, user turns, evidence
anchors, and observable pass/fail criteria. They are not measured user outcomes.
The offline unit tests validate their integrity, not the quality of agent responses.

## Run a case with an agent

1. Use a fresh disposable repository outside this checkout. Materialize the case's
   `files` mapping as relative paths and commit that initial state, including in
   greenfield cases (an empty commit is sufficient). Do not copy these fixtures into
   a user's working repository or run setup commands on an existing project.
2. Load the current skill through the agent's normal skill mechanism. Keep the
   model, system instructions, available tools, and permissions fixed across runs.
   Do not expose the case's `pass`, `fail`, or `evidence` fields to the agent.
3. Send each `turns` entry in order, waiting for the agent to finish each turn.
   If it asks an unanticipated question, record the run as blocked rather than
   inventing facts. Add any standardized reply to the fixture before comparing reruns.
4. Save the transcript, repository diff including untracked files after each turn,
   tool/check output, model identifier, skill revision, and any blockers outside the
   fixture repository. Check content and changes, not just what the agent claims.
5. Review every `pass` and `fail` criterion against that evidence. A case passes only
   when all required behaviors hold and no failure condition occurs. Missing evidence
   is not a pass. Do not demand exact wording or a particular pattern name.

For evidence cases, verify actual references and the reasoning connecting them to
the recommendation. The fixture anchors help locate relevant code; quoting every
anchor is not itself success. For consent cases, inspect the diff after each turn;
a final clean diff does not establish that the agent avoided earlier writes.

## Compare usefulness, not just compliance

Run the same cases with the redesigned skill and a no-skill baseline, using a new
session and clean repository for each. Remove the explicit skill invocation from
baseline prompts, keeping the task and context identical. Optionally include version
1 from a separate checkout; never mix its files or instructions into a version 2 run.

Randomize and anonymize the outputs for the evaluator. Keep the factual assessment
separate from these usefulness questions:

- Can the user identify the decision and execute the next step?
- Is the proposed change smaller than an equally effective alternative?
- Does the explanation connect evidence, constraints, costs, and validation?
- How many clarifications and unnecessary artifacts did it require?

Record criterion-level results, clarification counts, changed files, and evaluator
reasons, not a single architecture-fit score. Repeat across runs to expose variance.
Then test at least five representative real decisions with users before claiming
improved utility; synthetic compliance alone is insufficient.

## Scope of automated checks

`python -B -m unittest discover -s tests -v` checks metadata, workflow structure,
selected explicit contract clauses, local links, case coverage, fixture paths,
Python syntax, and evidence anchors. Text assertions are regression reminders,
not proof that an agent follows the policy. The old arithmetic tests were removed
because version 2 has no scoring engine; behavioral evaluation replaces their
product-level purpose, not their arithmetic implementation.

No agent runs or usefulness comparisons are performed by that command or CI.

## Independent adversarial cases

`adversarial_scenarios.json` adds seven cases independently of the original eight:

| Case | Consequential boundary |
|---|---|
| `contradictory-release-contract` | Incompatible mandatory requirements must be resolved, not scored away |
| `folders-are-not-runtime-evidence` | Folder names, team size and allegations do not prove runtime boundaries or coupling |
| `consent-narrows-after-agreement` | Read-only advice, agreement, then explicit permission for exactly one ADR |
| `record-unresolved-decision-in-place` | Initial permission is enough; uncertainty remains Proposed; owner notes survive |
| `existing-gate-fails-legacy-baseline` | A checker rejecting permitted debt is not a ready gate; new violations must still fail |
| `transition-is-not-completion` | Accepted target is not current implementation; legacy exception and rollback remain necessary |
| `independent-release-does-not-imply-events` | Independent releases do not require messaging, projections or event sourcing |

These cases include explicit failure criteria, not expected answer strings. The
mandatory-constraint pair deliberately includes both a satisfiable release case
and a contradictory one: always recommending a split or always keeping the baseline
cannot pass both. Similarly, the consent sequence requires both restraint before
authorization and action after a bounded request. Existing text-contract tests
remain reminders only; they were not replaced with a simulated architecture engine.

## Executable recording and filesystem checks

`eval_recorder.py` prepares a new directory **outside this checkout** and captures
external evidence after each turn. It never invokes an agent, model, shell command,
package installer, or API. `write_scopes.json` defines the exact allowed file paths
for each turn of all 15 cases; no wildcard grants are used.

Example preparation (choose a fresh directory for every run):

```sh
python -B tests/eval_recorder.py prepare consent-narrows-after-agreement \
  /tmp/opencode/advisor-consent-run \
  --model ACTUAL_MODEL_ID --configuration 'actual harness, permissions and tools'
```

The printed `workspace` contains only initial fixture files, not evaluation criteria.
The sibling `run.json` records the fixtures, skill/reference text, declared model
and configuration, and initial filesystem state. It is evidence storage, not a
sandbox or trusted execution attestation. Use an external agent in that workspace,
load the recorded skill through its normal mechanism, and send only the current
user turn. Keep criteria and artifacts out of the agent's supplied context.
Do not run these fixtures in this checkout. No Git repository is required by this
recorder; do not initialize one after preparation, since that changes the captured
baseline. If an agent requires Git, use the manual committed-baseline protocol
above instead and record that difference in the evaluation environment.

After **each** real response, save the complete transcript and tool trace outside
the workspace, then capture before sending the next user turn:

```sh
python -B tests/eval_recorder.py capture /tmp/opencode/advisor-consent-run \
  --transcript /tmp/opencode/turn-1.txt --tool-log /tmp/opencode/tools-1.txt
python -B tests/eval_recorder.py check /tmp/opencode/advisor-consent-run
```

Repeat capture with separate evidence files for subsequent turns. State explicitly
in the tool log when no tools ran. Capture refuses missing evidence or extra turns;
check exits nonzero for incomplete recordings or observed out-of-scope changes.
All paths, including untracked files, empty directories, symlinks, binary content,
permissions and deletions, are compared. Symlinks are recorded without traversing
their targets. Newly necessary parent directories are allowed only for authorized
files; an existing parent or sibling is not implicitly writable.

An unchanged repository can still contain a useless or incorrect recommendation.
Even exit code zero means **only complete recording and allowed end-of-turn state**.
The JSON always reports `behavioral_verdict: NOT_EVALUATED` and provenance
`externally-supplied-unverified`. A fabricated transcript or test double cannot
turn that into a real-agent pass. Review every semantic criterion against transcript,
tool trace, actual source references and recorded content; record pass/fail/blocked
with evidence for each criterion separately. In authorized-write cases, also check
that the requested update actually occurred and preserved unrelated content.

Snapshots catch a violation on turn one even if restored on turn two. They **cannot**
detect a write restored within the same turn, writes outside the workspace, tool
side effects or forged evidence. Audit a trusted tool trace for those properties;
do not infer read-only execution from a clean final snapshot. Agent runs that ask
unexpected questions remain blocked, not passed by supplying invented answers.

## What the automated tests establish

`test_eval_recorder.py` executes acceptance and negative controls for this limited
filesystem evaluator: allowed ADR update, agreement without permission, forbidden
sibling edits and deletion, restored intermediate violation, binary/mode/symlink
changes, empty directories, missing evidence, and incomplete or extra turns. It also
executes the synthetic boundary checker in three deterministic states: legacy
baseline fails, no violation passes, new reach-in fails. That validates the fixture,
not enforcement in an actual user project and not an agent's interpretation of it.

No real-agent responses, semantic judgments, no-skill comparisons or measured user
outcomes are produced by the unit suite. Those remain pending until an authorized
external agent runner is available; no paid model calls or credentials are needed
or used by the included tooling.
