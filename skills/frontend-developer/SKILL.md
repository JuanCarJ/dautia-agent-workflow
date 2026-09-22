---
name: frontend-developer
description: Use when implementing production-grade frontend code from a design contract, a design brief, or an established product style. Use for React, Next.js, Vue, Nuxt, Svelte, Astro, and plain HTML/CSS when the job is to actually build the interface cleanly rather than just discuss it.
---

# Frontend Developer

Native Codex frontend execution skill.

Focused creative-workflow update: 2026-09-10.

Goal: turn design direction into production-quality UI without drifting into generic defaults or overengineering.

When the requested delta is explicit and authorized, implement and verify it directly.
Do not reopen discovery, research, or a preliminary UX audit because the change is
large. This includes broad migrations with resolved contracts. Use deeper design
methods only for material decisions that remain open, while preserving the existing
product-code review and integration contract. An explicit typography, palette, or
layout change is the decision to execute; preserve the rest of the accepted visual
scope and accessibility rather than debating that preference again.

Use the accepted visual source for the current surface as the default reference,
whether it is a design file, rendered product, screenshot, prototype, or documented
contract. A focused change preserves the remaining composition, tokens, assets,
components, states, and behavior. A broad scope allows justified alternatives to be
evaluated, but does not itself authorize a redesign or require discovery when the
target is already defined.

Classify the visual request before acting: focused delta; new surface within an
established system; broad improvement without redesign; new identity or authorized
redesign; or audit. A brief written by the agent may organize implementation, but
it does not replace the user's original request, turn an agent concept into a user
requirement, or silently lower the intended ambition. Focused deltas execute
directly. New surfaces extend the current system. Broad improvements raise quality
inside the accepted identity. Only a new identity, authorized redesign, or another
materially open creative direction warrants establishing a new visual direction.

## Activation

Use this skill when the task is to:
- implement or finish a frontend
- translate a design brief into code
- build a new page or component inside an existing design system
- refactor a UI while preserving product behavior

Do not use it for:
- pure design critique without code changes
- backend-only work
- tiny CSS nits that do not need an execution lens

## First Step

Read only the nearest product and design contracts that affect the requested surface.
Identify the accepted visual source even when no `docs/DESIGN.md` exists; inspect the
actual surface and representative neighboring states when they carry the established
design. If `docs/DESIGN.md` exists and is relevant, use it together with that evidence;
otherwise infer the established system from accepted visuals and code. Preserve the
authorized delta and the contracts, assets, composition, states, and behavior outside
it.

Do not create a design document, token exercise, or new system for a
micromodification with no durable decision. For a substantive implementation that
lacks a usable design source, capture the minimum source needed to preserve the
accepted design and delta. Follow
[documentar el diseño](../dautia-project-cycle/references/continuity.md#documentar-el-diseno):
the author updates the existing canonical source when implementation changes a durable
decision, and the independent reviewer checks that source against the candidate.

## Executor Authority

Use the contract and references as guidance, but keep final authority over local implementation decisions.

That includes:
- exact button hierarchy
- CTA wording and microcopy
- spacing adjustments needed for a real viewport
- whether a suggested pattern should be simplified or discarded
- whether a component needs more or less emphasis than initially planned

Priority order:
1. explicit user instruction
2. product truth and functional constraints
3. accepted visual source and authorized delta
4. relevant canonical design contract, including `docs/DESIGN.md` when present
5. established product patterns and executor judgment on the implemented UI
6. generic suggestions or defaults

Do not make a screen worse just to remain mechanically faithful to a suggestion.

## What To Extract From The Contract

The numeric scales below are optional: use them only if the accepted project design contract defines them. Do not invent values, create a design document, or replace established tokens to satisfy this skill. When a relevant `docs/DESIGN.md` exists, extract only its actual constraints:
- `DESIGN_VARIANCE`
- `MOTION_INTENSITY`
- `VISUAL_DENSITY`
- palette and token names
- typography and size scale
- spacing tokens
- stack and styling approach
- component specs in `docs/research/components/` if present

## Execution Rules

### Layout

Drive layout from `DESIGN_VARIANCE`:
- `1-3`: conventional, centered, grid-aligned
- `4-7`: asymmetric splits, staggered sections, controlled broken-grid moments
- `8-10`: bolder asymmetry, bleeding type, more aggressive composition

### Motion

Drive motion from `MOTION_INTENSITY`:
- `1-3`: CSS states and small entrances
- `4-6`: richer entrances, reveals, and interaction transitions
- `7-10`: more advanced scroll or choreography where justified

Rules:
- prefer one primary motion system, not several
- animate mostly transform and opacity
- respect `prefers-reduced-motion`
- use motion to reinforce hierarchy, not decorate aimlessly

### Density

Drive spacing and width from `VISUAL_DENSITY`:
- `1-3`: spacious sections, narrower reading widths
- `4-7`: balanced density
- `8-10`: compact spacing, denser information surfaces

## Non-Negotiables

- Use semantic HTML.
- Use tokens or theme primitives instead of scattered hardcoded values.
- Make desktop, tablet, and mobile intentional.
- Use `clamp()` for meaningful type scales when appropriate.
- Keep paragraphs readable.
- All meaningful images need alt text.
- Below-the-fold media should usually lazy-load.
- No placeholder identity, lorem ipsum, TODO UI, or fake polish.
- Include loading, empty, and error states when the feature needs them.
- Keep accessibility basics intact: focus states, contrast, keyboard reachability, landmarks where relevant.

## Functional Relevance

Build for the role, task, domain, and implemented behavior rather than for a component checklist.

- A KPI belongs when it answers a business question in the current context.
- A badge belongs when the state changes interpretation or the next action.
- A table belongs when aligned comparison or scanning is useful.
- An icon belongs when it improves recognition or compact action use.
- Copy belongs when it prevents a material error, explains a non-obvious consequence or state, or enables recovery.

These patterns are not required or forbidden globally. Omit information that cannot justify what the user can understand, decide, or do with it. Prefer hierarchy, labels, affordances, and direct feedback over prose that narrates the interface. Translate implementation concepts into domain language only when translation is accurate; do not invent business terminology or hide a real unresolved product decision.

For a new identity or open creative brief, implement a distinctive composition
and professional finish appropriate to the original request; generic defaults are
not sufficient merely because technical checks pass. Preserve established identity
for focused changes. Choose motion, generated imagery or 3D only for a concrete
visual or interaction benefit, with accessibility and performance appropriate to
the surface; none is a mandatory effect or dependency.

## Avoid These Failures

- using typography that conflicts with the accepted identity, reading conditions, or explicit visual direction
- generic card-grid SaaS layouts as the answer to every problem
- hardcoded random colors across components
- `transition: all`
- overusing shadows, pills, and decorative chrome
- shipping only the happy path

## Stack Guidance

- Respect the existing stack on redesigns and in ongoing products unless migration is explicitly requested.
- For Tailwind, push tokens into theme primitives instead of inline chaos.
- For CSS Modules, SCSS, or vanilla CSS, centralize tokens in globals.
- For React/Next, keep heavy animation libs scoped and lazy where sensible.
- For Astro or static work, do not pull in React without a real reason.

## Component Specs

If `docs/research/components/*.spec.md` exists, treat each spec as executable design intent:
- implement the stated interaction model
- preserve listed states
- preserve responsive behavior
- preserve dependencies and content assumptions

## Shared System Evolution

When a change expands, breaks, migrates, or retires a component or token family used
by more than one consumer, read [design-system evolution](references/design-system-evolution.md).
Skip it for a local implementation that preserves the shared contract. Similar
infrastructure does not by itself justify shared brand, copy, business rules, or a
new package.

## Material Visual Refinement

When an implemented frontend needs material refinement beyond the requested local
edit, read [visual refinement](references/visual-refinement.md). Apply it inside the
same implementation and review contract; it is neither a new phase nor a reason to
add an auditor. Skip it for a micromodification whose visual effect is already clear
and locally verifiable.

## Practical Working Style

When material creative choices remain open for a new surface, a broad visual
improvement, or an authorized new identity/redesign, read
[visual direction](references/visual-direction.md). Skip it when the accepted
system and requested delta already resolve the implementation. Choose technology,
fonts, and asset types after the direction is clear; convenience alone is not a
design rationale.

- Build first, then tighten.
- Reuse existing product patterns where they are strong.
- Replace weak patterns instead of layering hacks on top.
- Resolve reversible layout details using the existing design contract. Do not invent business semantics (pricing, eligibility, permissions, taxonomy, counts); return that specific decision to the root and continue independent work.
- Before implementing an audit, retain accepted states, reference visuals, assets and permitted delta. A suggested component or width is a proposal, not authority to replace the product style. Compare the actual candidate in equivalent states/viewports.
- Inspect one representative composition with real content early when a pattern will be repeated. This is not routine user approval or a required set of variants; resolve reversible details and ask only about choices that materially change the result.
- If a user-facing product needs polish, verify in the browser before calling it done.

## Output Standard

A good implementation pass should leave:
- working code
- coherent tokens or styling primitives
- no obvious unfinished UI states
- a result that matches the contract or the inferred system
- separate evidence for functional acceptance, professional finish, and fidelity to the ambition of the original request
