---
name: windows-wsl-ci-ops
description: Prepare and operate isolated development, database, container, web-test, and CI workloads on the canonical SSH host alias `windows-wsl`. Use when a user explicitly selects a project for WSL, asks to move local Docker or Supabase work off macOS, needs a Tailscale-only development relay, or needs reproducible source/data handoff between macOS and WSL. Do not use for production, linked Supabase projects, automatic project discovery, iOS builds, or generic Windows administration.
---

# Windows WSL CI Ops

Treat WSL as private development/CI infrastructure reached through the SSH alias `windows-wsl`. Keep the main agent responsible for scope and terminal truth.

## Establish authority

1. Read the selected project's `AGENTS.md`, canonical docs, test commands, and environment boundaries on the source machine.
2. Require the user or approved plan to identify the project explicitly. Record its local root, WSL root, workload, ports, compose project, and intended lifetime. Never infer a project from directory names, recent work, or an existing WSL checkout.
3. Classify the stack explicitly as `<project>-ci` or `<project>-dev`. CI remains loopback-only and is resettable only inside an authorized isolated job. Development preserves data and may use the controller-managed Tailscale relay only after the user accepts authenticated-tailnet trust. Refuse production, staging promotion, provider mutation, linked Supabase operation, or destructive cleanup without separate explicit authority.
4. Use `data_security` to review database, Auth, RLS, secrets, migrations, runner credentials, or sensitive fixtures. Use `release_operator` for authorized remote mutations and staged activation; read-only inspection may remain with the auditor or orchestrator.

## Preflight without mutation

Use one explicit read-only mode and declare `--stack-kind ci|dev`:

- Prepare a CI stack: `python3 scripts/wsl_preflight.py --mode prepare-new --stack-kind ci --project <absolute-wsl-path> --port <loopback-port> --dry-run`, then repeat with `--execute` when SSH inspection is authorized.
- Verify an existing CI stack: add `--project-id <id>-ci --compose-project <name> --expected-manifest <absolute-path> --expected-digest sha256:<digest> --port <owned-loopback-port>`.
- Verify an approved development stack: use `--stack-kind dev`, a `*-dev` project ID, loopback Docker `--port` values, and two ordered triplets of `--relay-port`, `--relay-unit`, and root-owned `--relay-manifest` (API first, DB second), plus `--tailscale-ip`.

`prepare-new` exits nonzero with machine-readable `fail_reasons` when the path or Git checkout is missing, a requested port is occupied, Docker/Compose is unavailable, or capacity is below the declared thresholds. `verify-existing` accepts either a real Git checkout whose computed source digest matches the deployment identity, or an immutable source package whose source manifest supplies non-null `git_head`, `git_branch`, and content/dirty digest and whose complete-file digest is referenced by that identity. It also proves that occupied ports, containers, and network belong to the named Compose project. It never accepts a null identity or returns success merely because collection completed.

Stop on any nonempty `fail_reasons`, when the project is ambiguous, or when the requested operation crosses the private dev/CI boundary. Development verification must prove that Docker remains on loopback, each host relay is owned by its declared active systemd unit, and every relay listener uses the one expected active Tailscale IPv4. Never accept Docker, `0.0.0.0`, a LAN address, or IPv6 as the development exposure. Do not print identity-manifest contents, environment values, Docker labels beyond project ownership, or other secrets while diagnosing a failure.

## Build an isolated execution packet

Before copying or activating anything, capture:

- source commit, branch, dirty/untracked path hashes, and a digest of that manifest;
- explicit local and WSL roots;
- unique compose project, network, container, and persistent-volume names;
- stack kind, loopback Docker ports, and health endpoints;
- for approved dev only: exact active Tailscale IPv4 and, separately for API and DB, relay port, controller unit, and root-owned runtime manifest;
- required commands, fixtures, migrations, test evidence, lifetime, and rollback.

Do not reuse another project's persistent volumes. Docker always binds to `127.0.0.1`; never bind Docker to Tailscale, `0.0.0.0`, LAN, or IPv6. Do not copy `.env*`, SSH keys, provider tokens, or production dumps unless the approved plan names a safe source and `data_security` approves the handling.

Read [references/workflow.md](references/workflow.md) before source transfer, Supabase startup, runner/helper installation, persistent-volume creation, or teardown.

## Activate in stages

1. Re-run read-only preflight and compare the source manifest with the approved packet.
2. Transfer into a project-specific WSL path without implicit deletion; verify the received manifest.
3. Render and inspect Compose/Supabase configuration before creation. Enforce loopback Docker bindings and unique names. For approved dev, expose only API/DB through the controller-owned host relay on the exact active Tailscale IPv4.
4. Create only new exclusive persistent volumes, then start the database layer.
5. Verify health. For `*-dev`, take a pre-migration snapshot and apply only forward migrations; never reset. For `*-ci`, reset only within the isolated authorized job. Run data/security contract tests.
6. Start the web/test layer and run the approved test matrix.
7. Stop project containers when finished. Preserve volumes by default; never use `docker compose down -v`, `docker volume prune`, or an equivalent deletion shortcut.

Keep macOS-only work on macOS. WSL may host database, API, web, and test services; Xcode, iOS builds, Simulator, signing, and device QA remain on the Mac. Development apps use project-local Mac env files pointing directly to the approved Tailscale relay; CI and ad hoc administration continue through loopback/SSH tunnels. Record residual cleartext-HTTP, App Transport Security, callback/OAuth redirect, and authenticated-tailnet trust risks instead of treating network reachability as application readiness.

## Use the fixed controller contract

Operate persistent development stacks only through:

```text
sudo dautia-local-stacks start|stop|status sidequest|myroof|all
```

`start` may start existing containers and their relay, but must preserve volumes and must not reset databases, apply migrations, restore data, or seed fixtures. `stop` preserves volumes. `status` is read-only and reports Docker loopback bindings, relay ownership/bindings, project identity, and health. `all` means SideQuest plus MyRoof only. Never infer, include, inspect, or mutate Templo Rojo through this controller.

## Keep a minimal connection registry

If continuity is required, store only routing metadata in `~/.codex/state/windows-wsl-ci-ops/connections.json`. Set the directory to `0700` and file to `0600`. Record explicit project ID, roots, alias, compose project, stack kind, loopback ports, exclusive volume names, baseline digest, lifecycle state, and verification time. Initialize every entry with `reset_allowed: false`. A dev entry may additionally record the exact Tailscale IPv4 and separate API/DB relay descriptors containing port, unit, and root-owned manifest path.

Never store secrets, environment values, command output, source manifests, logs, test output, database contents, or runner tokens in the registry. When an approved local stack needs connection values, keep them in a separate project-scoped secret file or local vault under a `0700` directory with file mode `0600`; allow only local/unlinked values and never log or version them. The metadata registry may reference only its path as `connection_secret_file`, never its values. The registry remains a routing aid, not authority to reconnect, mutate, reset, or select a project automatically.

## Close truthfully

Separate command completion from the user's objective. Report project identity, source/received manifest digests, WSL target, services, ports, volumes, tests, lifecycle state, and residual risks. A running job, healthcheck, migration, or required test keeps the objective in `RUNNING`, `VERIFYING`, or a monitored wait; it is not `COMPLETE` merely because SSH returned.
