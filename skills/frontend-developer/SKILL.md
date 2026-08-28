---
name: frontend-developer
description: Use when implementing production-grade frontend code from a design contract, a design brief, or an established product style. Use for React, Next.js, Vue, Nuxt, Svelte, Astro, and plain HTML/CSS when the job is to actually build the interface cleanly rather than just discuss it.
---

# Frontend Developer

Native Codex frontend execution skill.

Goal: turn design direction into production-quality UI without drifting into generic defaults or overengineering.

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

Read only the nearest product and design contracts that affect the requested surface. If `docs/DESIGN.md` exists and is relevant, use it; otherwise infer the established system from the codebase. Do not create a design document, token exercise, or new system merely because one is missing. Record a new durable design decision only when the implementation actually introduces one.

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
3. `docs/DESIGN.md`
4. executor judgment on the implemented UI
5. generic suggestions or defaults

Do not make a screen worse just to remain mechanically faithful to a suggestion.

## What To Extract From The Contract

When `docs/DESIGN.md` exists, pull these first:
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

## Avoid These Failures

- defaulting to bland fonts when the project clearly needs personality
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

## Practical Working Style

- Build first, then tighten.
- Reuse existing product patterns where they are strong.
- Replace weak patterns instead of layering hacks on top.
- If a requirement is ambiguous, choose the most defensible implementation and keep momentum.
- If a user-facing product needs polish, verify in the browser before calling it done.

## Output Standard

A good implementation pass should leave:
- working code
- coherent tokens or styling primitives
- no obvious unfinished UI states
- a result that matches the contract or the inferred system
