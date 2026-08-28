---
name: user-surface-value-review
description: Use after an implementation changes a user-visible surface, or when reviewing whether copy, KPIs, cards, badges, tables, icons, alerts, help, terminology, or controls add contextual value. Review only the changed surface against the real role, task, domain, behavior, and observable UI. Skip backend-only, infrastructure, data, and refactor work with no visible delta. This is a focal validation lens, not a full redesign, extra workflow phase, mandatory agent, or release gate.
---

# User Surface Value Review

Determine whether each affected visible element earns its place. A datum can be true and a component can be attractive while still being irrelevant. Conversely, a dense report can be excellent when every element supports a real decision.

Apply this file once within the validation of a user-visible implementation. It does not grant implementation or release authority. If the same request already authorizes implementation, return findings to that implementation loop; otherwise report them without editing.

## Scope

Review only elements added or materially affected by the current delta:

- copy, labels, headings and helper text;
- KPIs, cards, badges, tables and summaries;
- icons, alerts, empty/error/success states and confirmations;
- controls, navigation and progressive disclosure;
- visible terminology, values, units and comparisons.

Return `NOT_APPLICABLE` immediately when there is no visible user-facing change. Use `ui-ux-designer` instead for a broad page, visual-system or end-to-end UX audit. Do not automatically run both.

## Evidence

Use the smallest evidence set that proves the result:

1. accepted user intent and the role's real task;
2. changed files or diff;
3. observable rendered surface at affected states and viewports when practical;
4. behavior, data or domain contracts only where they determine visible meaning.

Documentation alone does not prove the active surface. Code alone does not prove hierarchy, clipping or visual noise. If observation is unavailable, state the evidence gap instead of claiming a visual verdict.

## Contextual value test

For each affected element ask:

1. **Role:** Who sees it, and do they understand this concept?
2. **Task:** What are they trying to complete at this moment?
3. **Value:** What question does it answer or what decision, action, state recognition or recovery does it enable?
4. **Timing:** Is it needed now, elsewhere, on demand, or only for accessibility?
5. **Truth:** Does it match actual behavior, calculations and domain meaning?
6. **Expression:** Can hierarchy, a control, a label or direct feedback communicate it better than prose?

Judge by context, not component count:

- Keep a KPI when it answers a business question.
- Keep a badge when the state changes interpretation or next action.
- Keep a table when aligned scanning or comparison is useful.
- Keep copy when it prevents error, explains a non-obvious consequence or enables recovery.
- Keep visually hidden accessibility text when it supplies a necessary accessible name or description.
- Remove or relocate metrics, implementation vocabulary, decoration and explanations that enable no useful response in this context.

Do not invent friendly terminology that changes an approved business meaning. A technical term may be correct for an expert role and wrong for a store operator.

## Decisions

Assign only one decision when an element needs discussion:

- `KEEP` — useful, truthful and appropriately placed.
- `SIMPLIFY` — valuable but overexplained, ambiguous or expressed in system language.
- `REPOSITION` — useful in another hierarchy, moment, role or disclosure level.
- `REMOVE` — adds no demonstrable contextual value.
- `MISSING` — absence creates material ambiguity, error risk or no recovery path.

Do not inventory every correct label. Mention `KEEP` selectively to prove that the review is not rewarding minimalism.

## Severity and closeout

- `MATERIAL_FIX`: misleading data, contradiction with behavior, obscured primary action, unsafe consequence or missing recovery.
- `FOCAL_ADJUSTMENT`: relevant information is overexplained, misplaced, ambiguous or expressed in internal language.
- `PASS`: no material value problem in the changed surface.
- `EVIDENCE_GAP`: the surface or required state could not be observed.
- `NOT_APPLICABLE`: no visible delta.

This verdict is advisory. It blocks nothing by itself. In an authorized implementation, a finding is corrected before closeout only when it violates accepted behavior, usability or another existing acceptance condition; otherwise report it as a residual.

## Output

Keep the response proportional:

```markdown
Verdict: PASS | FOCAL_ADJUSTMENT | MATERIAL_FIX | EVIDENCE_GAP | NOT_APPLICABLE

Context: [role] — [task] — [surface/state]

Keep
- [Only useful examples needed to establish context.]

Change
- [DECISION] Element — evidence — concrete correction.

Acceptance
- [Observable conditions for material or focal findings.]
```

Omit empty sections. If the verdict is `PASS` or `NOT_APPLICABLE`, explain it in one or two sentences and stop. Never add copy, components or findings merely to make the report look complete.

## Calibration examples

- A total-sales KPI in a performance report can support a decision; a total count of internal records in a point-of-sale flow may not.
- Unknown profit caused by missing costs must not render as zero. Show that it is unavailable and provide recovery when the product supports it.
- A paragraph describing table columns is redundant when clear headers and row states already communicate the same truth.
- An operational warning is valuable when it identifies consequence and recovery; an alert that merely narrates implementation state is noise.
