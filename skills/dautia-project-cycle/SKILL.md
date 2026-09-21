---
name: dautia-project-cycle
description: Coordinate a substantive DautIA objective across discovery, audit, implementation, multi-repository delivery or authorized operations; preserve scope and evidence before edits and closure. Ordinary follow-ups reuse the active context.
metadata:
  version: "15.0.0-rc1"
---
# DautIA project cycle · r3

The principal owns the result, not just dispatch. Skills are methods; the active
routing policy chooses profiles without changing authority or acceptance.

## Enter and prepare

Identify DISCOVERY/AUDIT/IMPLEMENTATION/RELEASE and the actual outcome. Read nearest
instructions and relevant canonical sources. Reconcile intent, accepted decisions,
state observed now and test expectations before the first dependent change.
Preserve material examples, reasons, exclusions and previous decisions. A new
requirement is not a historical omission; a contradiction now must be resolved now.
Discovery/audit may produce authorized notes, not silently change canonical scope.

Use `references/r3-prevention.md` for material change/diagnosis. Investigate impact
through producer -> contract/state -> consumer -> treatment -> check. Do not infer
no-impact from no edited file. Defer only the block depending on an unresolved
product decision. Seek accessible information before increasing model effort.

Load the applicable diagnosis, platform, UI, provider or delivery skill before
acting on that frontier. `scripts/skill_catalog.py` extracts real metadata without
deleting collisions or claiming a skill was used. Do not load equivalent browser
skills or all platform skills by default. Existing project runbooks prevail over
generic recipes unless the exact change is approved.

## Bind the material boundary

Create one compact private packet per active objective/block using the examples
in `examples/r3-analysis.json`. It contains enough actual context, not a checklist
of invented confirmations. No packet is required for a trivial direct read.
Use `scripts/workflow_cli.py gate preflight PACKET --cwd WORKSPACE` before the
material writer starts; `dispatch` before delegation and `closeout` before closure.
Exit 3 is an unresolved condition; exit 2 is invalid input/storage. Resolve it or
report its precise boundary rather than bypassing it to make the check green.
The checks compare supplied facts and refresh declared source files; they cannot
prove semantic understanding, authentic human consent or provider truth.

For projects with complete, partial or scratch documentation, use
`references/evidence-contract.md` and `scripts/evidence_contract.py`. Evidence is
bound to the current objective and project. An active workstream may scope the
documentation status so a complete functional slice can close while a separate
demo remains pending. Incomplete context may continue through discovery, but it
blocks product closeout/release for that active scope.

`bind PACKET --session SESSION --generation GENERATION --cwd WORKSPACE` preserves
the packet for opt-in root hooks. Rebind at meaningful state changes; preserve
pause and restart a generation only for a genuinely resumed/new run. Do not use
binding as a way to invent approval or reset stop limits. A child's parent session
ID never grants the child the root's authority.

## Select and execute

Use `references/model-routing.md` and the versioned candidate policy. Ordinary
execution remains on the configured default; complex open questions become bounded
analysis with appropriate evidence, not a writer change or infinite retries.
Routing is local and deterministic; do not introduce a provider advisor into every
command. A negative observation, failed test or missing permission is relevant and
must remain visible in the packet and closeout evidence.

For material delegation, prepare the actual worker packet and call
`workflow_cli.py dispatch-plan PACKET --agents-dir CODEX_HOME/agents --cwd WORKSPACE`.
Supply the host's observed available profiles/targets. For product/test writers,
record whether the decisions are resolved and whether execution is routine,
demanding or unknown; unresolved decisions return to analysis before writing.
Use the returned exact `agent_type` in the native spawn and pass the same context.
Do not substitute the canonical role or silently inherit the parent's effort.
A material delegation must persist `runtime.required_agent_type` and its terminal
`runtime.dispatch_receipt`: exact role-qualified target, `fork_turns: "none"`,
observed model/effort, child reference, `status: "completed"` and evidence.
Generic `worker`/`code_explorer`, missing or mismatched profile, `fork_turns:
"all"`, or capacity/incomplete child is a dispatch contract violation and blocks
closeout; the principal cannot replace that receipt with its own artifact.
For an explicitly broad visual scope (`work.visual_scope: broad|redesign`), retain
the design baseline, real-viewport screenshots, responsive and accessibility
checks, explicit visible-content checks (for example, an analysis explanation and
its color mapping), and an independent `ux_auditor__PROFILE` handoff. Functional tests do not
prove visual hierarchy, continuity with the existing design, or user impact.
A prepared JSON request is not a spawned child: record its actual start/report and
receive its delivery. The CLI does not intercept the native tool. A principal choice
among ordinary eligible profiles requires explicit evidence and remains separate from
the configured default.

Delegate only a useful bounded block. Retain one writer per workspace and one
operator per simulator/browser/side-effectful resource. `workflow_cli.py lease`
provides a cooperative same-host lease; it is not a distributed or security lock.
Workers never create grandchildren. Ask independent reviewers for their first
judgment before comparing conclusions. Resolve disputes by evidence, not votes.

Unknown cause -> hypothesis and discriminating observation before a patch. New
regression/refuted premise -> reframe the affected block, retain evidence and
continue independent work. Do not simply add delay/hit-target/configuration layers.

## Verify, integrate and continue

Check intended behavior and preserved invariants. A test that also passes on the
broken variant does not prove repair; independently justify any exception.
Failed attempts remain evidence even after a later pass. Tie checks to the exact
candidate, config, artifact and environment. No live PASS from offline fixtures.
Product changes require independent review against original acceptance. An author
fixes findings; a reviewer does not edit their object or merge it themselves.

Use `dautia-ci-cd` for versioned integration or release and `r3-git-workspaces.md`
for local ownership/closure. No generic dev branch or cleanup. Provider effects
are separately authorized and verified. If a prior external effect is unknown,
reconcile before retry. A build/health/upload does not imply tester availability
or a business-channel response.

Before handback, list the relevant remaining actions. Execute authorized available
work or internal team preparation. Return only real user decisions, physical actions
or proven external blockers. Respect stop/pause/budgets; no fabricated heartbeat.

## Evidence and installation boundaries

Use `references/observability.md` and `references/r3-harness.md`. Minimal events
supplement the existing collector, not raw logs or an additional agent. Preserve
negative evidence and mandatory context independently of optional reranking.
Installed sources, configured profiles, observed calls and accepted outcomes are
different claims. Host/model/SDK validation is not established by static tests.
