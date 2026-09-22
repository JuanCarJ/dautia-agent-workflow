---
name: ui-ux-pro-max
description: Search bundled UI design data for palettes, typography, charts and stack guidance when a concrete design decision needs options.
---

# UI/UX Pro Max

Portable design intelligence skill backed by bundled scripts and datasets.

Goal: give Codex a fast searchable design system database so design choices are informed, comparable, and explainable instead of improvised.

## Activation

Use this skill when you need:
- typography options
- palette direction
- style or mood direction
- UX rules and anti-patterns
- chart recommendations
- landing page structure guidance
- stack-specific frontend guidance

Do not use it when:
- the right move is obvious from the existing design system
- the task is a tiny local UI fix that does not need research
- a database lookup would add ceremony without improving the decision

## Bundled resources

Resolve `<skill-root>` as the directory containing this `SKILL.md`. Do not
assume a user home, Codex directory, or operating system path.

Skill definition:
- `SKILL.md`

Scripts:
- `scripts/search.py`
- `scripts/core.py`
- `scripts/design_system.py`

Datasets:
- `data/styles.csv`
- `data/colors.csv`
- `data/typography.csv`
- `data/landing.csv`
- `data/products.csv`
- `data/icons.csv`
- `data/charts.csv`
- `data/ux-guidelines.csv`
- `data/react-performance.csv`
- `data/web-interface.csv`
- `data/prompts.csv`
- `data/ui-reasoning.csv`

## Working Model

This skill should behave like a searchable design reference layer.

Use it to:
- expand the option space
- compare candidates
- support a decision with concrete options
- retrieve stack-aware implementation guidance

Do not let it become a mechanical chooser that overrules:
- explicit user direction
- the existing product system
- the executor's judgment on the actual screen

## Preferred Workflow

### 1. Extract the real question

Identify what is actually needed:
- style direction
- typography
- color
- landing structure
- icons
- charts
- accessibility / UX rules
- stack-specific implementation guidance

### 2. Start broad when the problem is open-ended

For broad design direction, start with the design-system generation flow:

```bash
python3 "<skill-root>/scripts/search.py" "<product type> <industry> <keywords>" --design-system -p "<project name>"
```

Use this when the user needs a coherent recommendation set rather than one isolated lookup.

### 3. Search a domain when the decision is narrow

Use domain-specific search when you already know the axis:

```bash
python3 "<skill-root>/scripts/search.py" "<query>" --domain typography
python3 "<skill-root>/scripts/search.py" "<query>" --domain color
python3 "<skill-root>/scripts/search.py" "<query>" --domain ux
```

### 4. Use stack guidance only when implementation details matter

```bash
python3 "<skill-root>/scripts/search.py" "<query>" --stack react
python3 "<skill-root>/scripts/search.py" "<query>" --stack html-tailwind
```

Do this when:
- coding patterns matter
- performance tradeoffs matter
- stack-specific implementation guidance will change the solution

## Decision Rule

Use the results to compare options, not to obey the top hit blindly.

A good use of this skill produces:
- 2-3 plausible candidates
- a selected option
- a reason the selection fits this product and audience

## Domains

Available domains include:
- `style`
- `prompt`
- `color`
- `chart`
- `landing`
- `product`
- `ux`
- `typography`
- `icons`
- `react`
- `web`

## Stack Guidance

Available stacks include:
- `html-tailwind`
- `react`
- `nextjs`
- `vue`
- `nuxtjs`
- `nuxt-ui`
- `svelte`
- `swiftui`
- `react-native`
- `flutter`
- `shadcn`

## Practical Rule

If the existing design system already answers the question, do not search just to create activity.

If the decision is materially unclear, search.

If the search result conflicts with the product truth seen in the actual UI, trust the product truth.

## Executor Authority

This skill expands options; it does not have the final vote.

Priority order:
1. explicit user instruction
2. product truth and existing system
3. design contract such as `docs/DESIGN.md`
4. executor judgment on the actual interface
5. `ui-ux-pro-max` suggestions

Use the database to support taste, not replace it.
