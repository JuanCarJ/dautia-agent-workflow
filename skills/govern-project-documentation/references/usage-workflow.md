# Usage Workflow

## Contents

1. Invocation
2. Modes and authorization
3. Audit workflow
4. New-project scaffold
5. Document-first initiative
6. Normalization
7. Verification and closeout
8. Installation and updates

## 1. Invocation

Explicit invocation:

```text
Use $govern-project-documentation to audit this workspace read-only.
```

Useful prompts:

```text
Use $govern-project-documentation in plan mode. Decide where docs should live; do not edit repos.
Use $govern-project-documentation to scaffold governance for this new multi-repo project.
Use $govern-project-documentation to normalize these sources of truth through a docs-only PR.
Use $govern-project-documentation to verify traceability and worktree state before closeout.
```

Implicit triggers include requests about documentation architecture, AGENTS/CLAUDE alignment, multi-repo governance, functional/architecture planning, traceability, or Gitflow documentation.

## 2. Modes and authorization

| Mode | Default behavior | Authorization |
| --- | --- | --- |
| `audit` | read-only evidence report | implied by review request |
| `plan` | read-only migration plan | implied by planning request |
| `scaffold` | dry-run first | explicit request to create |
| `normalize` | plan/diff first | explicit request to change/move |
| `verify` | read-only closeout | implied by verify/readiness request |

Never infer permission to initialize Git, split repos, deploy, promote branches, delete sources, or install the skill globally.

## 3. Audit workflow

1. Read applicable agent contracts.
2. Run:

   ```bash
   bash scripts/audit_workspace.sh /absolute/workspace/path
   ```

3. Confirm Git roots, codebases, deploy ownership, branches and dirty state.
4. Classify topology and lifecycle tracks.
5. Audit canonical docs, agent contracts, traceability, Gitflow enforcement and sensitive sources.
6. Return findings with evidence and a target structure.
7. Make no writes.

## 4. New-project scaffold

1. Decide single-repo, monorepo or multi-repo before code.
2. Verify Git/repo ownership and authorization.
3. Run scaffold in dry-run mode.
4. Review proposed paths and placeholders.
5. Execute write mode only after approval.
6. Fill project-specific values.
7. Validate manifest, links, traceability and Git status.
8. Commit the governance baseline before the first functional increment.

## 5. Document-first initiative

Use when a future demo/system is being designed while other project surfaces are already operational.

1. Register lifecycle `discovery` or `design`.
2. Keep authority in the governance repo.
3. Preserve established As-Is/To-Be paths; add a manifest instead of duplicating them.
4. Link evidence, business rules, functional requirements, planned architecture, open decisions, risks and acceptance criteria.
5. Keep implementation repos non-authoritative until the entry gate is approved.
6. When approved, pin governance commit/version in technical repos.

## 6. Normalization

1. Start from a clean branch/worktree.
2. Inventory and hash sources before moves.
3. Classify active, historical, superseded, evidence and sensitive artifacts.
4. Move one source-of-truth concern at a time.
5. Preserve pointers/provenance before deleting duplicates.
6. Update AGENTS/CLAUDE and links.
7. Run project tests only in proportion to affected runtime files.
8. Deliver via PR; do not combine promotion/deploy unless asked.

## 7. Verification and closeout

Require:

- canonical path per concern;
- valid links and IDs;
- lifecycle-appropriate traceability;
- branch-flow compliance;
- tests/environment evidence;
- composite SHAs for multi-repo releases;
- `git diff --check` and `git status --short` per repo;
- explicit residuals.

Never collapse product correctness and worktree cleanliness into one verdict.

## 8. Installation and updates

Install only after approval:

```bash
cp -R govern-project-documentation "${CODEX_HOME:-$HOME/.codex}/skills/"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" \
  "${CODEX_HOME:-$HOME/.codex}/skills/govern-project-documentation"
```

After material policy changes:

1. update `SKILL.md` and affected references/assets;
2. regenerate `agents/openai.yaml` if the public interface changed;
3. run static/unit/fixture/integration tests;
4. rerun read-only pilots;
5. publish a new semantic version/tag;
6. synchronize the global agent directive.
