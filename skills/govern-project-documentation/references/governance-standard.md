# Documentation Governance Standard

## Contents

1. Allocation by topology
2. Canonical document set
3. Traceability
4. Multi-repo releases
5. Enforcement
6. Sensitive sources
7. Mixed lifecycle and document-first initiatives

## 1. Allocation by topology

| Concern | Single-repo | Monorepo | Multi-repo |
| --- | --- | --- | --- |
| Business/product | repo root | monorepo root | governance repo |
| System architecture | repo root | monorepo root | governance repo |
| Internal architecture | repo docs | subtree docs | technical repo |
| Gitflow/CI/deploy | repo | repo/subtree as needed | each technical repo |
| Current product state | repo | monorepo root | governance repo |
| Local release evidence | repo | owning subtree/repo root | technical repo |
| Composite release | not required | optional | governance repo |

An unversioned workspace directory is never normative.

## 2. Canonical document set

Governance or monorepo root:

```text
AGENTS.md
workspace.yaml
docs/README.md
docs/CURRENT.md
docs/business/
docs/product/requirements.md
docs/architecture/overview.md
docs/architecture/adr/
docs/delivery/roadmap.md
docs/quality/traceability.md
docs/releases/
docs/sources/manifest.yaml
```

Technical repo:

```text
AGENTS.md
docs/project-contract.md
docs/architecture.md
docs/gitflow.md
docs/testing.md
docs/runbooks/
docs/releases/
```

## 3. Traceability

Recommended IDs:

- `BO-###`: business objective
- `BR-###`: business rule
- `RF-###`: functional requirement
- `RNF-###`: non-functional requirement
- `ADR-####`: architecture decision
- `INC-###`: increment
- `BUG/PF/MEJ-###`: finding
- `TEST-###`: validation
- `REL-YYYYMMDD-##`: release

Required columns:

| Requirement | Objective/rule | Status | ADR | Increment/finding | Repos | PR/commits | Tests | Environment | Release | Reviewed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 4. Multi-repo releases

Maintain:

- `workspace.yaml`: repo identity, role, path, base branch, allowed flows, deployment mapping.
- `workspace.lock.yaml`: approved/observed SHA per repo for a cut.
- release manifest: SHAs, migrations, tests, deployments, residuals, rollback.

The governance repo tracks coordination; it does not replace repo-local release evidence.

## 5. Enforcement

Written policy should be paired with:

- branch source/target validation;
- required checks and protected branches;
- Markdown link validation;
- traceability ID validation;
- secret and sensitive-source scan;
- generated-artifact ignore coverage;
- recursive repo status at close;
- deploy record bound to a commit SHA.

## 6. Sensitive sources

Choose deliberately:

1. private Git with LFS and access control; or
2. external private storage plus a versioned manifest.

The manifest records logical name, owner, classification, version/date, checksum, access location, and consumers. Never leave sensitive sources simply untracked but eligible for `git add .`.

## 7. Mixed lifecycle and document-first initiatives

A project can contain productive systems and future initiatives simultaneously. Keep them separate:

| Track | Example state | Documentation authority |
| --- | --- | --- |
| Current operation | operational/production | As-Is, runbooks, releases, current architecture |
| Future initiative | discovery/design/approved | To-Be functional spec, planned architecture, ADRs, risks, acceptance |
| Implementation | implementation/staging | technical repo + pinned governance contract |

Use an initiative manifest to map existing canonical artifacts rather than duplicating them. The manifest includes lifecycle, canonical files, source evidence, target repos, open decisions, blockers, and entry criteria.

Do not label a future demo `production` because its landing or supporting automation is already productive. Conversely, do not treat productive support systems as merely planned because the future platform is still in design.
