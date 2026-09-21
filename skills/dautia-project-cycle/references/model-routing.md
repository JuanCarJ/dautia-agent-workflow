# Execution profiles · routing r3.2

Canonical policy: `../config/routing-policy.json`. The principal remains
`gpt-5.6-sol/high`. The configured `implementer` default is `gpt-5.6-sol/medium`;
other canonical defaults are unchanged by this correction. A default is not a
quality benchmark or a universal requirement imposed by the adapter generator.
Skills and role methods retain the same authority, procedures and acceptance.

## Prepared implementation versus analysis

For `implementer`, `implementer_complex` and `systems_implementer` writing product
or tests, supply `work.decisions_resolved: true` from the actual bounded handoff.
False or absent readiness returns a preparation block, not an effort escalation.
Also characterize `work.execution_difficulty` as `routine`, `demanding` or `unknown`:

- Routine, defined implementation can use Sol medium or high. The implementer
  baseline is medium. Jev can recommend high when the supplied task warrants it.
- Demanding execution uses high without an automatic downgrade. An explicit user
  profile exception still requires a usable target and never overrides authority.
- Unknown difficulty uses high as fallback while Jev may assess medium/high. It
  does not imply unresolved product decisions can be delegated to a writer.

Jev's `route` questions distinguish available information, open decisions,
execution/analysis depth and contradictions. Implementation recommendations are
medium/high only. If new product/architecture decisions or conflicts appear,
return the analysis to the principal; do not convert the writer to Astra.
Missing tools, credentials or evidence are not deficiencies of model intelligence.

Analytical roles can use Sol high, Astra low or Astra medium. Astra never writes
product or performs external operations under this policy. A substantive analytical
question can merit Astra from the outset, not only after failures. No routing by
role name, file count, brand or sensitivity alone. The mapping remains uncalibrated.

## Default, principal selection and user exception

`runtime.principal_choice = {"profile": "astra_medium", "evidence_refs": ["..."]}`
allows the principal to select an ordinary eligible profile with evidence, including
when Jev is off or shadow. This is not a user approval and grants no permissions.
Sol xhigh requires the separate `runtime.explicit_override` bound to a user
directive. Astra high is above the current workflow ceiling and remains blocked
even when a legacy definition exists. Availability, denied profiles,
capabilities and budget are checked before any external routing call. Missing
availability remains unverified; no fabricated fallback profile is run.

Off uses the differentiated baseline or a permitted explicit selection. Shadow
observes but does not apply Jev's recommendation or add a semantic blocker.
Selective applies `route` only when that feature is enabled and local gates pass.
Low confidence/API failure preserves the baseline. A selective missing-information
or open-decision result returns preparation rather than another speculative patch.
No setup, network permission or live mode is enabled by this code change.

## Generate, prepare, dispatch, observe

The generator validates each host's configured role default against eligible
profiles instead of requiring all roles to be high. It derives a canonical name
and qualified `ROLE__PROFILE` definitions from one role body. Profiles excluded
from a role are not generated; no Astra writer definitions exist. These are
configuration variants, not additional running agents or a new supervisor.

For a material worker use the installed launcher:

```sh
dautia-workflow dispatch-plan PACKET --agents-dir CODEX_HOME/agents --cwd WORKSPACE
# Add --allow-network only with the existing Jev and data-sharing authority.
```

Use real paths. The packet's `runtime.available_targets` must describe names
actually loaded in the host, not only files found on disk. The command checks the
packet, chooses the profile, binds the decision to context/policy, and reads the
exact generated TOML to verify name, model, effort and sandbox. It returns a
prepared `agent_type`. The principal must invoke that exact native worker with
the same bounded handoff, not the canonical role or a different effort argument.
Regenerate/reload profiles before using new names. Parent config can otherwise
change native permissions; the local check is not proof of runtime enforcement.

`workflow_dispatch.dispatch_prepared` is the callable consumer for a supported
host's spawn API. It revalidates the plan before making one callback and separates
requested/configured/reported values, child start and delivery. Unknown spawn
outcomes require reconciliation, never an automatic retry. No provider report is
inferred from a configured model. A returned mismatch remains a mismatch.
The dispatch ledger uses a stable identity derived from objective/block/attempt,
packet context, policy, definition and selected profile; variable evaluation
timing is audit metadata and cannot create a second child for the same work. A
successful reservation exposes its `dispatch_id` for delivery readback.

The standalone CLI cannot call a tool in its parent Codex thread. The native
principal/tool binding still requires a host smoke; a JSON plan does not prove a
spawn. No shell proxy, private socket, unconditional spawn hook or new agent runtime
is introduced. Cursor continues to inherit its model selector; no parity claim.

Independent review and acceptance remain unchanged. Evaluate the policy using
comparable tasks and total accepted-objective effort, not unit-test counts or
Astra's opinion as ground truth. Historical r3.1 evidence stays historical.
