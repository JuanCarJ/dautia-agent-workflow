---
name: device-interaction
description: Verify an affected mobile-app flow on a real device or simulator when runtime UI, touch behavior, accessibility hierarchy, or platform state cannot be proved by build or unit tests alone. Skip build-only, backend-only, code-review, and non-UI changes.
---

# Device Interaction

Prove the smallest device-visible boundary affected by the change. This is a validation capability, not a mandatory phase, agent, device matrix, or release gate.

## Routing

- Work directly from root when it already owns the implementation and one bounded device flow is sufficient.
- Delegate to `qa_ios` or `qa_android` only when an independent or platform-specific block adds distinct evidence. Never delegate merely because this skill was selected.
- One actor owns a device session. Reuse an existing compatible session instead of starting another.
- Prefer native device/simulator tooling over general computer use. Do not boot or interact with a device when build or pure tests already prove the requested result.

## Frame the check

Fix before interaction:

- candidate revision/build and platform target;
- affected flow, starting state and observable acceptance;
- required device/OS only when the risk depends on it;
- fixtures, account and environment boundaries;
- stop condition and untested residuals.

Test only states invalidated by the current delta. Extra devices, orientations, permissions, lifecycle, performance, memory, localization or deep accessibility require a named risk or explicit gate.

## External mobile providers

Run broad mobile suites with external providers mocked, faked, or disabled. Use the real provider only for the smallest changed capability that cannot be proved by a deterministic double.

Before a device check that can reach an external mobile SDK, record each relevant provider as `mock`, `disabled`, `staging`, or `live`. A `live` smoke needs the exact capability, candidate revision/build, target device, expected maximum operations, quota or cost protection, and an immediate stop when calls exceed that expectation. Reuse direct-provider evidence when the adapter, configuration, credential, and capability contract remain valid; do not repeat it for unrelated UI or product corrections.

For Google Navigation, a sufficient real smoke normally initializes the SDK, performs one `setDestinations`, and starts/stops or minimizes/reopens that same navigation session without requesting another route. Exercise language, menus, layout, Dynamic Type, permissions, lifecycle, arrival, errors, retries, and other regression states with a deterministic provider unless that state is the changed integration boundary. Apply the same focal principle to Apple/Google sign-in, APNs, StoreKit, maps, analytics, and other mobile SDKs.

Do not reinterpret this rule as changing database tests against verified Supabase `staging` or Vercel validation/release flows; those keep their existing project contracts.

## Session and evidence

1. Start a workspace-backed session for an app being built, or a normal session only for an already-installed app. Reuse it for the objective.
2. Install/run the current candidate once. Repeat only after a code/build change that can affect runtime behavior.
3. Capture hierarchy and a representative image at the initial state. Prefer accessibility identifiers and hierarchy hit points over guessed coordinates.
4. Interact through the accepted flow. Batch stable actions when their intermediate states are not evidence. Recapture after a meaningful navigation, modal/state transition, unexpected result, or final acceptance state—not after every tap or keystroke.
5. Retry an ambiguous launch or interaction once after refreshing hierarchy. If it still fails, classify and report it instead of looping.
6. End the session when the relevant checks finish; open sessions consume resources.

Use full-size images only when hierarchy or a normal screenshot cannot resolve a visual question. Keep binary payloads out of root context: return concise findings and stable artifact paths, expanding only the failing state.

Read [interaction-syntax.md](references/interaction-syntax.md) only when raw coordinate, keyboard, gesture, orientation, or hardware-button commands are needed.

## Verdict

Distinguish:

- product defect: wrong behavior, crash, missing state or unusable control;
- visual/accessibility defect: clipping, overlap, unreadable content, missing accessible target or incorrect focus/order;
- environment/tooling failure: install, simulator, signing, fixture or session problem;
- transient state: animation/loading that resolves after one bounded refresh.

Return candidate, target, flow, result, minimal evidence, untested boundaries and residuals. A successful build does not prove device behavior; a screenshot alone does not prove interaction.
