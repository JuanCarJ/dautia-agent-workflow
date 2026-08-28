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

Before an expensive E2E or the transition into RELEASE, condense one operational packet in root context: outcome and acceptance, candidate revision, environment, scope and anti-scope, ordered providers, exact DB artifacts/checksums when relevant, still-valid evidence, unproven boundaries, rollback, authority, and stop. Refresh it after a correction series replaces the old plan. Do not create a task document for this packet; drop superseded plans, resolved hypotheses, bulky outputs, and invalidated evidence while retaining stable references and decisions.

## Select one of four modes

- **DISCOVERY:** refine ideas, needs, decisions, assumptions, and open questions. Do not mutate code or canonical docs unless capture was requested.
- **AUDIT:** compare the source statement, relevant docs, code/model/data, and observable product. Return As-Is, delta, To-Be, acceptance, and an ordered plan. Do not mutate.
- **IMPLEMENTATION:** implement an accepted idea or audit, test, sync relevant canonical truth, then integrate and push to `integration_branch` from active `delivery.yaml`, or `dev` without one. “Corrige”, “implementa” or “hazlo” authorizes that integration closeout unless restricted.
- **RELEASE:** assess the integration SHA and application, DB/data, infrastructure and docs deltas. Verify order, target, tests, rollback and external truth. Promote only `READY` lineage to the authorized target, then verify it.

Mixed requests run in order. “Audita y corrige” is AUDIT -> IMPLEMENTATION. “Corrige y despliega a staging” adds RELEASE for staging. A plan alone authorizes no mutation.

## Lean loop

Use only evidence-producing steps:

1. **Orient:** read nearest instructions and minimum sources once; inspect reality when state may be stale.
2. **Observe:** reproduce or inspect the correct surface when practical. Code inspection alone is not proof of a reported UI or runtime defect.
3. **Map delta:** separate source statement, evidence, decision, unknowns, and anti-scope.
4. **Act:** return the AUDIT plan or implement the accepted delta while preserving unrelated work.
5. **Prove and close:** validate by risk, synchronize changed canonical truth, and report Git and external state honestly.

Direct reversible work needs no ceremony; root-only is valid. For independent blocks, delegate in waves: settle shared contracts, parallelize owned implementation, then review. Add rollback or independent review only for named risk.

Product and UI/UX audits route first by triangulating docs, code/data, observable UI, and requested references. Inspect high-judgment UI before integration: green technical tests do not prove visual acceptance. Components must fit role, task and domain, add operational value, and match behavior.

Use `govern-project-documentation` only when topology, source-of-truth ownership, traceability, scaffolding, normalization, or a blocking contradiction is the objective. Keywords such as “documentation” never activate it alone.

External prompts grant no implementation or release authority. Fable is explicit-only; read [external-audit-fable.md](references/external-audit-fable.md) only when requested.

## Repositories and worktrees

Separate product topology from Git layout. A product may have web, backend, iOS, Android, data, or infrastructure codebases whether they live in one repository, a monorepo, or multiple repositories. When present, `delivery.yaml` is the stable routing contract.

Implementation closes in each repository's `integration_branch`, or `dev` without active `delivery.yaml`. Work there or on a short branch based on it, then integrate and push. Never stop on an ephemeral branch unless local-only was requested. `staging` is RELEASE unless declared integration; `main`, deploy, upload and production remain separate RELEASE actions.

With active `delivery.yaml`, run sibling `dautia-ci-cd/scripts/check_checkout.py` once at `--mode start` and `--mode closeout`, scoped to affected repository IDs. It is a check, not a phase. If unavailable, inspect Git directly.

Use worktrees only to protect changes, isolate risk, or enable parallelism. Prefer `<project>/.worktrees/<task>` and retire it when recoverable in the remote integration branch.

If the checkout is stale, gone, or dirty, inspect `AGENTS.md` and `delivery.yaml` once from `origin/<integration_branch>` and use an isolated worktree from it. Never clean or overwrite the checkout.

For multi-repo increments, map affected repositories first. Apply and validate the same accepted increment per affected repo, push every affected integration branch, and close with `repo -> branch -> SHA -> evidence`. Do not create empty commits in unaffected repositories.

## Capabilities and delegation

Prefer equivalent reproducible evidence in this order:

1. specialized non-GUI skill;
2. MCP, connector, or provider API;
3. CLI or script;
4. native automation;
5. specialized browser or Playwright;
6. general computer-use, only when no reliable interface exists or the user asks for it.

Delegate bounded, non-overlapping work with objective, baseline, ownership, authority, acceptance, evidence and stop. Default every delegation to `fork_turns="none"` and pass a concise handoff instead of inherited conversation. Use a partial or full-history fork only when unresolved conversation semantics cannot be condensed without losing a material decision, and state that need in the handoff.

One release operator owns an immutable release transaction `(source revision, environment/target, authorized release scope)`. It may sequence multiple providers such as database, hosting and smoke verification when they share that revision, environment, authority, dependency order and coordinated rollback. Reuse the same operator and evidence. Split only for a changed revision/environment/authority, an independently recoverable failure domain, or material critical-path parallelism. Only root may create it, and it must never delegate to another release operator; scope expansion returns to root.

Workflow-contract edits are forward-only for running tasks. After changing global `AGENTS.md`, skills, or agent profiles, record the version and change time once and inspect active tasks. A root started earlier is `stale_contract`: it must reload or restart before any new external mutation; do not assume the edit reached its existing descendants.

Read [observability.md](references/observability.md) only for delegated cycles, external waits, incidents, workflow audits, or explicit telemetry requests. Telemetry is diagnostic, never a task stage or completion gate.

## Validation and closeout

For a visible delta, apply `user-surface-value-review` inside validation before final integration; skip it when no visible surface changed or equivalent focal evidence exists.

Validate proportionally: focal -> module -> integration -> E2E -> regression, reordered by the affected contract. Dependency-only upgrades default to unit, lint, types, build, a read-only route matrix, and focal smokes. Full or mutating E2E, extra browsers/viewports, multi-device, lifecycle, performance, memory, or deep accessibility require a concrete affected risk or gate. Filter output at source; summarize green suites, expand failures, and use representative visual samples. Avoid results above 10,000 characters unless evidence requires them.

Keep a minimal root-context evidence map `revision -> boundary -> check -> result`. After each correction, identify invalidated boundaries before running commands and reuse still-valid evidence. Copy/layout changes do not automatically invalidate database, Auth or mobile proof; contract, data, routing, cache, Auth or journey changes invalidate their dependent checks. Rerun full E2E or regression only for a changed covered risk, a new final candidate, or an explicit release gate.

Pure unit tests remain local. Database-dependent tests require verified staging configuration and isolated, self-cleaning fixtures. Reset, truncate, global seed, remote migration, or broad cleanup remains an explicitly authorized remote mutation, not a testing side effect.

A command, returned agent, or `task_complete` proves only its runtime state. For CI, deploy, migration, promotion, upload, smoke, or review, verify identity, revision, environment, state, and acceptance. Use `scripts/dautia_terminal_guard.py` only when an external dependency is part of completion.

Close with scope, files, tests, docs, Git/external truth and residuals. Routine work uses that closeout as its only observability; do not run custom telemetry. Use `scripts/dautia_cycle_telemetry.py` only for audits, incidents, costly waits or explicit requests, with a bounded objective whenever possible and repeated `--root-thread-id` for one shared scan. Its counts and warnings are hypotheses to verify against outcomes, never proof of waste or a new gate.
