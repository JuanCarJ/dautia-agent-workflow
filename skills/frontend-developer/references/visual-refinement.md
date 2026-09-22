# Visual refinement

Read this reference only when a frontend implementation needs material visual
refinement. Refinement finishes the accepted design; it does not conceal a redesign,
expand the authorized delta, or change business meaning.

## Preserve the visual contract

Start from the accepted visual source for the same product surface. It may be a
design file, documented contract, screenshot, prototype, or a verified rendered
state. `docs/DESIGN.md` is useful when present, but its absence does not lower the
priority of existing visual evidence. Keep the accepted composition, assets,
interaction model, responsive intent, states, and product semantics outside the
requested delta.

Compare the candidate with the reference on the same surface, state, content, and
viewport. If an exact match is impossible, make the difference explicit before using
the comparison as evidence. Do not turn a generic recommendation into permission to
replace the product's established style.

## Diagnose before changing

Classify each visible drift at the narrowest level that explains it:

- **Missing token:** a reusable visual value is absent from the established system.
- **Incorrect component:** a local implementation bypasses the shared component or
  product pattern that owns the behavior and states.
- **Conceptual mismatch:** hierarchy, flow, terminology, or interaction differs from
  the accepted product model and cannot be repaired as surface styling alone.
- **Local defect:** one implementation is incomplete, inconsistent, or broken while
  the surrounding system remains sound.

Fix a missing token at the system boundary only when reuse is demonstrated. Replace
an incorrect component through its established contract. Return a conceptual
mismatch as an unresolved product or design decision rather than hiding a redesign
inside polish. Correct a local defect locally. Preserve accessibility and recovery
behavior in every case.

## Refine the implemented path

Inspect the rendered experience, not only source code or automated detector output.
Use optical alignment as well as numeric alignment for type, icons, controls, and
grouped content. Keep typography consistent for the same role, and exercise long and
localized content, wrapping, browser zoom, and font loading where those conditions
can affect the surface.

Cover the states the implemented path can actually reach, such as loading, empty,
error, success, disabled, focus, active, slow, offline, missing content, or restricted
permission. Choose the pertinent set from product behavior instead of forcing every
state onto every component. Check keyboard, pointer, and touch behavior where each
input applies, including visible focus, logical order, useful names, and adequate hit
targets.

Choose verification from the actual runtime: a mobile viewport may be a web page,
not a native app. Do not require an installed build or native-device tooling without
evidence that the affected surface uses that platform.

Group related checks so one run can exercise coherent surfaces, states, and
viewports. Select the breadth from the accepted scope and observed risk. Do not impose
an arbitrary test-count ceiling that knowingly leaves visible defects, broken states,
or affected viewports unverified. Automated checks support the result; inspect the
actual candidate and finish the complete affected path.

Update the existing canonical design source when implementation changes a durable
decision, following
[documentar el diseño](../../dautia-project-cycle/references/continuity.md#documentar-el-diseno).
Do not create documentation for a local adjustment with no durable decision. When a
substantive surface has no usable source, record only the minimum reference needed to
preserve its accepted design and authorized changes. The author updates that source;
the independent reviewer verifies its coherence with the final candidate.

## Source and boundary

This guidance selectively adapts the causal classification and whole-path checks from
[Impeccable's `polish.md`](https://github.com/pbakaus/impeccable/blob/main/skill/reference/polish.md).
It does not adopt the Impeccable package, CLI, hooks, installation or initialization
workflow, and it does not establish universal aesthetic rules.
