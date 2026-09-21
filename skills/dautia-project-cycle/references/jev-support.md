# Jev decision support · r3

One shared synchronous client, no second supervisor. `scripts/jev_support.py`
implements setup, doctor, synthetic probe and evaluate over packet schema 3.
The r3 plan governs routing; the earlier prototype schema 1 is not silently adopted.

Checkpoints: brief (coverage), impact (known consumers), continuity (decision delta),
route (prepared implementation medium/high or analytical profile), context (optional recoverable evidence), progress
(remaining work/reframe), closeout (claim vs evidence), action (scope/procedure).
Do not call all checkpoints for every message. Mechanical identities, permissions,
exit codes and failed tests need deterministic checks, not another model call.
The classifier is textual; visual evidence is inspected by the proper platform agent.

## Configuration

After installing the candidate:

```sh
dautia-jev setup --mode shadow --store-key
# Alternatively inject TYPESAFE_API_KEY from a secret manager, then:
# dautia-jev setup --mode shadow --from-env
dautia-jev doctor
dautia-jev probe --allow-network
```

Use one key option, not both. No key in arguments, Git, chat or logs. Configuration
lives in XDG_CONFIG_HOME/dautia (default ~/.config/dautia); the optional key file
uses 0600 in a 0700 directory and is not an encrypted keychain. Existing configuration
requires explicit --replace after inspection; no automatic activation/migration of
an old enforce policy. The default without setup is off.

Direct endpoint: `https://api.typesafe.ai/v1/systemone`, Bearer header. Model version
is pinned to `jev-1.13.0`; doctor checks local shape, not server availability. Probe
uses only synthetic content and requires explicit network permission. No SDK needed;
Python 3.11+ standard library. Config carries question_revision, feature allowlist,
request/response sizes, question count, timeout, per-day and per-objective quotas,
cache TTL and per-function confidence thresholds. Initial thresholds are NOT
calibrated. Record policy/model/question versions during evaluation.

Modes: off; shadow (record recommendations, keep the baseline/principal choice); selective (apply only
explicitly enabled route/context features after a successful pilot). `apply_features`
is empty initially. Even selective returns a prepared dispatch target, not an agent
that was spawned. It never changes authorization or certifies a result.

```sh
dautia-jev evaluate route /private/path/packet.json --allow-network --record
```

Data sharing requires an explicit reference in the packet and a sanitized bounded
envelope. Never send raw transcripts, credentials or unrelated provider payloads.
Secret scanning is an extra guard, not a proof that arbitrary text is safe.
Questions return finite enumerated values; validate the answer set, model, types,
probabilities and confidence. Typed does not mean correct. No free-form explanation
is invented. Low confidence/unknown returns to the principal; API failures preserve
Sol coordination and mandatory controls. They do not force human intervention.

Cache stores only typed answers and a hash, scoped to objective/project/packet,
questions, policy and model. Source or scope changes invalidate it. Cache never
refreshes permission or external target identity. It does not remove originals or
negative evidence. Batching is explicit when a request exceeds its configured cap.
Metadata telemetry records recommendation vs selected profile and typed question
results separately; model observed from a worker remains unknown until actual
runtime evidence. No rate/cost/quality claim comes from client latency alone.

Routing r3.2 uses `model-routing.md` and the `dispatch-plan` consumer. The default
implementer is medium; defining a profile or obtaining a recommendation is not
proof that the native client executed it. No live activation is implied.
