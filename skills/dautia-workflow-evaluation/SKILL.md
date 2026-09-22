---
name: dautia-workflow-evaluation
description: Evaluate DautIA workflow behavior and model profiles with sanitized contract replays and attributed results in Codex; use for an explicit workflow/model evaluation, not ordinary implementation.
---

# DautIA Workflow Evaluation

Focused instruction-audit update: 2026-09-12. For an audit of AGENTS.md, skills,
model routing or instruction streamlining, use
[instruction audit](references/instruction-audit.md). Recommendations come before
changes; audit mode does not authorize edits. Skip runtime pilots for an ordinary
configuration review unless execution is requested.

Measure whether a candidate preserves acceptance and authority at lower total
cost. Use the actual Codex harness, not a Claude runner labelled Codex. Shared
skills remain the domain contract; vary model/effort only in a controlled comparison.

For a small behavioral pilot, run `scripts/run_replay.py --help`. Its eight
sanitized cases check authority, evidence, UI lineage, provider preservation and
routing. It uses the installed Codex CLI and account, limits run duration, applies
read-only sandbox and disables MCP/plugins in each child invocation. No providers,
real transactions, new user tasks or production fixtures. Keep cases/contract
identical across profiles. It records CLI runtime model headers, outcomes and
reported usage; requested profile alone is not proof of actual routing.

Run `--dry-run` first to inspect scope without model calls. `--run` explicitly
executes the pilot; account usage applies. For the GPT-6 migration, start with Sol medium/high, Luna high and Astra low;
compare Astra medium only for a concrete unresolved analytical question. Historical
v11/v12 cases retain their original profile expectations and are not the active
GPT-6 routing oracle. Use the versioned GPT-6 pilot for adoption evidence.
The ceiling is Astra medium; max/ultra and higher Astra efforts are excluded.
Sol xhigh remains an explicitly authorized exception, not an automatic pilot target.
A replay is instruction-following evidence, not an implementation benchmark or
proof of automatic skill discovery. Check fresh-session discovery separately.

For the versioned GPT-6 decision replay use `scripts/run_gpt6_pilot.py --repo
<workflow-checkout> --output <private-output> --codex <compatible-client>` first
without `--run`, then repeat with `--run`. It freezes contract, cases, runner and
grader dependency. It uses an isolated CODEX_HOME with a temporary link to the
existing Codex auth file, removed on normal/handled exit; account calls are real,
product/provider operations are not performed. An interrupted host may require
removing that pilot-owned link. A requested model or failed turn is not a pass:
require runtime context, completed response, acceptance and no tool calls.
Keep v1/v2 failures and rubric amendments; do not compare changed fixtures as a
controlled performance experiment. Select `--profiles` to test only a relevant
uncertainty. The ordinary CLI may lag the app's model support; verify the exact
client instead of silently changing model. This runner does not prove native
subagent dispatch; validate generated definitions with a separate child pilot.

For full task evaluation freeze baseline, fixtures, tools and acceptance; compare
actual resulting artifacts and escaped defects, corrections, user time and total
usage including all agents/handoffs. Use replay/fakes for real-provider operations.
Report unknown fields as unknown. Never sum reasoning again on top of output,
or convert Codex usage into API dollars/subscription credits without billing
attribution. Read `references/pilot-cases.json` only for fixture maintenance.

For the bounded nested-role simulations, run
`scripts/run_workflow_simulations.py --dry-run --output <owner-only-scratch>` first.
`--run` creates fresh sanitized fixtures, uses each absolute fixture directory as
the corresponding model process working directory, invokes one real Codex CLI root per case,
and grades artifacts plus each child's own archived `turn_context` and terminal
event. It disables providers, plugins and network but leaves multi-agent enabled.
For dependent cases, the downstream child emits the frozen contract receipt in
its own output before editing; this confirms observable acceptance without
claiming that encrypted spawn content was decrypted or compared byte for byte.
The positive cases force named roles to prove runtime resolution; they do not prove
autonomous role selection or relative model quality. The copy control requires no
child. Read `references/workflow-simulation-cases.json` only when maintaining these
fixtures or their frozen acceptance.

For the broader natural-routing suite, use the same runner with `--suite v12`.
Its `--dry-run` writes `control/frozen-plan-v12.json`, including fixture, routing,
artifact and verified effective-contract fingerprints; `--run` refuses drift.
The model workspace is a sibling of this control directory, so ordinary fixture
inspection does not enumerate expected values. This is not OS read isolation;
observable tool access to the frozen plan or installed v12 case catalog invalidates
the affected result. The terminal `SIM_RESULT` block is parsed as one unique value
per expected key, with exact or bounded semantic rules frozen per key; narrative
mentions, contradictory duplicates and unsafe nonempty values do not pass.
Use `--workers 1` for the v12 fixture-cwd runner. Each case uses its own scoped
trust key, and parallel execution of this mode has not been validated. It keeps raw sessions owner-only, publishes
a sanitized result without thread IDs or messages, and removes only scratch trust
entries created during the run, including on exceptions. The case catalog preserves
the 26-case baseline and adds nine versioned corrective or expanded cases for
acceptance/test conflict, coordinated handoff, server, mobile and CI boundaries.
Each maps to atlas references and a qualitative regression; counts describe
coverage, not measured frequency.
Natural prompts do not name roles; required and permitted outcomes remain frozen
grader data. Read `references/workflow-v12-cases.json` only when maintaining that
suite. A hash-bound terminal review receipt establishes that a separate reviewer
emitted a favorable verdict for those final bytes; it does not establish review
depth or a native GitHub approval.

Keep original personal skill-creator evaluation resources disabled but recoverable;
use the system skill-creator for authoring. Do not call its legacy Claude scripts
as evidence for Astra/Sol. Do not schedule recurring collection without a cadence
request; telemetry collection remains diagnostic and explicit.
