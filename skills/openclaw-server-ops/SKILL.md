---
name: openclaw-server-ops
description: "Diagnose or operate OpenClaw on the user's `servidor_do_1` host, including gateway or agent-runtime failures, MCP registration and probes, cron jobs, WhatsApp inbound media, workspace exposure, and OpenClaw-backed Redecarga integrations. Use on OpenClaw plus servidor_do_1, harness not registered, gateway healthy but agent failed, MCP unavailable, cron schedule wrong, WhatsApp attachment not saved, or media/inbound issues."
---

# OpenClaw Server Ops

Diagnose OpenClaw application behavior on `servidor_do_1` without confusing host health, gateway health, agent capability, channel ingestion, or downstream workflow behavior.

Also use `digitalocean-ssh-ops` for the SSH, host, Docker, secret, mutation, rollback, and production-safety contract. This skill adds the OpenClaw-specific investigation layer; it does not replace the server skill.

## Authority

Default to read-only inspection when the user asks to review, diagnose, or explain. Editing OpenClaw configuration, installing plugins, registering MCPs, changing cron jobs, restarting the gateway, copying media, or modifying application code requires explicit intent for that action class. Use `release_operator` for delegated external mutations.

Never print tokens, credentials, full OpenClaw config, WhatsApp identifiers, private message contents, or `.env` values. Redact destinations when reporting notification jobs.

## Live Orientation

Do not trust remembered versions or paths without checking the host. Establish live truth first:

```bash
ssh servidor_do_1 'bash -s' <<'REMOTE'
set -euo pipefail
hostname
date -u '+%Y-%m-%dT%H:%M:%SZ'
command -v openclaw || true
openclaw --version 2>/dev/null || true
ps -eo pid,lstart,args | grep '[o]penclaw' || true
find /root/.openclaw -maxdepth 2 -type d -print 2>/dev/null | sort
REMOTE
```

Then inspect `openclaw --help` and the relevant subcommand help before using commands remembered from an older installation.

## Layered Diagnostic Model

Always identify the first failing layer:

1. **Host/process:** SSH works, disk/resources are adequate, and the OpenClaw process exists.
2. **Gateway:** the gateway responds. A heartbeat proves transport, not agent readiness.
3. **Agent runtime/harness:** the requested runtime is registered and can answer a minimal test.
4. **Tooling:** the intended MCP/plugin is listed, probes successfully, and exposes the expected tools.
5. **Scheduler:** the exact job id, timezone, payload, delivery behavior, and computed date window match intent.
6. **Channel ingestion:** WhatsApp or another channel wrote the attachment/event to OpenClaw's inbound store.
7. **Workspace exposure:** the agent or workflow can access the inbound artifact under the active media/workspace policy.
8. **Downstream application:** the target integration or automation consumed the event and produced its expected output.

Do not skip a lower layer just because a higher-level UI reports “healthy.”

## Symptom Playbooks

### Gateway healthy, embedded agent failed

- Capture the exact error and timestamp.
- Verify live gateway/process state.
- Inspect registered runtimes/plugins with the current CLI help and read only the relevant keys from the active config, redacting values.
- Treat `Requested agent harness "codex" is not registered` as a runtime-registration problem, not a generic web-heartbeat failure.
- After an authorized fix, restart only the required component and require a minimal agent reply as the regression check.

### MCP missing or tools unavailable

- Resolve the active OpenClaw config and MCP location from the live installation.
- Use the current equivalents of MCP list and probe; record server name, command/cwd existence, probe result, and tool count.
- Test the MCP directly before registering it when changing code.
- After an authorized registration or reload, probe again and verify one read-only representative tool.
- Keep business-facing output separate from internal status codes or legacy metric names.

### Cron schedule or monitor is wrong

- List jobs as structured data and identify the exact job id before editing.
- Verify host time, scheduler timezone, user timezone, cron expression, payload, and delivery mode separately.
- Dry-run the computed date range for the current date before leaving the job enabled.
- Edit the existing job in place when correcting it; do not create duplicates.
- For “notify me when finished,” require an explicit channel and recipient. Never infer a generic last chat.
- Re-list jobs after mutation and verify no stray duplicate monitor exists.

### WhatsApp attachment appears not to save

- Split the claim into inbound ingestion and later workspace/workflow handling.
- Inspect only metadata for recent files under the live inbound-media directory: timestamp, size, type, and redacted basename.
- If the file exists inbound, do not report an ingestion failure. Trace workspace exposure, `workspaceOnly` or equivalent policy, agent tool roots, and the downstream workflow.
- Do not copy private media into another directory as a diagnostic shortcut without explicit intent and a retention decision.
- Stop at the first confirmed boundary and report the next unverified layer.

## Change Procedure

For authorized mutations:

1. Capture the relevant current config/job/plugin state with secrets redacted.
2. Record a rollback path or backup for the narrow file/object being changed.
3. Make one bounded change.
4. Reload or restart only what the live CLI and docs require.
5. Re-run the layer-specific regression check.
6. Verify the user-visible outcome when possible.

Never use an old command from memory as proof that the current install supports it. Verify with live `--help` or authoritative current documentation first.

## Stop Conditions

A diagnostic is complete when the first failing layer is supported by timestamped evidence and the next action is explicit. A fix is complete only when:

- the intended config/plugin/job/media behavior is present;
- the exact regression check passes;
- no duplicate job, broad restart, leaked secret, or unrelated service change was introduced;
- remaining unverified layers are named honestly.

## Final Response

Report:

- SSH alias and live OpenClaw version observed;
- symptom and first failing layer;
- read-only evidence collected;
- state-changing commands, if explicitly authorized;
- regression result and user-visible outcome;
- residual risks or unverified layers.
