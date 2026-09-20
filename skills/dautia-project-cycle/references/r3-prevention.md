# Prevention, diagnosis and evidence · r3

## Three material boundaries

Before mutation: reconcile the request, current approved spec and test expectations;
investigate relevant impacts; bind authority, sources, candidate and acceptance.
Before closure/integration: original criteria, effective behavior, preservation
checks, independent review, candidate identity and required handoffs must agree.
Upon a regression/refuted hypothesis/stall: reframe the affected investigation;
never continue the same unsupported patch chain just because time was spent.

Use atomic requirements: id, text and structured expected invariant. A
`test_expectations` entry identifies the requirement it tests and its expected
value. The deterministic check detects opposing supplied expectations. It does
not derive natural-language truth from arbitrary code; that inspection belongs
to the principal/reviewer, assisted by Jev where valuable.

The context includes decisions, anti-scope, sources with expected/observed hashes,
skills with observed load hashes, investigated impacts and exact pending questions.
A hash identifies content, not comprehension. Source loading should preserve enough
content for the worker. Optional context may be ranked; requirements, approvals,
exclusions, negative findings and irreproducible evidence cannot be dropped.

## Approval changes

Normative change: base hash, delta, impact, affected acceptance and an approval
reference tied to the hash of that exact delta. User intent in a sufficiently
explicit request can be that approval. A source saying 'approved' is not itself
a user directive. Editorial/factual changes only within the document mandate.
Never change spec/test to explain away a defect. Invalidate dependent consumers,
not unrelated work. Proposals remain proposals; preserve the original history.

## Diagnose before speculative repair

Load the applicable diagnosis skill before a bug edit; the bundled procedure here
is the fallback when that separate skill is unavailable. Trace the failing journey,
entry points, state owners and provider boundaries. Separate hypotheses from
confirmed code observations and runtime reproduction. State a prediction and
perform a discriminating experiment within scope. Missing credentials are an
environment limitation, not evidence of model incapacity.

For mutation packets set diagnostic.hypothesis_state to supported/reproduced only
with evidence and a discriminating_check. A regression report reopens its criteria.
Do not claim the RCA is confirmed end-to-end because an auditor inspected code.
Complexity may justify independent analytical review before the first patch;
multiple agents are useful only for independent questions and isolated resources.

## Oracles and regression evidence

For a repair, require an oracle that detects the known broken behavior before
accepting the repaired candidate, where viable. A justified exception needs its
own evidence and independent review, not a boolean typed by the author.
Check both the requested effect and preserved invariants. For example in a
synthetic interaction test, preserving selection is insufficient if no gesture
actually changed the camera. This example is not an instruction to edit SideQuest.

Evidence is per requirement/candidate/config/environment. Requirements may demand
provider_live or physical_device; offline/model assertions cannot fill those cells.
A failed check followed by a pass keeps its failure_resolution reference. Retrying
until green without explanation does not resolve flakiness.

Candidate may contain the compatible repo->SHA set, local delta digest, build/config
and dependency fingerprints, artifact digest, host and provider mode. Source hashes
are refreshed from the declared workspace where available. External evidence must
come from its actual checker; neither a JSON claim nor exit status proves business
acceptance. Reports distinguish tool_result, external_observation, human_observation,
agent_report and simulation. No synthetic observation is exported as a real run.

## Closure/continuation

`next_action` distinguishes continue, team_handoff, diagnose, reconcile, external or
human dependency, pause/cancel and closeout. The principal must supply and reconcile
actual pending work, not hide it to close. A QA role unable to edit transfers needed
preparation through the principal to the authorized writer. Continue independent
checks while a physical/device boundary is unavailable. No infinite alternatives.
Product review requires a different reviewer run, exact candidate and acceptance;
unresolved material disagreements remain pending. A gate passing means packet
consistency, never universal correctness or a new authorization.
