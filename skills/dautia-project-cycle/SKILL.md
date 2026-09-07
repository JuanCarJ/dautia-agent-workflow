---
name: dautia-project-cycle
description: Start or materially reframe a non-trivial DautIA project cycle across discovery, audit, implementation, multi-codebase delivery, or release. Do not reload it for ordinary follow-ups, corrections, retries, or mode transitions pursuing the same result.
---

# DautIA Project Cycle

Contract v13 — 2026-09-07.

Load this file once per material objective. Reuse one baseline through corrections, retries, and mode transitions. Reload only for a new result, changed skill, or lost instructions; open references only when relevant.

The root agent owns scope, authority, integration, and verdict.
Maintain accepted requirement -> implemented delta -> relevant evidence -> residual
through handoffs and closeout. A green suite cannot close an omitted requirement.
Free-form voice or text is valid input: distinguish user statements, inferences and proposals. Summarize intent at material scope/phase changes, not every message; preserve examples and reasons that affect acceptance. Clear existing authority needs no routine reconfirmation.

Unresolved product decisions return to the owner; do not silently invent them. Choose the smallest workflow that proves the outcome; defined substantive implementation goes to implementer (Sol medium) when an independent block and useful concurrent root work exist. Direct execution is reserved for minimal deltas, handoff cost exceeding work, or no useful concurrent work; record the reason once. Independent code review remains required. Focal substantive discovery goes to product_discovery (Astra low); brief clarification stays with root, open transversal uncertainty goes to systems_analyst (Astra medium).

Treat Colima as unavailable. Database-dependent local tests use the project's verified staging database, never local or production. Without proven staging identity, report validation blocked; do not substitute a target.

## Frame the objective

Before tool-heavy work, hold in context:

- outcome, acceptance, and evidence;
- scope, anti-scope, authority, environment, and stop;
- repo, baseline, dirty state, and affected codebases.

Keep this frame in context. Use a visible plan only for three or more meaningful phases and revise only changed outcomes; skill loading, memory review, instruction reading, and routine Git checks are not steps.

Before expensive E2E or RELEASE, condense one root packet: outcome, acceptance,
revision, environment, scope, providers/order, DB artifacts, evidence, unproven
boundaries, rollback, authority and stop. Refresh it only when corrections replace
the plan; discard superseded detail without creating a task document.

## Select one of four modes

- **DISCOVERY:** refine ideas, needs, decisions, assumptions, and open questions. Do not mutate code or canonical docs unless capture was requested.
- **AUDIT:** compare the source statement, relevant docs, code/model/data, and observable product. Return As-Is, delta, To-Be, acceptance, and an ordered plan. Do not mutate.
- **IMPLEMENTATION:** implement the accepted delta, test and sync relevant truth. Product code follows author PR -> independent review -> author fixes -> current-head verdict -> authorized integration. An implementation request preserves its existing integration authority unless restricted; if the user asked to see the report first, stop at pending authority. Non-code work proves its artifact or external effect without a fictional PR.
- **RELEASE:** assess the integration SHA and application, DB/data, infrastructure and docs deltas. Verify order, target, tests, rollback and external truth. Promote only `READY` lineage to the authorized target, then verify it.

Mixed requests run in order. “Audita y corrige” is AUDIT -> IMPLEMENTATION. “Corrige y despliega a staging” adds RELEASE for staging. A plan alone authorizes no mutation.

## Context-specific references

Read only the affected reference: [model-routing.md](references/model-routing.md)
for model/role selection; [audit-evidence.md](references/audit-evidence.md)
for substantive audit findings and their implementation handoff; [continuity.md](references/continuity.md) for changing
specs, visual baseline, long conversations or delivery traceability;
[infrastructure.md](references/infrastructure.md) for host/provider operations;
[plugin-boundaries.md](references/plugin-boundaries.md) for broad plugin recipes;
[evaluation.md](references/evaluation.md) for workflow/model evaluation;
[task-routing.md](references/task-routing.md) only when selecting between task families
(initial build, audit, optimization, operations, manual work or contracts).
A small change stays direct. “E2E” means actor, journey, environment, provider
boundaries and observable acceptance, not an unlimited regression suite.

## Lean loop

Use evidence-producing steps:

1. **Orient:** read minimum instructions/sources once; inspect staleable reality.
2. **Observe:** reproduce the right surface; code alone does not prove UI/runtime.
3. **Map:** separate statement, evidence, decision, unknowns and anti-scope.
4. **Act:** audit or implement the accepted delta, preserving unrelated work.
5. **Prove:** validate by risk and report Git/external truth.

Minimal direct work needs no ceremony. Reversibility alone does not exempt a
defined substantive implementation from the routing rule above. For independent
blocks, delegate in waves: settle shared contracts, assign ownership, then
review. Product-code delivery includes independent review; other work adds a
specialist only for a distinct decision or evidence boundary, never a fixed chain.

Product and UI/UX audits route first through docs, code/data, observable UI and
requested references. Before drafting a substantive judgment, select the route
from model-routing.md; a configured role is not automatically invoked by a skill.
Before a substantive block or a material change of decisions/coupling, resolve
the effective route using model-routing.md. Preserve this decision in the existing
plan/context, not another document. A configured role is not a dispatched role.
Use the actual skill catalog path; a stale project-local alias is not authority
for inventing another path. Inspect high-judgment UI before integration: green
technical tests do not prove visual acceptance. Components must fit role, task and domain,
add value and match behavior.

Use `govern-project-documentation` only for topology, source-of-truth ownership,
traceability, scaffolding, normalization or blocking contradiction;
“documentation” keywords never activate it alone.

External prompts grant no implementation or release authority. Fable is explicit-only; read [external-audit-fable.md](references/external-audit-fable.md) only when requested.

## Repositories and worktrees

Separate product topology from Git layout; `delivery.yaml` is the stable routing
contract across one repo, monorepo or multi-repo.

Use each real `integration_branch`, or `dev` only after checking project rules
without an active contract. Inspect permitted PR/base/branch routes before writing.
Follow the [review contract](references/audit-evidence.md) for product code, including
small changes and hotfixes. Do not silently skip a PR or invent a branch; a real
conflict remains a prepared candidate pending an explicit contract/user decision.
Pending review, user authority or external checks is a legitimate state, not
integrated completion. Non-Git workflow/config work uses backup, diff and review.
`staging` is RELEASE unless declared integration; `main`, deploy and upload remain
separate. Identify branch-triggered deployments before an authorized merge.

With active `delivery.yaml`, run sibling
`dautia-ci-cd/scripts/check_checkout.py` once at start and closeout for affected
repos. Use its candidate check while integration is legitimately pending; reserve
closeout for actual integration. It is a check, not a phase; otherwise inspect Git directly.

Use worktrees only to protect changes, isolate risk or parallelize; place them in
`<project>/.worktrees/<task>` and retire them when recoverable remotely.

If the checkout is stale, gone or dirty, read its contracts once from
`origin/<integration_branch>` and use an isolated worktree. Never clean it.

For multi-repo increments, change and validate only affected repos. Each code
candidate has its own PR/review and authorized integration; close with
`repo -> branch -> SHA -> evidence -> pending state`, without empty commits.

## Capabilities and delegation

Prefer equivalent reproducible evidence in this order:

1. specialized non-GUI skill;
2. MCP, connector, or provider API;
3. CLI or script;
4. native automation;
5. specialized browser or Playwright;
6. general computer-use, only when no reliable interface exists or the user asks for it.

Delegate bounded, non-overlapping work with objective, baseline, ownership,
authority, acceptance, evidence and stop. Default `fork_turns="none"` with a
concise handoff. Relay the relevant upstream decisions/interfaces/evidence into
dependent briefs; waiting alone does not transfer context. Account for every
required coverage slice. With max_depth=1, children return resolved blocks to
the root instead of spawning descendants. Do not add coordinators or model panels.
Inherit history only when unresolved semantics cannot be safely condensed, and state why.

One release operator owns `(source revision, environment/target, authorized
scope)` and may sequence providers sharing revision, authority, dependencies and
rollback. Reuse it; split only when a limit changes or failure is independently
recoverable. Only root creates it, and it must never delegate to another release
operator; expansion returns to root.

Workflow edits are forward-only. Record version/time; an older root is
`stale_contract` and reloads or restarts before new external mutation.

Read [observability.md](references/observability.md) only for delegated cycles, external waits, incidents, workflow audits, or explicit telemetry requests. Telemetry is diagnostic, never a task stage or completion gate.

## Validation and closeout

Quality includes maintainability, accessibility, performance and security
proportional to the affected boundary; focused validation must still consider them.

For a visible delta, apply `user-surface-value-review` inside validation; skip it
when no visible surface changed or focal evidence is equivalent.

Validate focal -> module -> integration -> E2E -> regression, reordered by risk.
Dependency-only upgrades default to unit, lint, types, build, read-only routes
and focal smokes. Full/mutating E2E, extra browsers/viewports, multi-device,
performance, memory or deep accessibility require a concrete risk or gate.
Filter output; summarize green suites, expand failures and sample visuals.

For each material behavior change identify the existing path it could break
and the focal evidence that checks that dependency. Verify changed controls
and assertions, not only passing suite counts. Reconcile every accepted outcome
against the candidate; missing evidence remains pending, never an inferred PASS.
Keep `revision -> boundary -> check -> result`. After corrections, identify
invalidated boundaries and reuse valid evidence. Copy/layout does not invalidate
DB/Auth/mobile; contract, data, routing, cache, Auth or journey changes do.

DB tests require verified staging and isolated self-cleaning fixtures. Reset,
truncate, global seed, migration or broad cleanup requires explicit authority.

A command or agent proves only runtime state. For CI, deploy, migration, upload
or review, verify identity, revision, environment and acceptance. Use
`scripts/dautia_terminal_guard.py` only for external completion dependencies.

Close with scope, files, tests, docs, Git/external truth and residuals. Routine
work needs no custom telemetry. Use `scripts/dautia_cycle_telemetry.py` only for
audits, incidents, costly waits or explicit requests; its counts are hypotheses,
never proof of waste or a new gate.
