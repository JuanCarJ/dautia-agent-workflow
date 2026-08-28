# Isolated WSL workflow

Use this reference for mutation planning and review. Examples are generic; replace every placeholder with the explicitly selected project's values.

## Boundaries and naming

Choose stable, unique names before activation:

```text
project_id: <explicit-id>
local_root: /absolute/path/on/mac
wsl_root: /srv/codex/<explicit-id>
compose_project: codex-<explicit-id>-<purpose>
network: codex-<explicit-id>-<purpose>
volumes: codex-<explicit-id>-<purpose>-db, codex-<explicit-id>-<purpose>-storage
stack_kind: ci | dev
docker_ports: 127.0.0.1:<host-port>:<container-port>
dev_relay: <active-tailscale-ip>:<api-or-db-port> -> 127.0.0.1:<docker-port>
reset_allowed: false
```

- Keep WSL worktrees on the Linux filesystem rather than `/mnt/c` when build and database I/O matter.
- Reject names already owned by another project. Existing unrelated containers, networks, volumes, and ports are immutable anti-scope.
- Bind every Docker-published service to `127.0.0.1`. CI and administration use loopback plus SSH tunnels.
- For an explicitly approved `*-dev` stack, a host relay may bind only the exact active Tailscale IPv4 and forward only the minimum API/DB ports to Docker loopback. Never bind Docker directly to Tailscale, `0.0.0.0`, a LAN address, or IPv6. Treat the whole authenticated tailnet as trusted only when the user explicitly accepts that boundary.
- Create new persistent volumes for each project/purpose. Reusing a database volume is a data-boundary decision, not a convenience.

## Source baseline and transfer

Generate the source manifest before transfer. At minimum include:

```text
schema_version
source_root
git_head
git_branch
dirty: [{path, status, sha256|null}]
```

Hash regular dirty and untracked files; represent deleted paths with a null hash. Hash the canonical JSON manifest itself and record only that digest in the connection registry. Record the observation time beside the manifest, not inside the content digest, so identical source state produces an identical digest.

Transfer from the approved source root into the explicit WSL root. Prefer an archive or `rsync -a`-style copy that does not delete destination content by default. Exclude Git-ignored caches/build outputs and secrets according to the project contract. Never use `--delete` merely to make the trees match. After receipt, regenerate the manifest and explain any expected path or metadata differences before activation.

## Local-only Supabase and Docker guards

Before creation, inspect the rendered configuration, not only the source YAML/TOML:

- all Docker-published ports use `127.0.0.1:<port>:<port>` or a stricter Unix-socket path;
- compose project, containers, networks, and volumes are unique;
- images and resource limits are explicit enough to fit observed WSL capacity;
- healthchecks exist for required database, API, and web services;
- test credentials and fixtures are synthetic or approved;
- no production hostname, provider project ref, remote database URL, or deploy token appears.

For Supabase, allow local lifecycle commands only. Prohibit `supabase link`, `db push`, `functions deploy`, remote secrets, provider project refs, and any command that targets a hosted project. Treat migrations, Auth configuration, RLS, seed data, dumps, and fixtures as `data_security` review surfaces.

For Docker, never run host-wide cleanup. Prohibit `docker system prune`, `docker volume prune`, `docker compose down -v`, `docker rm -f` against unscoped names, or deletion of pre-existing resources. Teardown removes only the selected project's containers/network when authorized and preserves persistent volumes unless the user separately authorizes their exact deletion.

## Preflight modes and existing-stack identity

Use `prepare-new` before creating a stack. Declare required ports and capacity thresholds; failure of the project path, Git baseline, Docker daemon, Compose plugin, capacity, or port-availability checks is terminal for that gate.

Use `verify-existing` only with all of:

- explicit project path and project ID;
- exact Compose project name;
- absolute path and expected SHA-256 of a project-scoped identity manifest;
- every loopback port the existing stack is expected to own.

The identity manifest is a small non-secret JSON file owned by the project lifecycle. It must contain non-null `project_id`, `compose_project`, and `source_manifest_sha256`. Hash the complete identity file and supply that expected digest to preflight. The checker reports only its path, digest, validity, and allowlisted identity fields; it never prints arbitrary manifest content.

For a real Git checkout, `source_manifest_sha256` must match the canonical source manifest computed from the checkout. For an immutable package/release directory without `.git`, the identity must also contain an absolute `source_manifest_path`; its `source_manifest_sha256` must match that complete file. The referenced source manifest must contain non-null `git_head`, `git_branch`, and at least one SHA-256 `content_digest` or `dirty_digest`. This preserves Git provenance without requiring the deployed release directory itself to be a checkout. Reject a missing file, null field, digest mismatch, or a deployment that provides neither a verifiable checkout nor a verified package manifest.

An existing stack passes only when the identity digest and fields match, Docker returns at least one container and network labeled `com.docker.compose.project=<expected>`, every requested Docker port is listening and published by those containers, and every Docker binding is loopback-only. A CI stack has no relay. A dev stack must additionally prove that the expected Tailscale IPv4 is currently active, each declared API/DB systemd relay unit owns its separate root-owned runtime manifest and live PID, exactly those relay ports listen on that IPv4, and Docker owns none of those relay listeners. A listener on `0.0.0.0`, LAN, IPv6, another Tailscale address, or another process is a failure.

## Staged activation and evidence

Use gates in this order:

1. **Preflight:** run `prepare-new`, or `verify-existing` with the expected identity manifest; require `ok: true` and empty `fail_reasons` before continuing.
2. **Configuration:** rendered config, local-only guard, name collision check, resource plan, rollback.
3. **Database:** create exclusive volumes; start database/storage; verify health. A persistent dev stack is controlled only with `sudo dautia-local-stacks start|stop|status sidequest|myroof|all`; start/stop preserve volumes, and start never resets, migrates, restores, or seeds.
4. **Data:** for `*-dev`, record a pre-snapshot, apply forward-only migrations, verify source/target counts, then record a post-snapshot. Never reset dev. For `*-ci`, a protected isolated run may reset logical data while preserving its exclusive volumes. Run schema, RLS, Auth, and privacy checks.
5. **Application:** start API/web/test services; verify health and logs for the selected project only.
6. **Tests:** run project commands; preserve concise exit/result evidence outside the registry.
7. **Lifecycle:** stop or retain as approved; report containers, ports, networks, and preserved volumes exactly.

Do not advance after a failed gate. A later green gate does not erase an earlier unresolved failure.

## macOS and WSL platform split

Use WSL for Linux tooling, API/web services, browser tests, and CI-like commands. Colima is unavailable and must never be started or used. Tests launched from Mac or WSL that need a database connect only to the project's verified staging database; local WSL databases and dev relays are not test targets. Keep Xcode toolchains, Simulator, signing, provisioning, TestFlight/App Store operations, and device QA on macOS. Do not put connection values in shared or versioned env files. Validate HTTP/cleartext behavior, ATS exceptions, OAuth/callback redirect allowlists, and any device-specific routing from the Mac. WSL service health is not iOS QA.

## Retire legacy Colima data without touching originals

This is a recovery/retirement procedure only, never a development or testing workflow. Do not start Colima. Treat migration of legacy SideQuest/MyRoof development data as a `data_security` surface and keep effort proportional to simple development data while preserving a recoverable chain:

1. Identify exact source volumes and capture source schema/table/Auth/Storage counts. Exclude Templo Rojo unless separately named; the controller never infers it.
2. Access original Colima volume files offline and read-only, without starting Colima. Create encrypted raw backups and verified working copies; perform recovery, filtering, and dump generation only from working copies.
3. Produce logical filtered loads for application schemas plus approved `auth.users`, `auth.identities`, and Storage metadata. Exclude sessions, refresh/one-time tokens, MFA/challenges, OAuth/client state, audit state, vault/provider secrets, and other ephemeral credentials.
4. Quarantine orphaned identities, Storage rows, and application references instead of silently deleting or importing them. Record counts and the decision needed for each quarantine class.
5. Take target pre-restore/pre-migration snapshots, load data into the matching `*-dev` target, apply forward-only migrations, verify source/loaded/quarantined counts and focal relationships, then take post snapshots.
6. Keep originals, encrypted backups, working copies, and rollback evidence until equivalence and the approved retention gate are satisfied. Never use `db reset` on dev or delete Colima/volumes as part of migration.

Simple non-production data does not require production ceremony, but it still requires encrypted backup, filtered Auth handling, count reconciliation, orphan quarantine, and a tested recovery point.

## Controller contract

Accept only `sudo dautia-local-stacks start|stop|status sidequest|myroof|all`. `all` expands to SideQuest and MyRoof only. The controller validates the exact project, preserves volumes, keeps Docker on loopback, manages the API and DB dev relays on the active Tailscale IPv4, and emits a separate root-owned runtime manifest for each relay. It never runs reset, migration, restore, or seed during `start`; data changes are separate reviewed operations.

## Runner or helper security gate

Installing a self-hosted CI runner, daemon, persistent helper, startup task, or credential broker is a separate security-sensitive increment. It is never implied by “use WSL for CI.” Require:

- explicit installation authority and owner;
- `data_security` review of trust boundary, repository/org scope, tokens, secrets, filesystem access, network egress, persistence, update path, and cleanup;
- an ephemeral or disposable runner when practical;
- a dedicated unprivileged account and project-scoped work directory;
- no access to unrelated worktrees, Docker resources, host credentials, or production secrets;
- a tested uninstall/revocation path.

Do not put runner tokens, registration responses, job logs, or command output in the connection registry.

## GitHub-to-WSL migration delivery

Treat GitHub as the steady-state source of truth. A local `rsync` handoff is a
bootstrap or explicitly approved diagnostic path, not the normal release channel.

Separate the two database purposes:

- `<project>-ci` is disposable at the logical-data level. A protected CI run may
  rebuild it with `db reset` while preserving its exclusive Docker volumes.
- `<project>-dev` preserves shared development data. Apply forward migrations
  incrementally and take a verified project-scoped snapshot first; never reset it
  merely because a new migration arrived.

Use these gates:

1. A `feature/*` pull request into `dev` validates a fresh isolated stack, all
   migrations, seeds, database tests, lint, and affected consumers. PR and fork
   jobs have no WSL, Docker-host, deployment-secret, or production access.
2. After required checks and merge, a protected `push` to `dev` creates a package
   containing only the approved Supabase/configuration subtree and a canonical
   manifest. Record repository, exact commit SHA, content digest, project ID,
   port family, CLI version, and expected migration range. Exclude `.env`, linked
   refs, caches, private fixtures, build output, and provider credentials.
3. The WSL receiver verifies that the SHA is reachable from the authorized `dev`
   ref, the package digest matches, the project and ports are exact, migrations
   are ordered, and no hosted/staging/production target is present. Reject on any
   ambiguity; never run `git pull` blindly in the active stack.
4. Store releases under a project-scoped immutable SHA directory and update a
   `current` pointer only after snapshot/reset, migrations, healthchecks, and
   focal consumer tests succeed. Record the deployed SHA without secrets.
5. Serialize each project with its own lock. Failure preserves the previous
   `current` release and volumes. For `<project>-dev`, restore the verified
   snapshot when forward recovery is not valid; for `<project>-ci`, rebuild from
   the previous accepted package.

A future self-hosted runner may consume only protected `push: dev` events. It
must not run pull-request or fork code, belong to the Docker group, retain checkout
credentials, or have general `sudo`. Pin actions by commit SHA. Any privileged
helper must expose fixed project-scoped operations, sanitize the environment, and
drop privileges before executing repository-controlled code. Installing that
runner/helper remains a separately reviewed and explicitly authorized increment.

## Registry shape

The optional registry may contain entries shaped like:

```json
{
  "schema_version": 1,
  "projects": {
    "<explicit-id>": {
      "ssh_alias": "windows-wsl",
      "local_root": "/absolute/path/on/mac",
      "wsl_root": "/srv/codex/<explicit-id>",
      "compose_project": "codex-<explicit-id>-<purpose>",
      "stack_kind": "ci",
      "loopback_ports": [15432, 18000],
      "volumes": ["codex-<explicit-id>-<purpose>-db"],
      "baseline_digest": "sha256:<digest>",
      "connection_secret_file": "/project-scoped/private/path/local.env",
      "reset_allowed": false,
      "lifecycle_state": "stopped",
      "verified_at": "RFC3339 timestamp"
    }
  }
}
```

Create the parent directory with mode `0700`, write through a temporary file with mode `0600`, and atomically replace the registry. Validate permissions before reading it. Never interpret an entry as current authorization or automatic project selection.

The registry contains routing metadata only and every new entry begins with `reset_allowed: false`. A dev entry may add `tailscale_ipv4` and API/DB relay descriptors with `port`, `unit`, and `manifest`; these are routing/ownership metadata, not permission to expose more ports or reset data. If local connection values are required, place them in a separate project-scoped secret file or local vault under a `0700` directory with mode `0600`. Permit only local, unlinked values; never store hosted project refs, production credentials, provider tokens, logs, or command output. Never version or print the file. The registry may retain only its path in `connection_secret_file`; do not copy the path or values into source, package, release, or identity manifests, and never call a secret environment file a registry.

## Rollback

Rollback means stop only newly created project-scoped services, restore the previous source directory from an identified local backup or baseline, and leave pre-existing resources untouched. Preserve new persistent volumes for inspection by default. If exact volume deletion is later authorized, name every volume and verify ownership before removal; never translate that approval into `-v` or a prune command.
