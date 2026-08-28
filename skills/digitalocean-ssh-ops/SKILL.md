---
name: digitalocean-ssh-ops
description: "Use when operating the user's DigitalOcean server through SSH alias `servidor_do_1`: production deploys, Docker or Docker Compose services, container logs, healthchecks, server validation, rollback planning, nginx/proxy checks, remote app debugging, or project deployments under `/opt/*`. Trigger on natural language like servidor DO, DigitalOcean, servidor_do_1, entra al servidor, despliega, sube al servidor, rebuild, docker compose, logs del contenedor, valida produccion, deploy proyecto, or app en /opt."
---

# DigitalOcean SSH Ops

Operate the user's DigitalOcean server safely through the SSH alias `servidor_do_1`.

This skill is for remote production-like operations. Prefer evidence, small steps, and reversible changes. Do not print secrets, delete data, remove volumes, or restart critical services unless the user explicitly asked for that exact class of action.

## Connection Contract

- Use SSH alias: `servidor_do_1`.
- Do not ask the user for host/IP if the alias is enough.
- Do not inspect, print, copy, or modify private SSH keys.
- Local alias check, when useful:

```bash
ssh -G servidor_do_1 | sed -n '1,40p'
```

- Remote command pattern:

```bash
ssh servidor_do_1 'bash -lc "hostname && uptime && docker ps --format '\''table {{.Names}}\t{{.Status}}\t{{.Ports}}'\''"'
```

For multi-line remote work, prefer one explicit remote shell block with clear read-only or mutating intent:

```bash
ssh servidor_do_1 'bash -s' <<'REMOTE'
set -euo pipefail
hostname
pwd
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
REMOTE
```

## Safety Levels

Read-only, no extra confirmation normally needed when the user asks to inspect/validate:

- `pwd`, `ls`, `git status`, `git log --oneline -5`
- `docker ps`, `docker compose ps`
- `docker logs --tail`
- `curl` healthchecks
- checking nginx config files without editing
- listing env variable names with values redacted

Mutating, requires explicit user intent in the request:

- `git pull`, `git checkout`, `git merge`
- `docker compose up -d --build`
- `docker compose restart`
- editing config, compose, env, nginx, systemd
- changing firewall, DNS, certificates, cron, secrets

Destructive, require action-time confirmation even if the user generally asked to fix things:

- deleting files, images, containers, volumes, databases, backups, logs needed for diagnosis
- `docker compose down -v`, `docker system prune`, `rm -rf`
- rotating/removing secrets
- dropping DB schemas/tables

## Production Preflight

Before deploy or restart, gather the smallest useful snapshot:

```bash
ssh servidor_do_1 'bash -s' <<'REMOTE'
set -euo pipefail
hostname
uptime
df -h /
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
REMOTE
```

Inside the project directory:

```bash
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git branch --show-current 2>/dev/null || true
git status --short 2>/dev/null || true
git log --oneline -5 2>/dev/null || true
ls -la
```

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
docker compose ps 2>/dev/null || true
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

3. Update code only when deploy intent is explicit:

```bash
git fetch --all --prune
git status --short
git pull --ff-only
```

If `git status --short` is not clean, stop and report before pulling unless the project runbook says those changes are expected.

4. Rebuild/restart with the narrowest service set that satisfies the request:

```bash
docker compose up -d --build <service-a> <service-b>
```

If the project has a wrapper script, use it instead of raw compose when appropriate.

5. Validate:

```bash
docker compose ps
docker compose logs --tail=120 <service>
curl -fsS https://example.com/health
curl -k -I https://example.com/
```

6. Report:

- project path
- previous and current git commit
- services rebuilt/restarted
- healthcheck URLs and status
- relevant log lines
- rollback path if validation failed

## Copied Project Deployment Workflow

Use this subsection when a project on `servidor_do_1` is deployed as a copied tree under `/opt/*` rather than as a normal Git checkout. This pattern applies to any project on the server, not just one app.

Known context to resolve and verify before acting:

- local repo path from the current workspace, user prompt, or repo docs
- remote project path, usually `/opt/<project>`
- Docker Compose service name(s) to rebuild
- public host and healthcheck routes from docs, proxy config, or user prompt
- whether the remote path is a Git checkout, a copied deploy tree, or something else

Start locally, not on the server:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
```

Then run the project-specific validation/build commands from docs or package scripts before deploying. Examples for Node/Vite/React projects are `npm run check` and `npm run build`, but do not assume Node if the repo uses another stack.

If the user asks to commit before deployment, stage only source/deploy files that belong to the requested change. Do not commit generated evidence or local assistant folders such as `output/playwright/`, `.playwright-cli/`, `.claude/`, or `NOCODE/` unless the user explicitly asks for those artifacts.

On the server, first determine whether the target path is a Git checkout or a copied deploy tree:

```bash
ssh servidor_do_1 'bash -s' <<'REMOTE'
set -euo pipefail
PROJECT_PATH="/opt/<project>"
cd "$PROJECT_PATH"
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status --short 2>/dev/null || true
docker compose ps 2>/dev/null || true
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
REMOTE
```

If the remote path is not a Git checkout, deploy the exact committed local state instead of copying a dirty workspace. If the local repo is dirty and those changes must deploy, commit the intended source changes first or stop and report that `HEAD` does not include them.

```bash
PROJECT_SLUG="<project>"
git archive --format=tar HEAD | gzip > "/tmp/${PROJECT_SLUG}-head.tar.gz"
scp "/tmp/${PROJECT_SLUG}-head.tar.gz" servidor_do_1:"/tmp/${PROJECT_SLUG}-head.tar.gz"
```

Then on the server:

```bash
ssh servidor_do_1 'bash -s' <<'REMOTE'
set -euo pipefail
PROJECT_PATH="/opt/<project>"
PROJECT_SLUG="$(basename "$PROJECT_PATH")"
SERVICE="<compose-service>"
ARCHIVE="/tmp/${PROJECT_SLUG}-head.tar.gz"
cd "$PROJECT_PATH"
mkdir -p "/opt/${PROJECT_SLUG}-backups"
backup="/opt/${PROJECT_SLUG}-backups/${PROJECT_SLUG}-$(date +%Y%m%d-%H%M%S).tgz"
tar --exclude='.env' --exclude='node_modules' --exclude='.git' -czf "$backup" .
tmpdir="$(mktemp -d)"
tar -xzf "$ARCHIVE" -C "$tmpdir"
rsync -a \
  --exclude='.env' \
  --exclude='node_modules' \
  --exclude='.git' \
  "$tmpdir"/ ./
rm -rf "$tmpdir"
docker image tag "${SERVICE}:latest" "${SERVICE}:rollback-$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
docker compose up -d --build "$SERVICE"
docker compose ps
REMOTE
```

Do not add `--delete` to `rsync` unless the user explicitly asks to remove stale files and you have confirmed there are no server-owned runtime directories that would be deleted. The backup protects rollback, but it is not permission to erase unknown production artifacts casually.

If the remote project path is a clean Git checkout and the remote is configured, prefer the generic Git pull workflow instead. If it is dirty, stop and report before pulling.

Validate both HTTP and container health:

```bash
ssh servidor_do_1 'bash -s' <<'REMOTE'
set -euo pipefail
PROJECT_PATH="/opt/<project>"
SERVICE="<compose-service>"
cd "$PROJECT_PATH"
docker compose ps
docker compose logs --tail=120 "$SERVICE"
# Replace these with project-specific public routes from docs/proxy/user prompt.
curl -fsS -o /dev/null -w '%{http_code}\n' https://example.com/
curl -fsS -o /dev/null -w '%{http_code}\n' https://example.com/health || true
REMOTE
```

For admin UI changes, also run a browser or Playwright smoke against the public admin route when credentials are available. Report local validation and remote validation separately. If prior memory or docs contain project-specific routes like `/`, `/admin`, or `/admin/automatizaciones`, treat them as hints and verify they are still correct before using them.

Do not touch unrelated backend automations just because a UI deploy touches the same product area. When the user says an existing flow already works, solve the requested presentation/deploy problem without reworking that flow unless explicitly asked.

## Rollback Pattern

Before risky deploys, know the previous commit:

```bash
PREV="$(git rev-parse HEAD)"
printf 'Previous commit: %s\n' "$PREV"
```

If validation fails after a code deploy, prefer a git rollback to the previous known commit plus rebuild of affected services:

```bash
git checkout "$PREV"
docker compose up -d --build <affected-services>
docker compose ps
```

Only use this when rollback is explicitly needed or approved; explain data/schema risks first if migrations were involved.

## Final Response Requirements

When this skill is used, include:

- whether SSH alias `servidor_do_1` was used
- what remote path was operated
- what commands changed state, if any
- validation evidence
- unresolved risks or follow-up checks

Do not include secret values, private keys, full env files, or unnecessary server internals.
