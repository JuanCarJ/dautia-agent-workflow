---
name: dautia-ci-cd
description: Define or validate delivery topology, integration and release checks. Use for delivery contracts or versioned integration/release, not ordinary coding; grants no release authority.
---

# DautIA Delivery Contract — r3

Keep one canonical stable routing map. A product is not necessarily one Git repo.
Use the JSON-compatible subset of YAML 1.2. Existing schema 1/2 contracts keep
their original validator; do not migrate them automatically. New schema 3 supports
independent integration branches and multiple targets per component. See the
synthetic example in `../dautia-project-cycle/examples/delivery-v3-multirepo.json`
and the repository's `docs/project-contracts.md`.

Define product topology, repository layout/locations, each integration branch,
codebase ownership/stack/capability needs, target identities, reusable checks and
recovery. Provider identities must be non-secret. Supabase project refs retain
their dedicated validation; multiple same-environment targets need explicit
component/target disambiguation, never a first-match fallback.

Current deployment IDs, incidents, credentials, feature branches and temporary
worktrees are not stable delivery facts. Keep observed state in CURRENT or the
provider. Draft contracts have a concrete blocker and disabled production, not
invented active infrastructure. Do not force a staging branch or universal dev.

```sh
python3 scripts/validate_delivery.py delivery.yaml --repo . --require-active
python3 scripts/check_checkout.py delivery.yaml --repo . --mode start --json
```

A checkout observation is not integration proof. `--repository ID` scopes each
read. A task worktree may remain on its feature branch after its PR was integrated.
Do not switch an active thread or erase foreign changes to satisfy closeout.
Use the objective's evidence gate plus the baseline/final workspace reconciliation;
`check_checkout --mode closeout` requires `--closure-packet` with integration and
workspace evidence. These helpers do not fetch, reset, stage, commit or clean.

Product code/config follows author -> independent current-candidate review ->
author corrections -> final verdict -> integration with the already granted
project authority. Being a solo owner does not waive independent review. Only an
explicit applicable exception changes that route. Inspect branch protections,
allowed bases, required checks and autodeploy before integration. Do not invent
CI gates or open promotion PRs without the named promotion being authorized.

A multi-repo increment binds all compatible revisions and component evidence;
a passing API does not certify a stale mobile consumer. A push is not deploy,
an upload is not distribution, and runtime health is not a business transaction.
Release targets, operations, candidates and recovery require their own authority.
No destructive data action or production change follows from this skill.

For existing Supabase credentials/linking use
[references/supabase-credentials.md](references/supabase-credentials.md) and the
pinned `dautia-supabase` wrapper. Normal runs use the protected per-host registry,
not repeated prompts, copied secrets or application env files as a CLI credential
store. Schema 3 only changes target resolution, not credential or command safety.
Do not substitute psql, direct supabase/npx or DDL via MCP. Database-dependent
local tests require the project's verified staging target and isolated fixtures.

Choose proportionate checks by changed contract and risk, preserving security,
accessibility, error recovery and affected consumers. A read-only schema validation
never certifies provider state. Capabilities still need verification on the host;
Mac owns iOS/Xcode/signing and WSL does not prove those boundaries.
