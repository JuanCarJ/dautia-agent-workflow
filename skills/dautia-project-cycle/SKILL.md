---
name: dautia-project-cycle
description: Start or materially reframe a non-trivial DautIA project cycle across discovery, audit, implementation, multi-codebase delivery, or release. Do not reload it for ordinary follow-ups, corrections, retries, or mode transitions pursuing the same result.
---

# DautIA Project Cycle

Load this file once per material objective. Reuse one baseline through corrections, retries, and mode transitions. Reload only for a new result, changed skill, or lost instructions; open references only when relevant.

The root agent owns scope, authority, integration, and verdict. Choose the smallest workflow that proves the outcome; zero delegation is healthy.

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
- **IMPLEMENTATION:** implement an accepted idea or audit, test, sync relevant canonical truth, then integrate and push to `integration_branch` from active `delivery.yaml`, or `dev` without one. “Corrige”, “implementa” or “hazlo” authorizes that integration closeout unless restricted.
- **RELEASE:** assess the integration SHA and application, DB/data, infrastructure and docs deltas. Verify order, target, tests, rollback and external truth. Promote only `READY` lineage to the authorized target, then verify it.

Mixed requests run in order. “Audita y corrige” is AUDIT -> IMPLEMENTATION. “Corrige y despliega a staging” adds RELEASE for staging. A plan alone authorizes no mutation.

## Lean loop

Use evidence-producing steps:

1. **Orient:** read minimum instructions/sources once; inspect staleable reality.
2. **Observe:** reproduce the right surface; code alone does not prove UI/runtime.
3. **Map:** separate statement, evidence, decision, unknowns and anti-scope.
4. **Act:** audit or implement the accepted delta, preserving unrelated work.
5. **Prove:** validate by risk and report Git/external truth.

Direct reversible work needs no ceremony; root-only is valid. For independent
blocks, delegate in waves: settle shared contracts, assign ownership, then
review. Add rollback or independent review only for named risk.

Product and UI/UX audits route first through docs, code/data, observable UI and
requested references. Inspect high-judgment UI before integration: green
technical tests do not prove visual acceptance. Components must fit role, task and domain,
add value and match behavior.

Use `govern-project-documentation` only for topology, source-of-truth ownership,
traceability, scaffolding, normalization or blocking contradiction;
“documentation” keywords never activate it alone.

External prompts grant no implementation or release authority. Fable is explicit-only; read [external-audit-fable.md](references/external-audit-fable.md) only when requested.

## Repositories and worktrees

Separate product topology from Git layout; `delivery.yaml` is the stable routing
contract across one repo, monorepo or multi-repo.

Implementation closes in each `integration_branch`, or `dev` without active
contract. Work there or on a short branch based on it, then integrate and push.
Never stop on an ephemeral branch unless local-only was requested. `staging` is
RELEASE unless declared integration; `main`, deploy and upload remain separate.

With active `delivery.yaml`, run sibling
`dautia-ci-cd/scripts/check_checkout.py` once at start and closeout for affected
repos. It is a check, not a phase; otherwise inspect Git directly.

Use worktrees only to protect changes, isolate risk or parallelize; place them in
`<project>/.worktrees/<task>` and retire them when recoverable remotely.

If the checkout is stale, gone or dirty, read its contracts once from
`origin/<integration_branch>` and use an isolated worktree. Never clean it.

For multi-repo increments, change and validate only affected repos, push each
integration branch and close `repo -> branch -> SHA -> evidence`; no empty commits.

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
concise handoff. Inherit history only when unresolved semantics cannot be safely
condensed, and state why.

One release operator owns `(source revision, environment/target, authorized
scope)` and may sequence providers sharing revision, authority, dependencies and
rollback. Reuse it; split only when a limit changes or failure is independently
recoverable. Only root creates it, and it must never delegate to another release
operator; expansion returns to root.

Workflow edits are forward-only. Record version/time; an older root is
`stale_contract` and reloads or restarts before new external mutation.

Read [observability.md](references/observability.md) only for delegated cycles, external waits, incidents, workflow audits, or explicit telemetry requests. Telemetry is diagnostic, never a task stage or completion gate.

## Validation and closeout

For a visible delta, apply `user-surface-value-review` inside validation; skip it
when no visible surface changed or focal evidence is equivalent.

Validate focal -> module -> integration -> E2E -> regression, reordered by risk.
Dependency-only upgrades default to unit, lint, types, build, read-only routes
and focal smokes. Full/mutating E2E, extra browsers/viewports, multi-device,
performance, memory or deep accessibility require a concrete risk or gate.
Filter output; summarize green suites, expand failures and sample visuals.

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
