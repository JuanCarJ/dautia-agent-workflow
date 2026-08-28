# Delivery contract

`delivery.yaml` is the machine-readable source for stable delivery routing. Keep this page only when a human runbook adds provider-specific commands, access requirements, smoke checks, or rollback steps that do not belong in the manifest.

## Product and repositories

Explain the product codebases and whether they live in one repository, a monorepo, or multiple repositories. Link each repository to its `dev` integration path.

## Environments

Explain only observed or deliberately planned integration, staging, and production targets. Never describe a planned branch or disabled target as active.

Inspect branch rules and allowed head patterns before creating a short branch or
pull request. Open promotion pull requests only for an authorized release
candidate; otherwise each new integration SHA can waste CI and preview builds.

## Checks and rollback

List the minimum checks required for each promotion using the names that actually exist in the project, plus the exact rollback references. An observed environment needs at least one reproducible check; a planned environment may use an empty list while deployment remains disabled. Required checks are reusable evidence, not universal job names or mandatory pull-request ceremony.

Implementation closes in `dev`. Staging, main, deployment, upload, and production require explicit release authority.
