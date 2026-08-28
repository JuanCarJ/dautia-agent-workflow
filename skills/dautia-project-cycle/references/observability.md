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

Routine work needs no custom snapshot: the normal closeout already records outcome, tests, Git/external truth and residuals. Generate deep snapshots with `scripts/dautia_cycle_telemetry.py` only for costly external waits, incidents, workflow audits, or explicit telemetry requests. Use `checkpoint` while the objective remains open and `final` only after evidence-backed closeout. Prefer a bounded time window: it permits exact token deltas when counters have a baseline. Unbounded aggregate token totals are suppressed by default because they conflate unrelated objectives; include them only with the explicit CLI override and label them cumulative.

Schema v3 records the operator-supplied `objective_id`, one of the four workflow modes, `dev_closeout`, and an optional release target while remaining able to read v1/v2 registries. Bound the time window whenever one thread contains several user turns; otherwise the snapshot labels its comparison reliability as `multi_turn_unbounded` instead of pretending that every event belongs to one objective. It walks the complete descendant tree, distinguishes direct children and maximum depth, and flags nested release operators. It also separates task starts from completions, agent waits from generic execution waits, and one objective-level skill load from raw file-read calls. Same-turn extra reads may be legitimate pagination; `skill_reload_turns` is the stronger signal that a skill was reopened during the same bounded objective.

Tool telemetry stores only structural volume: call/input/output character counts, largest result, separate large text versus visual/binary results, and safe tool-method names. Visual payload size is not a context-noise alert. It never retains arguments or outputs. Use `--contract-version` with `--contract-changed-at` after a workflow edit; a root that started before that instant but continued afterward is reported as `stale_contract`.

Task-name and `(agent_type, task_name)` fingerprints are privacy-safe duplicate proxies; the authoritative delegation fingerprint remains `(role, baseline, purpose)`. Raw agent/tool/token/skill/wait/plan counts never prove over-orchestration. Investigate only duplicated scope, conflicting work, unused results, unchanged polling with impact, a gate without named risk, or a worse matched comparison. Plan and repeated-release warnings require a bounded objective; wait timeouts become suspicious only with repeated unchanged results. Correct verified friction instead of adding another agent or gate.

Use `dev_closeout=verified` only after every affected repository is integrated and pushed to `dev`, and pass one `--repo-closeout PROJECT=DEV_SHA` per affected repository. Use `local_only` only when the user requested it, `missing` to expose an incomplete implementation, and `not_applicable` outside IMPLEMENTATION. Record `--docs-sync` and `--external-state` when closeout truth matters. These fields diagnose workflow quality; they do not grant Git or release authority.

Root reasoning is `high` by default. Pass `--xhigh-evidence` only when a representative comparison actually demonstrated that `xhigh` improved the outcome; otherwise the extractor flags it. This prevents model effort from compensating for unclear scope, missing acceptance, or excessive orchestration.

Never retain prompts, messages, raw arguments or outputs, connector data, logs, diffs, paths, URLs, personal identities, child IDs, provider credentials, or secrets. Omit unknown counters rather than writing zero. Report ignored or unsupported event types as warnings so instrumentation gaps are visible.

At root closeout state `docs_sync: yes|no|n/a` and `external_state: verified|pending|n/a`. These are concise outcome indicators, not per-agent receipt fields.

At closeout report only decision-relevant coordination: roles/invocations, repeated passes and reasons, reused evidence, failures, residuals, and external truth. Telemetry warnings are advisory signals; they never override root judgment, imply billing, or block work.

## Rollback

Before changing global workflow contracts, keep a verified restrictive backup under `~/.codex/backups/` and report its location at closeout.
