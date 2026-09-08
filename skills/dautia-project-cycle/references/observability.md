# DautIA delegated observability

This reference applies only when the active branch involves delegation, an external wait, an incident, or a workflow audit. Direct work has no ledger, receipt, telemetry, wait policy, or terminal guard.

## Optional per-agent receipt

For a costly, risky, or independently reviewed delegation, end with a compact receipt:

```yaml
task: unique_task_name
role: configured_role
purpose: implementation
baseline: safe_reference
status: complete
outcome: concise_value
evidence: [stable_reference]
changed_baseline: false
retry_required: false
next: concise_action
```

Omit fields that add no decision value. Status is `running`, `waiting_external`, `verifying`, `complete`, `partial`, `blocked`, `failed`, or `interrupted`. Keep values short and free of secrets or raw content.

## Ledger, reuse, and waiting

Track `(role, baseline, purpose)`, freshness, evidence, and replacement reason in root context only when more than one delegation or a risky handoff makes the ledger useful. Reuse fresh evidence. A repeat must identify the changed surface.

Use one watcher per external dependency and prefer provider-native watchers or one durable command over repeated agent follow-ups. A subagent that has returned run identity should not receive a new turn merely because state is unchanged. Use bounded waits, continue independent work where useful, and do not busy-poll. Repeat only when the dependency blocks progress, a checkpoint is due, or changed state is reasonably expected. Persist the next checkpoint for later resumption and return confirmed blockers early.

## External dependencies

Only when required external work exists, separate runtime from objective states: `RUNNING`, `WAITING_EXTERNAL`, `VERIFYING`, `COMPLETE`, `BLOCKED`, `FAILED`. Record compact provider/run identity, expected revision, environment, state, success/failure conditions, monitor identity when waiting, and next action. Never store credentials, tokenized URLs, payloads, logs, or provider responses.

Run `scripts/dautia_terminal_guard.py` before durable external wait or release closure. `WAITING_EXTERNAL` requires a confirmed same-thread heartbeat. Required dependencies that are active, unknown, failed, stale, or identity-mismatched block completion.

## Telemetry

Routine work needs no custom snapshot: the normal closeout already records outcome, tests, Git/external truth and residuals. Generate deep snapshots with `scripts/dautia_cycle_telemetry.py` only for costly external waits, incidents, workflow audits, or explicit telemetry requests. Use `checkpoint` while the objective remains open and `final` only after evidence-backed closeout. Prefer a bounded time window aligned to token snapshots or a session boundary. A start between snapshots excludes the crossing delta, and an unaligned end is partial; the collector never assigns an indivisible boundary interval to the latest model. Unbounded aggregate token totals are suppressed by default because they can conflate objectives; include them only with the explicit CLI override and label them cumulative.

Schema v6 keeps the v5 fields and records the operator-supplied `objective_id`, one of the four workflow modes, `integration_closeout`, the effective integration branch evidence, and an optional release target while remaining able to read v1-v5 registries. Model and reasoning-effort distributions use effective turn segments, including context carried into a bounded window, rather than the last profile seen in each session. Token output includes privacy-safe per-turn/model/effort/counter-epoch segments and aggregates by model plus effort. A counter decrease begins a new epoch: the post-reset snapshot is retained as an observable lower bound, while the unobserved crossing interval increments `unknown_gaps` and makes coverage partial. `reasoning_output_tokens` is a component of output telemetry and must not be added again to `total_tokens`.

Bound the time window whenever one thread contains several user turns; otherwise the snapshot labels its comparison reliability as `multi_turn_unbounded` instead of pretending that every event belongs to one objective. It walks the complete descendant tree, distinguishes direct children and maximum depth, and flags nested release operators. It also separates task starts from completions, agent waits from generic execution waits, and one objective-level skill load from raw file-read calls. Same-turn extra reads may be legitimate pagination; `skill_reload_turns` is the stronger signal that a skill was reopened during the same bounded objective.

Tool telemetry stores only structural volume: call/input/output character counts, largest result, separate large text versus visual/binary results, and safe tool-method names. Visual payload size is not a context-noise alert. It never retains arguments or outputs. Use `--contract-version` with `--contract-changed-at` after a workflow edit; a root that started before that instant but continued afterward is reported as `stale_contract`.

Task-name and `(agent_type, task_name)` fingerprints are privacy-safe duplicate proxies; the authoritative delegation fingerprint remains `(role, baseline, purpose)`. Raw agent/tool/token/skill/wait/plan counts never prove over-orchestration. Investigate only duplicated scope, conflicting work, unused results, unchanged polling with impact, a gate without named risk, or a worse matched comparison. Plan and repeated-release warnings require a bounded objective; wait timeouts become suspicious only with repeated unchanged results. Correct verified friction instead of adding another agent or gate.

Use `integration_closeout=verified` only after every affected repository is integrated and pushed to the `integration_branch` resolved from that project's effective rules. Pass one `--repo-closeout PROJECT=INTEGRATION_BRANCH@SHA` per affected repository; never substitute a universal `dev` branch. For a legitimate product-code candidate that is not integrated, use exactly one operator-supplied state: `pending_pr`, `pending_review`, or `pending_authority`. They are advisory and do not certify GitHub, checks, the reviewed head, or merge authority; telemetry records no PR URL, number, title, comment, path, or free text. Use `local_only` only when the user requested it, `missing` to expose an incomplete implementation, and `not_applicable` outside IMPLEMENTATION. A pending state produces `implementation_candidate_pending`; a final accepted/released outcome also produces `pending_candidate_with_terminal_outcome` so the snapshot cannot look integrated by omission. Record `--docs-sync` and `--external-state` when closeout truth matters. These fields diagnose workflow quality; they do not grant Git or release authority.

Resolve the effective model and reasoning profile from the active routing policy. Pass `--xhigh-evidence` only when a representative comparison actually demonstrated that `xhigh` improved the outcome; otherwise the extractor flags it. This prevents model effort from compensating for unclear scope, missing acceptance, or excessive orchestration.

In durable telemetry snapshots, never retain prompts, messages, raw arguments or outputs, connector data, logs, diffs, paths, URLs, personal identities, child IDs, provider credentials, or secrets. The separate workflow evaluator may keep only its synthetic sanitized cases and answers as private scratch (directory 0700, files 0600) for reproducible grading; these are never appended to the telemetry registry. `--host-id` is optional and must be a stable non-personal operator label. Acceptance at first pass, human corrections, and human-intervention minutes are emitted only when explicitly supplied; absence means unavailable, never zero. Report ignored or unsupported event types as warnings so instrumentation gaps are visible.

At root closeout state `docs_sync: yes|no|n/a` and `external_state: verified|pending|n/a`. These are concise outcome indicators, not per-agent receipt fields.

At closeout report only decision-relevant coordination: roles/invocations, repeated passes and reasons, reused evidence, failures, residuals, and external truth. Token fields describe processed session telemetry. They do not establish API billing, Codex credits, subscription use, monetary cost, or causal model quality. Telemetry warnings are advisory signals; they never override root judgment or block work.

## Rollback

Before changing global workflow contracts, keep a verified restrictive backup under `~/.codex/backups/` and report its location at closeout.

## Route conformance

During an explicit workflow audit compare the decided route with actual own-turn
model/effort and child linkage, not role names or requested configuration. Missing
observations are unknown. Separate mandatory failures, conditional applicability
and preferences; stale creation time alone does not prove instructions were not
reloaded. Preserve privacy constraints above; no per-command telemetry gate.

## Runtime completion correction · 2026-09-08

`sessions.complete` reflects the latest identifiable runtime turn at the window
boundary, not any historical completion. `latest_turn_states` distinguishes open,
completed, aborted and unknown; historical start/completion counts remain separate.
A new open turn invalidates the earlier completion as evidence of an exact token
end boundary. Late terminal events with a different turn ID do not close it.
These fields still do not certify acceptance, integration or provider completion.
Compare profile activity with positive observed output, not initialization contexts
alone, when auditing effective routing.
