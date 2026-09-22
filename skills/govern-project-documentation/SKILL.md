---
name: govern-project-documentation
description: Govern documentation topology, canonical sources, traceability, and scaffolding across single-repo, monorepo, or multi-repo products. Use only when documentation governance is the objective or materially blocks it; not for ordinary project-doc reading or product/UI audits that merely notice drift.
---

# Govern Project Documentation

Treat documentation as a versioned operating contract. This skill decides where durable knowledge belongs and verifies relationships between sources; it does not own product requirements or force a documentation phase into ordinary delivery.

Load this file once for the current governance objective and apply it from context. Do not reread it at planning and closeout. Repeat discovery only when topology, authority, canonical paths, or the relevant baseline changed.

## Safety and scope

- Default to read-only when the user asks to audit, review, recommend, or report.
- Create, move, delete, initialize Git, split repositories, scaffold, or rewrite contracts only when implementation was requested.
- Preserve dirty worktrees and unrelated changes. Do not publish, deploy, alter branch protection, or move sensitive sources without authority.
- Never treat an unversioned parent folder as normative merely because it groups repositories.
- Read the nearest instructions and only the documents needed for the stated governance question.
- An incidental contradiction found during product, UI/UX, code, or operational work does not activate this skill unless it changes authority, scope, required evidence, or the ability to proceed. Keep non-blocking drift subordinate to the user's actual objective.

This skill is not triggered merely because a task reads `AGENTS.md`, `CURRENT.md`, requirements, runbooks, or release notes. The root agent may read and update those files as part of normal delivery.

Do not trigger from lexical matches such as "audit", "documentation", "runbook", or "compare" without checking the requested outcome. A UI/UX audit that contrasts the real product with other products remains a UI/UX task even if project documentation is one evidence source.

## Choose audit depth

Use the smallest mode that answers the question:

- **Targeted:** one repo, canonical path, stale document, link, lifecycle label, or local contract. Inspect that delta only.
- **Topology:** ownership across repositories, deployment boundaries, normative homes, or an unknown workspace. Run the workspace audit once, then reuse its baseline.
- **Traceability:** requirement-to-change-to-test-to-environment-to-release evidence.
- **Scaffold/normalize:** create or migrate governance structure from bundled templates after explicit implementation authority.

Run `bash scripts/audit_workspace.sh /absolute/workspace/path` only for topology mode, a first full governance audit, or when repository layout may have changed. Do not run it before every plan or rerun the full audit at closeout; verify only the changed paths and dimensions.

## Topology and document homes

Classify real Git and deployment ownership:

- **single-repo:** one Git repository and primary codebase;
- **monorepo:** one Git repository with multiple codebases;
- **multi-repo:** independently versioned repositories that jointly deliver one product.

Several folders do not make a multi-repo product. In a single repo, keep transverse and technical docs together. In a monorepo, keep transverse truth at root and subtree detail near each codebase. In a multi-repo product, use a versioned governance home for business/product/system truth and keep internal architecture, tests, deploys, and runbooks in each technical repo.

Keep operational systems separate from discovery, design, approved, implementation, staging, production, blocked, superseded, or cancelled initiatives. Do not describe To-Be design as deployed behavior. For established conventions, preserve them instead of migrating solely to match a template.

Read [references/governance-standard.md](references/governance-standard.md) only when selecting canonical allocation or traceability structure. Read [references/usage-workflow.md](references/usage-workflow.md) only when the user asks how to install, operate, test, or roll out this skill.

## Sources, contracts, and traceability

Identify one canonical path per relevant concern: current state, business rules, requirements, architecture/ADRs, design, roadmap, findings, operations, and releases. Flag only evidenced problems such as normative docs outside Git, duplicated mutable state, stale status adapters, broken links, unlabeled As-Is/To-Be content, sensitive inputs without policy, or external sources without owner/version.

Instruction precedence is:

1. current user instruction;
2. nearest `AGENTS.md`;
3. broader project/governance `AGENTS.md`;
4. non-conflicting adapters such as `CLAUDE.md`;
5. canonical topic document;
6. historical material.

When a lower-priority source conflicts but the conflict does not affect the current objective, apply precedence silently and continue. If it matters, describe the exact affected contract; do not infer that all documentation is unreliable.

Keep proposed, accepted, implemented, verified and deployed states distinct. Preserve
source statements and mark superseded decisions; use the existing canonical spec,
not a new SPEC.md by default. Design references include accepted assets/components,
allowed delta and source-to-build lineage. Infrastructure keeps stable non-secret
identities, writer and procedures separate from observed SHA/deployment/incidents.

Keep mutable product state out of agent instruction files. A technical repo that must operate independently should document its role, governance location, Gitflow, environment limits, tests, and fallback when the governance repo is unavailable.

Use stable IDs where formal traceability is required:

```text
business rule -> requirement -> decision/increment -> PR or commit
-> test -> environment -> release or explicit no-release reason
```

Planned work may stop at source, decision, acceptance, and future increment. Do not demand release evidence before implementation exists or a full matrix for a small routine documentation update.

For design documentation ownership or traceability, use
[design continuity](../dautia-project-cycle/references/continuity.md#documentar-el-diseno).
Keep the existing canonical home; ordinary design updates stay with the implementer
and reviewer rather than activating a separate governance pass.

## Implement and verify

For authorized scaffolding, use `assets/templates/` instead of retyping. Replace placeholders, migrate one source-of-truth concern at a time, preserve or mark history as superseded, and update links and local contracts. Do not copy governance templates into an unversioned workspace folder.

At closeout, validate only what changed: normative paths remain versioned, relevant links resolve, obsolete canonical names are absent, and changed repos pass `git diff --check` plus branch/status inspection. Run broader link checks, manifest validators, recursive audits, CI, or provider checks only when the affected boundary requires them.

Return a compact verdict with evidence, topology or document-home decision when relevant, prioritized findings, changed paths, validation, Git state, and residual risk. Do not lead with incidental drift outside the governance objective, create documents, or rerun audits solely to satisfy ceremony.
