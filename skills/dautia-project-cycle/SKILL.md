---
name: dautia-project-cycle
description: Coordinate substantive DautIA work, delegation and closeout. Use for a new multi-step objective; reuse the active context on follow-ups.
metadata:
  version: "15.2.0"
---
# DautIA project cycle

Deliver the authorized outcome, with evidence of acceptance and preserved invariants.
The global/project contracts retain authority, review, environment and Git constraints;
this skill supplies the relevant execution interfaces, not additional permissions.

## Prepare the actual boundary

For material changes or diagnosis, read [prevention](references/r3-prevention.md).
Bind the request, approved decisions, exclusions, sources, candidate and acceptance;
trace affected producers, contracts and consumers. Preserve material examples and
negative findings. Resolve only blocking uncertainties before the dependent change;
continue independent authorized work. A new requirement is not an earlier omission.

Use one compact private packet per active objective/block, following
[packet example](examples/r3-analysis.json). No packet for a trivial direct read.

```sh
# For material implementation, resolve the qualified child first.
python3 scripts/workflow_cli.py dispatch-plan PACKET --agents-dir CODEX_HOME/agents --cwd WORKSPACE
# Add the exact returned runtime.required_agent_type, then run the gates.
python3 scripts/workflow_cli.py gate preflight PACKET --cwd WORKSPACE
python3 scripts/workflow_cli.py gate dispatch PACKET --cwd WORKSPACE
python3 scripts/workflow_cli.py gate closeout PACKET --cwd WORKSPACE
```

For material implementation, dispatch-plan and the exact target precede writing and
preflight; dispatch precedes delegation; closeout precedes handback. Direct trivial
reads and explicit trivial exceptions may run preflight without a child. Exit 3 means unresolved conditions, 2 invalid input/storage. Resolve or report
the boundary, not bypass it. Gates refresh declared sources and check supplied facts;
they do not certify semantic truth, user consent or provider state.

For complete, partial or scratch project documentation, apply
[evidence contract](references/evidence-contract.md) and `scripts/evidence_contract.py`
to the active objective. A functional slice can close while an unrelated demo remains
pending; incomplete active context blocks its product closeout/release, not discovery.

## Delegate material work by default

For a material product, test, migration or versioned configuration change, the
root must delegate the implementation to a qualified implementation agent before
writing: `implementer__PROFILE`, `implementer_complex__PROFILE`, or
`systems_implementer__PROFILE`. The principal may coordinate and inspect, but its
own artifact cannot replace the implementer's terminal receipt. Direct execution
is allowed only for a trivial delta or an explicit user-authorized exception
recorded with `scope: trivial`, `source_kind: user`, `source_refs` and a reason.
“No concurrent work” is not enough to bypass this rule for material product work.

Every product-code implementation also requires an independent reviewer before
integration. Broad or redesigned visual work additionally requires
`ux_auditor__PROFILE`. If a required child is unavailable or incomplete, closeout
is blocked; report that boundary instead of silently taking over.

Before material delegation read [model routing](references/model-routing.md), prepare
the worker packet and use the dispatch-plan command above. Use observed host availability and the exact returned qualified target. For writers,
resolve decisions and classify execution routine/demanding; unknown requires preparation.
The role policy, not parent effort, selects the profile. Record the exact native target,
`fork_turns: "none"`, actual start, observed model/effort, child reference and completed
terminal receipt in `runtime.dispatch_receipt`; retain `runtime.required_agent_type`.
Prepared JSON is not execution. Generic/mismatched/incomplete children block closeout;
the principal's replacement artifact is not a child receipt. The CLI does not intercept
the native tool. Principal profile choices need evidence and do not change the default.

Keep independent blocks/resources isolated, depth one, one writer/operator per mutable
resource. `workflow_cli.py lease` is a cooperative same-host lease, not a security or
distributed lock. Obtain the independent reviewer's first judgment before comparing
conclusions. Preserve failures rather than route around them or add a provider advisor.

## Check, integrate and finish

Acceptance determines checks and permitted scope. Unknown cause requires diagnosis
before a speculative patch; a refuted premise or regression reopens the affected work.
Retain failed attempts and justify oracle exceptions independently. Broad/redesign
visual work retains the global design-baseline, viewport, responsive, accessibility,
visible-content and independent UX handoff requirements; functional tests alone do not
prove user impact. No live PASS from offline fixtures.

For versioned integration or release, use `dautia-ci-cd`; for workspace reconciliation,
read [Git/workspaces](references/r3-git-workspaces.md). Product review compares original
acceptance and current candidate independently; its author fixes findings. The reviewer
neither edits nor merges the audited candidate. Existing project runbooks prevail
unless the exact change is authorized. External effects need separate authority and
readback; unknown prior effects require reconciliation before retry.

Continue remaining authorized execution, corrections, checks and team handoffs before
handback. Missing hardware/provider access leaves that boundary unverified while
independent work proceeds. Return only actual user decisions, physical actions or proven
external blockers. Respect pause and budget; do not invent ongoing monitoring.

## Conditional tools and references

- Before acting on a platform/provider/UI boundary, load its relevant skill. Do not
  load all platform or equivalent browser skills. `scripts/skill_catalog.py` reads
  actual metadata without deleting collisions or proving usage.
- For telemetry, read [observability](references/observability.md); for installation,
  hooks or client/runtime claims, read [harness](references/r3-harness.md). Installed,
  requested, observed and accepted are separate claims; static tests do not prove runtime.
- Only when using opt-in root hooks: `bind PACKET --session SESSION --generation
  GENERATION --cwd WORKSPACE`. Rebind meaningful changes, preserve pause and restart
  generations only for a genuinely resumed/new run. Binding/parent IDs do not grant
  authority or reset stop limits.
