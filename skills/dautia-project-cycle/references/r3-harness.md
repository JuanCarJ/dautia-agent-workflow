# Native integration coverage · r3

Codex remains the coordinator/runtime; no new fleet daemon, remote transport or
private Desktop socket is introduced. App is the main UI; CLI supports reproducible
local probes. Verify capabilities and hook schemas against the installed version.

The default integration is explicit CLI calls by the principal. The installer also
writes `hooks.r3.candidate.json` outside the active Codex hook path. It is not enabled
or trusted automatically. Smoke-test it in an isolated host workspace, reconcile
existing hook sources and use the runtime's trust interface before activation.

For a bound ROOT session, PreToolUse blocks known material edits when the packet
check fails and rejects unverified effects in a read-only task. Native sandbox and
approvals still authorize tools. This is NOT a general shell-command safety parser,
connected-tool permission system or universal interceptor. Unsupported tools and
unbound objectives are outside this hook's coverage. A child cannot use the parent's
binding; child scope/permissions are supplied at dispatch and require host tests.

Stop can return one bounded continuation for required executable preparation,
reframing or reconciliation. At most two stop interventions are reserved per
binding generation, with no action when stop_hook_active or interrupted/paused.
An external/physical dependency does not produce a fake heartbeat. Interrupt only
marks state and never restarts a turn. PreCompact retains the already-bound private
core, not a raw transcript. Resume retrieves/revalidates the current packet; it does
not assume old authorization is valid for a changed project or target.

The principal must refresh/rebind state at material transitions. A read-only source
hash change is detected from the actual declared file when --cwd or hooks are used;
other repo/provider sources require their own observations. Do not mark a helper
passing as proof the model understood a spec or followed the intended profile.

Acceptance pending on each actual App/CLI host: custom-agent discovery and return,
observed model/effort when exposed, scoped artifact writes without product writes,
pre-tool rejection, stop/interrupt/resume, compaction recovery and no duplicate
supervisor. The local tests exercise function/protocol fixtures, not those live
capabilities. No model API calls are needed for the offline unit suite.
