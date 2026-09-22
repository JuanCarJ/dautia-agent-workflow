# GPT-6 adoption · 15.1

The approved role matrix and exceptions live in
[model-routing](../skills/dautia-project-cycle/references/model-routing.md) and its
canonical JSON policy. Principal GPT-6 Sol medium; bounded exploration Luna high;
Astra low/medium analytical only; prepared implementation Sol medium/high.
Unknown implementation difficulty requires classification. No added roles, advisor,
hooks, provider changes or product edits. No automatic multihost rollout.

## Preserved installed skills

Several personal skills had evolved beyond this repository. The migration first
reconciles their installed versions: evaluation, UI/UX, frontend, DigitalOcean,
focal surface review, documentation governance and packaging review. The extra
changes centralize model choice and introduce the GPT-6 pilot. Historical v11/v12
case catalogs/results keep their original expectations. Existing documentation,
UI acceptance, environment and deployment guards are not reduced.

## Installation and client compatibility

The installer now derives both root and default-subagent model/effort from the
host profile and canonical policy. Other TOML settings must remain unchanged.
Use repeated `--skill` for selected extra skills, preview conflicts and preserve
local customizations before explicitly adopting reviewed files with a backup.

On the pilot Mac, PATH CLI 0.153.4 rejected GPT-6 Sol for ChatGPT sign-in. The app's
CLI 0.155.0-alpha.16 successfully ran it. This is evidence for these two observed
clients, not a universal minimum-version claim. Check the concrete client on each
host. Repointing an existing launcher is a separate backed-up host operation;
never overwrite its package or modify a live process.

The installer does not remove obsolete agent files. Archive only unchanged,
previously managed definitions no longer in the generated manifest, retaining
original paths, hashes and rollback data. Customized/unmanaged definitions need
individual reconciliation. A remaining higher-effort definition is not authorized
by its presence. Do not claim universal native enforcement.

## Validation and interpretation

- Routing/install tests verify eligibility, unresolved decisions, ceilings,
  exact dispatch, configuration preservation, drift and transactional rollback.
- The GPT-6 replay freezes 20 sanitized cases covering common and unusual flows.
  No providers or products are exercised; real account/model use is attributed.
- Compare 5.6 high versus 6 high first, then 6 medium. Luna/Astra runs here measure
  contract interpretation, not permission to assign them every represented role.
- Strict enum scores and semantic acceptance are different. Preserve original
  failed scores. Amend ambiguous rubrics prospectively and apply equally; do not
  call an equivalent focal-regression label an unsafe model action.
- The artifact pilot fixes camera-selection state and renders K-Means explanations
  in isolated Python/HTML fixtures. It does not prove SwiftUI, rendered visual
  quality, accessibility, physical devices or complete product behavior.
- Forced native dispatch checks exact named roles, fork policy, actual child
  contexts and completed deliveries. It is not autonomous role-selection proof.

No statistical quality or subscription-savings guarantee follows from this small
pilot. Record model, effort, client, contract/candidate hashes, failures, acceptance,
wall time and reported usage. Preserve unknown cost as unknown. Verify actual host
installation and fresh-session loading separately from source validation.

## Official guidance used

- https://learn.chatgpt.com/docs/models
- https://developers.openai.com/codex/agent-configuration/subagents
- https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra

Shared domain skills remain model-neutral. No instructions are selected from a
model's self-identification. Changing models does not automatically change skills;
any future profile-specific prompt delta requires explicit loading and evaluation.
