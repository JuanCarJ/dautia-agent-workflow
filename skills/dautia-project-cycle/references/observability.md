# DautIA observability · r3

Three separate planes: operational context/authority and pending actions; metadata
for evaluation; and a separately authorized sanitized semantic audit sample.
A metadata exporter failure does not block ordinary work. Missing mandatory
permission/evidence still blocks its dependent action. Logs are not authority.

Retain `scripts/dautia_cycle_telemetry.py` as the owner of native session counters,
windows, profile segments, descendant correlation and legacy schemas. This change
does not rewrite that parser or reinterpret its historical output. The new event
stream supplements it with boundary/routing facts. `workflow_cli.py export` can
reference a legacy snapshot hash without copying raw input or re-summing counters.

During the pilot, record the minimal lifecycle/outcome of every substantive eligible
objective, including direct work. No per-command packet or deep snapshot for routine
work. Deep collection remains bounded to incidents, costly waits or explicit audit.
One session can contain multiple objectives; one objective can span sessions/repos.
Use aliases for objective/project/run/repo/checkout and generation, not a branch as
identity. Retain requested, configured and runtime-reported profiles separately.
Absent observed fields remain null; a settings event is not a provider confirmation.

Events include context bound/invalidated, skills selected/load observed, route
evaluated, dispatch requested, agent started/ended, handoff received, validation,
review, scope/spec change, continuation, blocked/reopened and workspace reconciliation.
The schema allowlists small metadata and rejects arbitrary prompts, paths, commands
and tool outputs. The Jev client can record actual typed choices/probabilities and
recommendation vs selected profile. Dispatch performed remains false until the real
harness supplies an observation; no role name or client result invents an agent.

Storage is private JSONL per objective/emitter under XDG_STATE_HOME/dautia (default
~/.local/state/dautia). Each stream uses an advisory file lock; import deduplicates
event IDs and reports conflicting duplicates/unsupported records. Bindings and
cooperative resource leases are separate private SQLite stores. Do not synchronize
an active log or database between hosts. Consolidate closed exports by identities;
receipt time is not causal ordering across unsynchronized machines.

Do not add reasoning-output tokens again to output/total or cached input again to
input. Do not sum cumulative snapshots or both parent totals and their included
children. Keep counter resets, boundary gaps and shared unallocatable root usage
explicit. Credits, processed tokens and monetary billing are not equivalent. Do
not attribute provider capacity failures to workflow/model reasoning quality.

Evaluate acceptance, omitted requirements, escaped regressions, late impacts,
necessary vs avoidable user intervention, use of analytical results and own new
workspace residue. Every rate needs a denominator, cohort, source and unknowns.
Model comparison uses equivalent prior context/candidates and an independent rubric;
Astra is not ground truth. Compare improved workflow without Jev, shadow and selective
use, preserving withheld cases. Never repeat real business mutations to benchmark.

Metrics cannot prove comprehension. Semantic audit needs the authorized original
focal packet/evidence; hashes alone cannot reconstruct it. Keep that private sample
separate from statistical logs. Retention/export is explicit, no raw transcripts,
credentials, connector payloads or hidden reasoning collected by these helpers.
Snapshots/checkpoints report actual verified Git/external truth, not a task_complete
flag. A required external wait uses a real monitor or a clearly paused dependency,
never an invented heartbeat. Closeout separates product, integration, external
outcome and workspace disposition. Backups are under
XDG_CONFIG_HOME/dautia/workflow-backups, matching the installer.

El CLI registra automáticamente metadatos de bind/gate/hooks y las evaluaciones
de Jev; no lee transcripciones completas. DAUTIA_TELEMETRY=off desactiva ese
registro sin conceder permisos ni cambiar los criterios. evaluate --no-record
permite omitir su evento; las brechas de cobertura no se contabilizan como ceros.
