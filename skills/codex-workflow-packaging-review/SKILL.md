---
name: codex-workflow-packaging-review
description: "Audit recent Codex work, Memories, Chronicle, installed skills, custom agents, and automations to find repeated manual workflows worth packaging. Use when the user asks to look back over recent work, identify recurring workflows, reuse existing capabilities, or create only the smallest high-confidence skill, subagent, or automation."
---

# Codex Workflow Packaging Review

Turn recent work history into a small, evidence-backed set of reusable assets. Default to reuse or skip; creation is the exception.

## Scope

Use this workflow for a cross-session retrospective, normally covering the last 30 days or all available history when shorter. It may recommend or create:

- a skill for a stable procedure or playbook;
- a custom subagent for a bounded specialist investigation with a clear handoff;
- an automation for a real cadence, monitor, reminder, or recurring report;
- an extension to an existing asset;
- nothing, when evidence or repeatability is insufficient.

Do not use this skill to implement the underlying product work found in history. Package only the reusable workflow.

## Evidence Order

Use the strongest available evidence in this order:

1. Recent Codex threads and their turn summaries. Use thread timestamps and read the relevant turns; a sidebar title alone is not an occurrence.
2. `MEMORY.md` and the rollout summaries it points to. Treat remembered commands, paths, versions, and external state as potentially stale.
3. Chronicle, only when enabled and verified. Use it to discover work outside Codex, not as the final authority for important details. Upgrade material findings to the relevant repo, app, connector, server, or provider when possible.
4. Installed personal/plugin skills, custom agents, and automations. Reuse or extend before creating.

Run `scripts/inventory-local-assets.sh` when local Codex assets are available. Supplement it with the app's thread and automation tools; the script does not inventory remote/plugin capabilities.

## Build the Candidate Set

Atomize each workflow into:

- trigger or input;
- repeatable procedure;
- output or stopping condition;
- dates and distinct occurrences;
- time, risk, context, or error cost;
- current coverage.

Count distinct sessions or real-world executions, not repeated messages inside one unresolved incident. One occurrence may qualify only when recurrence is clearly likely and repeating it would be costly.

Reject a candidate if any required part is unstable, ambiguous, sensitive without a safe boundary, or lacks a clear result.

## Coverage Gate

Before recommending creation:

1. Compare the candidate against installed skill descriptions and actual instructions.
2. Compare it against custom-agent roles and their handoff boundaries.
3. Inspect existing automations before proposing another schedule or monitor.
4. Prefer an extension when one current asset owns the same trigger, procedure, and result.
5. Prefer composition when existing assets together cover the work without forcing the user to reconstruct missing context.

Do not create a project-specific duplicate of a generic skill merely because the evidence came from one project.

## Prompt and Agent Contract Gate

When reviewing skills, agents, or prompt stacks, use representative real traces and prefer surgical edits. Check whether each contract states the outcome, success criteria, evidence, authority, relevant tool routing, required output, and stop rules. Remove repeated process/style rules, obsolete scaffolding, irrelevant tools, and contradictions before adding instructions.

Evaluate the models and reasoning efforts actually configured in the current environment. Do not preserve, raise, or lower an effort level from role names or aggregate activity counts alone. Change one prompt group, model, or effort level at a time and rerun the same representative cases. Compare correctness and completeness first, then total calls, turns, retries, tokens, latency, cost, duplicated evidence, and time waiting without new signal. Never use model choice or reasoning effort as a substitute for missing acceptance, dependency, routing, or validation rules.

For long-running workflows, distinguish productive build/verification time from coordination and promotion lead time. Penalize repeated unchanged polling, stale persisted reasoning, redundant agents, re-reading stable baselines, and gates that do not reduce a named risk. Prefer sparse updates at major phase changes and a stop once the requested outcome has enough evidence.

Treat these as candidate orchestration regressions only when traces show that they harmed the requested result: a user-aborted goal for excessive duration, repeated waits without a dependency signal or state change, repeated task fingerprints, repeated `task_complete` without terminal outcome, full-history forks without evidence need, or a prepared artifact that never reaches an authorized promotion. Diagnose the cause before changing the contract; elapsed time or a timeout ratio alone is not proof of poor orchestration. Do not hide confirmed failures behind green tests or high local product quality.

Also treat false-positive routing as a regression: selecting a skill from a keyword instead of the requested outcome, surfacing a non-blocking governance contradiction before the product finding, justifying read-only work with unrelated branch commentary, or using GUI automation when CLI, MCP, logs, code, or a specialized browser provides equivalent evidence. Test edits against the original user prompt and require the response to lead with that prompt's outcome.

## Maintain instructions with progressive disclosure

Focused methods update: 2026-09-09. Give each conditional reference a concrete
trigger and expected use; improve that pointer before copying its contents into
the entrypoint. Keep caveats with the rule they qualify and one authoritative
owner for each requirement. Preserve explicit authority and environment guards;
do not remove them based on a theory about negative phrasing or model capability.
Validate edits against representative requests and contradictory cases, rather
than assuming shorter instructions improve quality. Reuse existing canonical
sources instead of adding a parallel glossary, tracker or model-specific catalog.

## Choose the Smallest Form

- **Skill:** procedural knowledge, stable checks, or a repeatable operational playbook.
- **Custom subagent:** bounded specialist work that benefits from independent delegation and ends in a defined handoff. Do not create a role just to rename an existing agent.
- **Automation:** a verified cadence or event, stable project/destination, non-ambiguous prompt, and safe authority. Do not invent a schedule.
- **Extend existing:** the same owner already exists and only a real gap is missing.
- **Skip:** covered, one-off, unclear, overly broad, unsafe, or under-evidenced.

## Creation Gate

Create only high-confidence missing items. For every item created:

- keep the trigger narrow enough to avoid accidental invocation;
- separate read-only discovery from mutating actions;
- make source-of-truth and staleness rules explicit;
- define a clear stopping condition and final evidence;
- preserve existing user files and plugin caches;
- add `agents/openai.yaml` with a concise display name, description, and `$skill-name` default prompt;
- validate frontmatter, referenced paths, shell syntax for scripts, and a representative dry run when safe.

If a general skill-creation validator is unavailable, perform equivalent local checks and report that limitation honestly.

## Required Shortlist

Present the decision before the creation summary using these columns:

| Repeated workflow | Evidence and dates | Frequency / confidence | Form | Decision |
| --- | --- | --- | --- | --- |

Keep evidence compact but specific enough to distinguish separate occurrences.

## Closeout

Finish with:

- assets created or extended and their paths;
- validation performed;
- candidates deliberately skipped because they are covered or unsuitable;
- candidates that need more evidence;
- automation and custom-agent decisions;
- any reliance on unverified or potentially stale memory.

Do not claim that a skill, agent, or automation is active until its files or external state were actually verified.
