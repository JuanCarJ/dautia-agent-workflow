# Instruction and routing audit

Focused update: 2026-09-12. This is a read-only audit template within the existing
workflow evaluation skill, not a new task phase or runtime gate.

## Scope and evidence

Inspect applicable AGENTS.md, relevant skills/references, role files and actual
host/task configuration. Separate user instructions, local project exceptions and
model guidance. Compare changed instructions with a cited previous version; if no
baseline exists, mark historical impact unknown. Do not infer that streamlining
for Astra caused a defect merely because a deletion and a defect coexist.

Check for lost test commands, acceptance, environment identity, workflow information
and confirmation requirements. Preserve necessary shared instructions for every
model; Astra needing less prompting does not prove Sol needs less. Verify nearest
project contracts rather than assuming a global Git or deployment policy applies.

Distinguish host default, task override, requested role/profile and runtime-observed
model/effort. A role name, model self-identification or configuration file alone is
not proof of execution. Cite the runtime source when available; otherwise report
not verified. Inspect whether the current harness actually loads separate role or
profile instructions. Switching a model does not automatically switch skills.
Do not change an intentional task override to match a habitual default.

## Recommendations first

Lead with prioritized recommendations and the smallest useful changes. For each
issue include:

| Source and version | Exact instruction (before/after where available) | Potential impact | Evidence and missing evidence | Smallest proposed change |
|---|---|---|---|---|

Separate confirmed conflicts, hypotheses and intentional exceptions. List what
works and should remain. Put model-specific guidance and its verified loading
mechanism in a separate section; avoid duplicating domain skills by model.

List safety, authority/permissions and reduced-verification proposals separately
for user decision. Existing implementation authority remains valid, but an audit
or its plan alone never authorizes changing those boundaries. Do not alter project
exceptions or protections while merely reporting them. Describe the exact project,
target and consequence before proposing reconciliation.

## Real-case evaluation

When outcome evaluation is requested, use comparable real cases with the same
baseline, tools, fixtures and acceptance; vary model/effort deliberately. Include
accepted outcomes met, corrections, escaped defects, elapsed/user time, reported
usage across root and children, and duplicated work. Reuse existing evidence rather
than collecting everything again. Record missing fields as unknown and confounders
explicitly; do not claim causal superiority from unmatched tasks or token counts.

Static checks and simulated cases establish instruction coherence, not measured
savings, real runtime routing or product quality. Use the existing replay runners
only for the requested experiment and within their documented side-effect limits.
Report recommended experiments separately from experiments actually executed.

## Closeout

Return recommendations, evidence, unknowns and decisions pending. Do not modify
files unless implementation is separately authorized. If authorized later, preserve
a baseline, apply only accepted deltas and validate the changed boundaries. Keep
project test commands and acceptance independent of the selected model. Do not
schedule recurring collection or create a new report file by default.
