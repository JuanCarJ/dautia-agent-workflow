---
name: user-surface-value-review
description: Review a changed user-visible surface when there is a material unresolved question about the contextual value of copy, data, status, controls, or help. Skip invisible changes and broad UX or visual-system audits.
---

# User Surface Value Review

Assess whether affected visible elements help the actual role understand, decide, act, recognize state, or recover. Use this focal lens within existing validation only when that value is unresolved; reuse equivalent UI/UX evidence. A visible change alone does not add a reviewer, phase, or release gate. For a broad page, visual-system or end-to-end UX audit, use `ui-ux-designer` instead. Return `NOT_APPLICABLE` when there is no visible delta.

This skill grants no implementation or release authority. If the request already authorizes implementation, return findings to that loop; otherwise report without editing. Review only added or materially affected copy, labels, values, KPIs, cards, badges, tables, icons, alerts, states, controls, navigation and terminology.

Ground the judgment in accepted intent, the real role and task, changed code, relevant behavior/data/domain contracts, and the rendered surface in affected states and viewports when practical. Documentation alone does not prove the active surface; code alone does not prove hierarchy or clipping. Report an observation gap instead of claiming a visual verdict.

For each disputed element, ask what question it answers, what action or recovery it enables, whether it is needed here or on demand, whether its meaning matches actual behavior, and whether hierarchy, a control, a label or direct feedback would communicate it better. Judge context rather than element count: density can serve a report; a correct metric can distract from checkout. Preserve necessary accessible names and descriptions. Do not invent friendly terminology that changes approved business meaning.

Use `KEEP`, `SIMPLIFY`, `REPOSITION`, `REMOVE`, or `MISSING` only for elements that need discussion; mention useful elements selectively. A misleading value, obscured primary action, unsafe consequence or missing recovery is `MATERIAL_FIX`. Misplaced, ambiguous or overexplained information is `FOCAL_ADJUSTMENT`. Otherwise return `PASS`, `EVIDENCE_GAP`, or `NOT_APPLICABLE` as appropriate. These verdicts are advisory: correct a finding before authorized implementation closeout only when it violates accepted behavior, usability or another existing criterion; otherwise report the residual.

Give the verdict, role/task/surface, evidence, concrete corrections and observable acceptance where needed. A `PASS` or `NOT_APPLICABLE` needs only a short explanation. Do not add copy or components to make a report look complete. Unknown profit from missing costs, for example, must remain unavailable rather than render as zero; useful warnings explain consequence and recovery, while prose that merely narrates clear table headers adds noise.
