# Shared prompting and skill semantics · 15.2

Baseline: 4db2de072e307cd2a6e150240bba49d5336545e5 (GPT-6 routing already installed).
This change edits instructions, not models, effort, policy, runtime gates or tools.

## Applied principles

- Describe the requested outcome, invariants, authority and completion boundary.
  Keep necessary sequences for mutations and evidence; remove repeated generic
  process and fixed report templates where no acceptance criterion requires them.
- Make discovery descriptions concise and discriminating. Examples and detailed
  API/topic lists belong in the selected skill/reference, not every task's catalog.
- Read only pertinent references; existing course/domain references remain intact.
  No extra coordinator, duplicate skill per model, or automatic research/audit phase.
- Continue authorized implementation, correction and validation. An explicit change
  does not require renewed discovery just because its surface is large. Unknown
  product semantics still block the dependent edit.

## Preservation map

| Boundary | Location after edit |
|---|---|
| Authority/modes, exact grants, no automatic permission | AGENTS Objective; each affected domain skill |
| Material preflight, dispatch, closeout commands | cycle entrypoint + r3-prevention |
| Exact qualified native role, isolation, observed receipt | AGENTS Profiles + cycle + unchanged routing |
| Original acceptance, fail-before oracle and reviewed exceptions | AGENTS Quality + unchanged r3-prevention |
| Existing design, broad visual evidence and independent UX | AGENTS Quality + UI/UX/frontend entrypoints |
| Course/OOUX/usability/mobile/voice/TV material | unchanged conditional UI/UX references |
| Canonical docs, scratch slices, spec authority | documentation skill + unchanged evidence-contract |
| Git/review, external identity/readback and recovery | AGENTS Git + CI/CD + project runbooks |
| DB staging only, fixed Supabase wrapper, no Colima | AGENTS Providers; no changed runner or project rules |
| Explicit read-only security review | AGENTS Providers + unchanged role policy |
| Test and evaluation commands, raw negative evidence | evaluation skill; unchanged scripts/catalogs |
| Separate Apple actions and Siigo business-write authority | unchanged domain skill bodies |

The global contract remains explicit because it is shared by Sol, Luna and Astra.
No necessary check, permission or review requirement is removed because one model
might infer it. The reduction concerns repetition and ceremonial shape, not these
boundaries. Apple SwiftUI references remain authoritative for the documented topic,
but their local copy is checked against the actual SDK rather than declared forever current.

## Model-specific guidance and loading

OpenAI's Astra article describes Astra behavior; do not generalize it into a claim
that Sol/Luna no longer need instructions. DautIA uses the same acceptance and domain
skills for all three. Existing generated qualified role definitions select the model;
the task's scope selects relevant skill references. Switching model does not switch
instructions. No new model-conditioned prompt layer or self-identification branch is
introduced without evidence that it improves outcomes.

## Catalog ownership

This release edits the shared core and 18 personal skill entrypoints. Other skills
are retained when already focused or tied to fragile operations; no plugin cache,
SDK export, hidden legacy skill, provider configuration or project contract is reset.
Installed copies newer than this repository are not replaced by stale source. The
installation explicitly selects changed skills rather than using scope all.
This is not a claim that every third-party skill or automatic selection is optimized.

## Evaluation boundary

Compare frozen before/after instructions with the same cases, models and acceptance.
Keep negative results; separate deterministic validation, model decision replays,
actual artifact checks and real project/provider proof. A shorter prompt is an input
size observation, not a measured subscription saving or a causal quality guarantee.
No test expectations or historical catalogs are changed to make the candidate pass.

Sources consulted:
- https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
- System Skill Creator installed on this host (current short, task-specific guidance).

Safety/permission/reduced-verification proposals: none. The existing required
boundaries remain active; no additional approval is inferred for their execution.
