---
name: ryven-release-closeout
description: Reconcile and close a SideQuest/Ryven release across multiple environments or Apple/Vercel/Supabase layers. Use only for an explicit release closeout, remote deploy, TestFlight/App Store action, or cross-layer release-state audit; not for routine docs, local fixes, isolated screenshots/privacy copy, or a build-number question.
---

# Ryven Release Closeout

Preserve the real separation between local, dev, staging, production, TestFlight, and App Store state. This is a release-boundary skill, not a general SideQuest workflow.

Load it once for the release objective and apply it from context. Do not reread it for each layer or follow-up. Resolve the SideQuest/Ryven Git root from the current checkout, `delivery.yaml`, and its remote; use another checkout only when the user identifies it.

## Establish release truth

Read the nearest `AGENTS.md`, `docs/CURRENT.md`, and only the release, QA, runbook, or subtree documents relevant to the affected layers. Verify repository root, branch, status, candidate revision/build, target project, and environment. When docs disagree with code or provider state, report and correct the evidenced discrepancy.

Classify the request:

- **local/dev closeout:** validate and synchronize docs locally; integrate only when asked;
- **remote deploy:** mutate Supabase, Vercel, domains, TestFlight, or App Store only with explicit authority;
- **release-state audit:** compare exact candidate identity and provider state without mutation;
- **blocked release:** separate valid local artifacts from external legal, processing, credential, provider, or review blockers.

Track only affected layers: `docs`, `web`, `admin-web`, `marketing-web`, `supabase`, `ios`, `infra`, or `transversal`.

## Proportional validation

Choose the smallest existing project commands that cover the changed boundary. Use focal tests before module, integration, or E2E suites. Remote Supabase checks are only for approved remote work and should be serialized. For web surfaces, verify a production-like build and the actual changed routes. For iOS, keep app, extension, and test build numbers aligned when a release bump is requested, and inspect archive metadata before upload.

Do not upload to TestFlight, submit App Review, deploy, migrate, commit, push, or merge unless the user authorized that action. A local archive is not an uploaded build; an uploaded build may still be processing; TestFlight availability is not App Review submission or release.

When public App Store submission is in scope, verify current Apple requirements from official sources at execution time. Confirm the exact candidate, real-device/TestFlight journey evidence, live privacy/support URLs, privacy answers grounded in current code/providers, accepted screenshot dimensions, metadata, review access, export compliance, and release mode. Keep credentials out of versioned files and reports.

Use precise Apple states: `ready locally`, `upload succeeded`, `processing`, `available in TestFlight`, `ready to submit`, `added for review`, `submitted`, `waiting for review`, `in review`, `pending developer release`, or `released`.

## Documentation and closeout

Update only documents whose truth changed, such as `docs/CURRENT.md`, current QA pending state, increment/release notes, or audit index. Do not open or rewrite all closeout docs by default.

Report affected layers, candidate identity, files, commands and results, Git state, and the separate truth for local/dev/staging/production/TestFlight/App Store. Name remaining blockers by layer. Never imply that implemented means deployed, an archive means uploaded, or an upload means released.
