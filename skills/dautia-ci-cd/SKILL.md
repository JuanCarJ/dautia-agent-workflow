---
name: dautia-ci-cd
description: Define and validate a compact delivery.yaml for product codebases, Git layout, the project-specific integration branch, lifecycle environments, required checks, and rollback. Use when delivery topology or CI/CD policy changes; it does not execute a release.
---

# DautIA Delivery Contract

Use this skill when a project needs stable routing for implementation or release. Do not use it for ordinary coding, documentation reading, or provider operations.

Create or update one root `delivery.yaml` from `assets/delivery.yaml`. It uses the JSON-compatible subset of YAML 1.2 and contains only stable facts:

- product topology: `single-codebase` or `multi-codebase`;
- Git layout: `single-repo`, `monorepo`, or `multi-repo`;
- repository locations and their integration branch;
- codebase ownership, status, and delivery target;
- integration, staging, and production branch roles;
- reusable checks and rollback references.

When a product uses a hosted database, `provider_projects` may map its stable,
non-secret identity per environment. For Supabase record only `provider`,
`environment`, `project_ref`, and the repository-relative CLI `workdir`. Never
store a database password, access token, service-role key, connection string, or
the name of a secret-bearing environment variable in this contract.

Keep mutable runtime state, current incidents, provider deployment IDs, temporary branches, credentials, and worktree paths out of this file. They belong in `CURRENT.md`, evidence artifacts, or the provider.

Use schema v2 for new or migrated contracts. The validator still accepts legacy v1 so existing projects do not break. A v2 `active` contract must be complete; a `draft` contains only identity and an activation blocker. Planned branches and codebases must keep deployment disabled.

Implementation closes in every affected repository's declared `integration_branch`; when the active contract does not define one, the fallback is `dev`. `staging` is a release target unless the project deliberately declares it as integration. `main`, deploy, promotion, upload, and production remain explicit release actions. For multi-repo products, the manifest is the routing map; close with `repository -> integration branch -> SHA -> checks`.

Validate with:

```bash
python3 scripts/validate_delivery.py path/to/delivery.yaml --repo path/to/product-root
python3 scripts/validate_delivery.py path/to/delivery.yaml --repo path/to/product-root --require-active
```

Before editing and again at closeout, run the read-only checkout check only for
the affected repositories:

```bash
python3 scripts/check_checkout.py path/to/delivery.yaml --repo path/to/product-root --mode start
python3 scripts/check_checkout.py path/to/delivery.yaml --repo path/to/product-root --mode closeout
```

For v2 multi-repo contracts, repeat `--repository <id>` to limit the check to
the repositories actually affected. `start` accepts a clean short branch based
on the current integration ref and flags dirty or stale state; `closeout`
requires the declared integration branch, a clean tree, and zero divergence
from its upstream. The script is read-only and never fetches, resets, switches,
commits, pushes, or creates worktrees.

For Supabase credential setup or linked CLI execution, read
[`references/supabase-credentials.md`](references/supabase-credentials.md) and
use `dautia-supabase`. Bootstrap once per project ref and machine; later runs
must obtain the database password from the global protected `0600` registry,
which bootstrap imports once from Keychain on macOS, protected terminal input
on WSL, or an ignored onboarding env. Normal commands read only the registry
and must fail closed instead of prompting. The wrapper also injects the official secure
`~/.supabase/access-token` fallback so a CLI binary update cannot reopen its
native credential-store ACL. Application `.env` files remain application
configuration, not the canonical store for CLI or MCP authentication.

The optional `--repo` verifies every branch marked `observed`. For `multi-repo`, repository paths are resolved below that product root.

Use the smallest useful checks and record their real project-specific names. An observed environment needs at least one reproducible check; a planned environment may keep an empty list while deployment is disabled. `required_checks` are delivery evidence, not an instruction to require universal job names, pull requests, reviewers, `CODEOWNERS`, or duplicate CI. A solo owner may commit and push an explicitly requested implementation directly to the declared integration branch after proportional validation.

Before creating a short branch or pull request, inspect the target's real rules, allowed branch patterns, and required checks once. Do not discover them through failed runs. Keep promotion pull requests closed until the user authorizes that release target; an open `dev -> staging/main` pull request can rerun Actions and previews on every new `dev` SHA.

Production enablement requires an observed production branch and concrete rollback references. Staging is enabled only when it belongs to the project's real promotion route; do not invent an environment or branch to satisfy the manifest. Never store credentials or secret-like values.

This skill designs and validates delivery contracts. It grants no authority for staging, main, deploys, provider changes, or production.
