---
name: digitalocean-ssh-ops
description: Inspect or operate a named project on DigitalOcean host servidor_do_1. Use when that host is identified, not for generic deploy, Docker or log requests.
---

# DigitalOcean SSH Ops

Operate the user's DigitalOcean server safely through the SSH alias `servidor_do_1`.

This skill is for remote operations on `servidor_do_1`. Prefer evidence, small steps, and reversible changes. Do not print secrets, delete data, remove volumes, or restart critical services unless the user's current instructions clearly authorize that exact target and class of action.

## Ownership and route

- A focused read-only diagnosis may stay with the principal using its effective
  profile.
- Versioned code is prepared by its author and reviewed independently on the
  exact current head before any server operation that deploys that code.
- After authority exists for the named host, project, service and candidate,
  root delegates the remote mutation to one `release_operator`; select its profile through the project-cycle routing policy.
- A separate analytical consultation is useful only while a real cross-system decision remains unresolved. Host
  access failure, an unknown path or missing evidence is not a reason to switch
  models or targets.

One operator owns `(servidor_do_1, project path, service set, candidate SHA,
authorized scope)`. It must not touch neighboring projects, services, data or
providers.

## Connection Contract

- Use the single SSH alias `servidor_do_1` with `BatchMode=yes`,
  `StrictHostKeyChecking=yes`, a bounded `ConnectTimeout`, and
  `ConnectionAttempts=1`.
- Do not ask the user for host/IP if the alias is enough.
- Do not inspect, print, copy, or modify private SSH keys.
- Never fall back to an IP, another host, another user, an ad-hoc identity file,
  disabled host-key checking or an interactive password prompt.
- Local alias check, when useful:

```bash
ssh -G servidor_do_1 >/dev/null
```

- Remote command pattern:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes \
  -o ConnectTimeout=10 -o ConnectionAttempts=1 \
  servidor_do_1 'bash -lc "test -d /opt/PROJECT && cd /opt/PROJECT && docker compose ps SERVICE"'
```

For multi-line remote work, prefer one explicit remote shell block with clear read-only or mutating intent:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes \
  -o ConnectTimeout=10 -o ConnectionAttempts=1 \
  servidor_do_1 'bash -s' <<'REMOTE'
set -euo pipefail
PROJECT_PATH="/opt/<verified-project>"
SERVICE="<allowlisted-service>"
PROJECT_MARKER="<project-owned-marker>"
cd "$PROJECT_PATH"
test -f "$PROJECT_MARKER"
docker compose ps "$SERVICE"
REMOTE
```

Before any project command, compare the remote hostname with the documented
non-secret host identity without printing connection configuration, then verify
the exact project path, a project-owned marker/compose file, service names and
candidate SHA. A successful SSH connection alone identifies no project.

## Safety Levels

Read-only, no extra confirmation normally needed when the user asks to inspect/validate:

- `pwd`, `ls`, `git status`, `git log --oneline -5`
- `docker compose ps <allowlisted-services>` after project identity is verified
- bounded service logs passed through the project's redactor
- `curl` healthchecks
- checking nginx config files without editing
- listing env variable names with values redacted

Mutating, requires clear user intent for the named host/project in the current session. Existing authority persists for the same target and action; do not ask for it again merely because a later step executes the change:

- fetching and selecting an exact reviewed Git SHA
- `docker compose up -d --build`
- `docker compose restart`
- editing config, compose, env, nginx, systemd
- changing firewall, DNS, certificates, cron, secrets

Destructive, resolve the exact targets read-only first and proceed only when the current instructions explicitly include that destructive scope; otherwise ask for the missing authority:

- deleting files, images, containers, volumes, databases, backups, logs needed for diagnosis
- `docker compose down -v`, `docker system prune`, `rm -rf`
- rotating/removing secrets
- dropping DB schemas/tables

## Production Preflight

Before deploy or restart, gather the smallest useful snapshot:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes \
  -o ConnectTimeout=10 -o ConnectionAttempts=1 \
  servidor_do_1 'bash -s' <<'REMOTE'
set -euo pipefail
PROJECT_PATH="/opt/<verified-project>"
SERVICE="<allowlisted-service>"
PROJECT_MARKER="<project-owned-marker>"
cd "$PROJECT_PATH"
test -f "$PROJECT_MARKER"
docker compose ps "$SERVICE"
REMOTE
```

Run host-wide uptime, disk or container inventory only when the user asked for
host capacity/incident scope. Never present a global `docker ps` as project
evidence.

Inside the project directory:

```bash
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git branch --show-current 2>/dev/null || true
git status --porcelain=v1 2>/dev/null || true
```

Resolve `PROJECT_PATH`, expected project marker, Compose file, service allowlist,
public host/health route, reviewed candidate SHA and rollback SHA from the
project's current contract or runbook. Do not discover them by acting on the
first `/opt/*` directory or similarly named container.

If the project path is unknown, search narrowly and read-only. Prefer known paths from `docs/architecture.md`, repo docs, prior runbooks, or user prompt before scanning.

## Environment Files

Never print secret values from `.env`, `.env.prod`, or similar files.

Allowed redacted check:

```bash
awk -F= '/^[A-Za-z_][A-Za-z0-9_]*=/{print $1"=<set>"}' .env.prod | sort
```

If a command needs env vars, prefer the project's wrapper script when one exists, for example `run-prod-compose.sh`, because wrappers usually load the correct env file and avoid misleading unset-variable warnings.

## Docker Compose Deploy Workflow

Use this when the user asks to deploy/rebuild/update a containerized project.

1. Identify project path and compose command:

```bash
pwd
ls -la
find . -maxdepth 2 \( -name 'docker-compose.yml' -o -name 'docker-compose.yaml' -o -name 'compose.yml' -o -name 'compose.yaml' \) -print
ls -la *compose* run-*.sh 2>/dev/null || true
```

2. Capture current state:

```bash
git rev-parse HEAD 2>/dev/null || true
git status --short 2>/dev/null || true
SERVICE="<allowlisted-service>"
docker compose ps "$SERVICE" 2>/dev/null || true
```

3. Select only the exact reviewed candidate when deploy intent is explicit.
`CANDIDATE_SHA` is the SHA authorized for this release and `REVIEWED_HEAD` is
the head named by the independent verdict; they must match. If merge creates a
different release SHA, review that SHA before continuing.

```bash
CANDIDATE_SHA="<reviewed-40-char-sha>"
REVIEWED_HEAD="<reviewed-40-char-sha>"
RELEASE_BRANCH="<project-release-branch>"
test "$CANDIDATE_SHA" = "$REVIEWED_HEAD"
test -z "$(git status --porcelain=v1)"
git fetch --prune origin "$RELEASE_BRANCH"
test "$(git rev-parse "origin/$RELEASE_BRANCH")" = "$CANDIDATE_SHA"
git switch "$RELEASE_BRANCH"
git merge --ff-only "$CANDIDATE_SHA"
test "$(git rev-parse HEAD)" = "$CANDIDATE_SHA"
```

Stop if the checkout is dirty, the reviewed head differs, the remote branch no
longer resolves to the candidate, or a fast-forward cannot produce exactly that
SHA. Do not use a floating `git pull` or deploy a newer head by accident.

4. Rebuild/restart with the narrowest service set that satisfies the request:

```bash
docker compose up -d --build <service-a> <service-b>
```

If the project has a wrapper script, use it instead of raw compose when appropriate.

5. Validate:

```bash
SERVICE="<allowlisted-compose-service>"
PROJECT_REDACTOR="<trusted-project-redactor>"
HEALTH_URL="<project-health-url>"
test -x "$PROJECT_REDACTOR"
docker compose ps
docker compose logs --since=10m --tail=120 "$SERVICE" 2>&1 | "$PROJECT_REDACTOR"
curl -fsS -o /dev/null -w '%{http_code}\n' "$HEALTH_URL"
```

6. Report:

- project path
- previous and current git commit
- services rebuilt/restarted
- healthcheck route class and status without tokenized/private URLs
- bounded, redacted service signals; if no trusted redactor exists, do not copy
  raw logs into chat
- rollback path if validation failed

## Copied Project Deployment Workflow

Use this only when the named project's current runbook proves that its target is a
copied tree. It is a host-level pattern, not permission to apply one universal
file list to every `/opt/*` project. Resolve and verify:

- exact local repo and reviewed `CANDIDATE_SHA`;
- exact remote project path and project-owned identity marker;
- Compose file and allowlisted service names;
- project-specific managed-file manifest, its remote state path and validator;
- health signal, rollback source and any server-owned persistent/runtime paths.

The repository must own the managed-file manifest or allowlist. It contains only
relative deploy-owned paths under that project. Before packaging, fail closed if
the manifest is missing, untracked, invalid, or names `.env*`, credentials,
sessions, runtime state, absolute paths, traversal, assistant output or another
project. Do not print a rejected path. A backup and an overlay must exclude the
same protected classes.

Build from the clean exact reviewed commit, not the working tree or floating
`HEAD`. The project-specific manifest validator decides its path format; the
following illustrates the required boundaries:

```bash
CANDIDATE_SHA="<reviewed-40-char-sha>"
REVIEWED_HEAD="<reviewed-40-char-sha>"
MANIFEST="<project-owned-managed-files>"
MANIFEST_VALIDATOR="<trusted-project-manifest-validator>"
PROJECT_SLUG="<project>"
test "$CANDIDATE_SHA" = "$REVIEWED_HEAD"
test "$(git rev-parse HEAD)" = "$CANDIDATE_SHA"
test -z "$(git status --porcelain=v1)"
test -f "$MANIFEST"
test ! -L "$MANIFEST"
git ls-files --error-unmatch "$MANIFEST" >/dev/null
test -x "$MANIFEST_VALIDATOR"
"$MANIFEST_VALIDATOR" "$MANIFEST"
if LC_ALL=C grep -Eiq '(^|/)(\.env[^/]*|[^/]*credentials?[^/]*|sessions?|runtime)(/|$)' "$MANIFEST"; then
  printf 'blocked: protected artifact class in managed manifest\n' >&2
  exit 1
fi

local_stage="$(mktemp -d)"
source_tree="$local_stage/source"
stage_tree="$local_stage/stage"
mkdir "$stage_tree"
cleanup_local_stage() {
  git worktree remove --force "$source_tree" 2>/dev/null || true
  rm -rf "$local_stage"
}
trap cleanup_local_stage EXIT
git worktree add --detach "$source_tree" "$CANDIDATE_SHA"
rsync -a --files-from="$MANIFEST" "$source_tree"/ "$stage_tree"/
if find "$stage_tree" \( -type l -o -type b -o -type c -o -type p -o -type s \) -print -quit | grep -q . \
  || find "$stage_tree" -type f -links +1 -print -quit | grep -q .; then
  printf 'blocked: unsupported link or special file in candidate\n' >&2
  exit 1
fi
artifact="$local_stage/candidate.tar.gz"
tar -czf "$artifact" -C "$stage_tree" .
if tar -tzf "$artifact" | LC_ALL=C grep -Eiq '(^|/)(\.env[^/]*|[^/]*credentials?[^/]*|sessions?|runtime)(/|$)'; then
  printf 'blocked: protected artifact class in archive\n' >&2
  exit 1
fi
cp "$MANIFEST" "$local_stage/managed-files.txt"
(cd "$local_stage" && shasum -a 256 candidate.tar.gz managed-files.txt > payload.sha256)
```

The validator must also reject absolute/traversing entries and entries whose
resolved source leaves the candidate tree. Links, hardlinks, devices, FIFOs and
sockets are rejected by default. A project may allow a symlink only through an
explicit project rule that proves its relative target remains inside both staged
and destination trees.

Create one remote `0700` staging directory, transfer the artifact, manifest and
digest, then verify the digest and archive types before extraction. Use the same
bounded remote shell for backup, overlay, readback and rebuild so its trap removes
the staging directory on success or failure:

```bash
REMOTE_STAGE="$(ssh -o BatchMode=yes -o StrictHostKeyChecking=yes \
  -o ConnectTimeout=10 -o ConnectionAttempts=1 servidor_do_1 \
  'umask 077; mktemp -d /tmp/dautia-release.XXXXXX')"
case "$REMOTE_STAGE" in /tmp/dautia-release.*) ;; *) exit 1 ;; esac
cleanup_remote_stage() {
  ssh -o BatchMode=yes -o StrictHostKeyChecking=yes \
    -o ConnectTimeout=10 -o ConnectionAttempts=1 \
    servidor_do_1 bash -s -- "$REMOTE_STAGE" <<'REMOTE_CLEANUP'
case "$1" in /tmp/dautia-release.*) rm -rf -- "$1" ;; *) exit 1 ;; esac
REMOTE_CLEANUP
}
trap 'cleanup_remote_stage >/dev/null 2>&1 || true; cleanup_local_stage' EXIT
scp -o BatchMode=yes -o StrictHostKeyChecking=yes \
  -o ConnectTimeout=10 -o ConnectionAttempts=1 \
  "$artifact" "$local_stage/managed-files.txt" "$local_stage/payload.sha256" \
  servidor_do_1:"$REMOTE_STAGE/"
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes \
  -o ConnectTimeout=10 -o ConnectionAttempts=1 \
  servidor_do_1 bash -s -- "$REMOTE_STAGE" <<'REMOTE'
set -euo pipefail
remote_stage="$1"
case "$remote_stage" in /tmp/dautia-release.*) ;; *) exit 1 ;; esac
test "$(stat -c '%a' "$remote_stage")" = "700"
trap 'rm -rf -- "$remote_stage"' EXIT
cd "$remote_stage"
sha256sum -c payload.sha256
tar -tzf candidate.tar.gz >/dev/null
if tar -tzf candidate.tar.gz | LC_ALL=C grep -Eiq '(^|/)(\.env[^/]*|[^/]*credentials?[^/]*|sessions?|runtime)(/|$)'; then
  printf 'blocked: protected artifact class in archive\n' >&2
  exit 1
fi
if tar -tvzf candidate.tar.gz | awk '
  BEGIN { bad=0 }
  substr($1,1,1) != "-" && substr($1,1,1) != "d" { bad=1 }
  END { exit bad ? 0 : 1 }
'; then
  printf 'blocked: unsupported archive entry type\n' >&2
  exit 1
fi
# Continue here with the verified project-specific backup, extraction, overlay,
# managed-file readback and allowlisted rebuild described below.
REMOTE
```

On the server, recheck host identity, project marker, target path and service
allowlist before extracting. Back up only deploy-owned code; exclude `.env*`,
credentials, sessions, runtime state, `.git`, dependencies and persistent data.
Extract to a new temporary directory, rescan archive names, then overlay only the
managed manifest paths without `--delete`.

After the overlay, compare hashes for every managed file between the extracted
candidate and `PROJECT_PATH`. Any missing or mismatched managed file stops the
release and triggers the prepared rollback decision. Persist/read back the
project's managed manifest and compare it with the previous one. Files removed
from the new manifest may be deleted only when the current authority explicitly
includes those exact removed paths; use exact file removal and empty-directory
cleanup, never broad `rm -rf` or `rsync --delete`.

An overlay without authorized removal proves only `managed_manifest_match`, not
an exact remote tree. Report `tree_exactness=partial` whenever stale deploy-owned
files, unknown remote files or an unavailable prior manifest remain. A backup
does not convert unknown files into authorized deletion scope.

If the target is actually a clean Git checkout, use the exact-SHA Git workflow
above. If it is dirty or its topology differs from the runbook, stop without
copying. Never touch a neighboring service merely because it shares Docker,
proxy, database or product naming.

Validate the allowlisted service and project-specific health signal. Do not run
`ps` variants that expose arguments/environments or emit `docker inspect` env.
Bound service logs by service, time/range and line count, redact them on the host
with a trusted project redactor, and emit only the status/error signal required
for the decision. Without a trusted redactor, omit raw logs and report that
surface unobserved. Use TLS verification; never use `curl -k`.

For UI changes, add a focal browser smoke when the authorized public route and
credentials are available. Report source, transfer, service, HTTP/UI readback and
tree exactness separately.

## Rollback Pattern

Before mutation, record the exact previous deployed commit or copied-tree
artifact/managed-manifest digest, the affected service image and the narrow
restore command. A backup is useful only after readback proves it exists and is
readable without exposing protected files.

```bash
PREV="$(git rev-parse HEAD)"
test -n "$PREV"
```

If validation fails after a Git deploy, select the exact previous deployed SHA
and rebuild only the affected allowlisted services:

```bash
git checkout "$PREV"
docker compose up -d --build <affected-services>
docker compose ps
```

For a copied tree, restore only deploy-owned paths from the verified backup and
its prior managed manifest. Do not overwrite `.env*`, credentials, sessions,
runtime state or persistent data. Validate the same service, HTTP/UI signal and
managed-file readback after rollback. Use rollback only when authorized or when
the active release authority explicitly includes automatic recovery; explain
data/schema compatibility first if migrations were involved.

## Final Response Requirements

When this skill is used, include:

- whether SSH alias `servidor_do_1` was used
- acting role and whether work was diagnosis, code preparation/review, or the
  authorized remote operation
- what remote path was operated
- candidate SHA, reviewed-head match and previous rollback identity
- what commands changed state, if any
- allowlisted services, validation/readback evidence and copied-tree exactness
- whether bounded redacted logs were observed or intentionally omitted
- unresolved risks or follow-up checks

Do not include secret values, private keys, full env files, or unnecessary server internals.
