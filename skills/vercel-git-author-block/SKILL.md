---
name: vercel-git-author-block
description: Use when a Vercel Git deployment fails before build with ERROR, empty or missing build logs, COMMIT_AUTHOR_REQUIRED, author association, readyStateReason mentioning GitHub could not associate the committer, seatBlock.blockCode, attribution.commitMeta, or githubCommitAuthorLogin. This is a narrow triage and remediation workflow for commit-author identity blockers, not a general Vercel deploy skill.
---

# Vercel Git Author Block

Diagnose and fix Vercel Git deployments blocked before compilation because Vercel cannot associate the commit author with an allowed GitHub user.

Use Vercel MCP/plugin tools when available. If not, use the Vercel CLI or API. Do not debug Next.js, env vars, or build code until deployment evidence shows the build actually started.

## When To Use

- Vercel shows `ERROR` or failed checks but build logs are empty.
- Deployment JSON or UI mentions `COMMIT_AUTHOR_REQUIRED`.
- `readyStateReason` says GitHub could not associate the committer with a GitHub user.
- Fields such as `seatBlock.blockCode`, `attribution.commitMeta`, or `githubCommitAuthorLogin` look relevant.
- The user says the Vercel deployment failure is recurrent and asks to identify or fix it.

Do not use this for ordinary build errors, missing env vars, DNS/alias issues, runtime exceptions, or framework compilation failures after the build has started. Use the Vercel deployment/env skills for those.

## Workflow

1. Confirm scope.
   - Identify the repo root, branch, target environment, Vercel project, and failing deployment or commit.
   - Run local git preflight when in a repo:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git show -s --format='%H%n%an <%ae>%n%cn <%ce>' HEAD
```

2. Inspect the deployment object, not just logs.
   - Prefer Vercel MCP/plugin inspection when available.
   - Otherwise use Vercel CLI/API with the deployment id, URL, project, or commit.
   - Capture these fields when present: `readyState`, `readyStateReason`, `seatBlock.blockCode`, `attribution.commitMeta`, `githubCommitAuthorLogin`, `buildingAt`, and check status.

3. Decide whether this is the author blocker.
   - Treat it as confirmed if `seatBlock.blockCode = COMMIT_AUTHOR_REQUIRED` or the reason says the committer could not be associated with a GitHub user.
   - If confirmed, stop investigating app code. The deployment did not fail because of Next.js or build output.
   - If not confirmed, hand off to the relevant Vercel deploy, env, or framework workflow.

4. Verify identity before changing anything.
   - Compare the commit author email with a GitHub email verified on an account connected to the Vercel project/team.
   - Check repo-local and global git identity:

```bash
git config --get user.name
git config --get user.email
git config --global --get user.name
git config --global --get user.email
```

   - Do not invent or guess the correct email. Use user-provided account details or confirmed project documentation.

5. Remediate with the smallest effective change.
   - Prefer repo-local git config unless the user asks for a global identity change.
   - If the user explicitly wants a persistent machine-wide fix, update global git config too.
   - Vercel re-evaluates author identity on a new commit. A config change alone does not repair an already-created deployment.
   - Create an empty commit only when the user has asked to fix/retrigger the deployment or has approved a fresh commit:

```bash
git commit --allow-empty -m "chore: trigger vercel deploy with verified github author"
git push origin HEAD
```

6. Verify the new deployment.
   - Confirm the new deployment reaches `READY` or the expected state.
   - Confirm `githubCommitAuthorLogin` or equivalent attribution now resolves.
   - If a staging/custom domain is the user-facing target, verify that URL too.

## Output

Report:

- failing deployment id or URL
- exact blocker field and reason
- commit author before and after, without exposing tokens
- config scope changed: repo-local, global, or none
- new commit hash if created
- final Vercel deployment state and user-facing URL check

## Pitfalls

- Empty Vercel logs can mean the build never started. Inspect deployment JSON before debugging code.
- Changing git config after the bad commit is not enough; push a new commit to trigger re-evaluation.
- Do not overwrite global git identity unless the user explicitly wants the machine-wide default changed.
- Do not expose Vercel tokens, env vars, or private account data in the final answer.
