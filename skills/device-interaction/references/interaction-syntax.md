# Device interaction command reference

Read this file only when the verification needs raw synthesized input. Use the current native tool schema as authority if it differs from these examples.

## Coordinates and hierarchy

Prefer the hierarchy `hitPoint` for taps. Activate the annotated `activationBundleId` first when an element belongs to another visible application. Estimate from a screenshot only after the hierarchy target fails once or is a remote placeholder.

## Common commands

| Command | Meaning |
| --- | --- |
| `t x y [duration]` | Tap or press at a point |
| `d x y` | Double tap |
| `t x1 y1 f x2 y2 [duration]` | Swipe |
| `drag x1 y1 x2 y2 [hold] [move]` | Drag and drop |
| `sender keyboard kbd <text>` | Type text; keep it last in a chain |
| `orientation portrait` | Change orientation; other supported orientations follow the tool schema |
| `b h`, `b p`, `b u`, `b d` | Home, power, volume up or volume down |
| `w duration` | Short device-side wait when state evidence requires it |

Use Unicode escapes such as `\u{000A}` for Return and `\u{0009}` for Tab when supported. Multi-touch and watch controls should follow the live tool schema rather than copied examples.

## Efficient observation

- Capture without interaction to establish the initial hierarchy.
- Refresh after navigation, a substantial state transition, a failed target, or the final state.
- Do not refresh after each character, harmless tap, or intermediate action whose state is not part of acceptance.
- If loading is visible, perform one bounded refresh. Report persistent loading rather than polling indefinitely.
