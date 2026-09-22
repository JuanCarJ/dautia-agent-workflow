# Usability and forms

Use this for open decisions in forms, filters, validation, destructive actions, or
recovery. For an explicit field, copy, or approved recovery change, implement and
verify the delta without starting a new heuristic audit.

## Interaction questions

- Define task success and, when observed, errors, assistance, effort, abandonment, and recovery. Heuristic inspection does not measure user satisfaction.
- Preserve labels or equivalent accessible names, required state, meaningful grouping, and logical reading/focus order. Spacing should distinguish label-to-field from field-to-next-group.
- Choose radio, checkbox, select, autocomplete, or another control from cardinality, option length, frequency, visibility, and saved-state semantics. Do not use fixed rules such as “more than two means dropdown.”
- Validate when correction is useful without interrupting every keystroke. Retain entered values, identify the affected field/group, and provide a safe next action.
- Match confirmation and reversibility to consequence. Do not invent undo for a settled operation or confirmation for every harmless action.
- Distinguish first-use empty state, filtered zero results, insufficient permission, loading, and error. Filtered emptiness must retain a way to change or clear filters.
- Use multiple steps only when stages or dependencies improve the task; allow return and editing without false progress or data loss.

Evidence should exercise the relevant input methods and actual stored behavior,
including error and recovery. Fewer fields or lines of code do not prove equivalent
semantics or accessibility.

## Sources and limits

- *Semana 3 Usabilidad y Principios*, physical pp. 8–10, 13–22, and 34–44: effectiveness, efficiency, heuristic questions, forms, errors, and recovery. Fixed recipes for option counts, defaults, and button position are contextual examples.
- Steve Schoger and Adam Wathan, *Refactoring UI*, physical pp. 48–53, 96–99, and 234–236: redundant labels outside forms, grouping through spacing, and empty states. The label-removal example excludes forms; do not remove accessible names.
- Brayan Yin Lin, *Atomic Design* course material, physical pp. 4–5: extraction can reduce repetition, but the before/after does not prove label association, validation, focus, or errors survived. The material applies the method originated by Brad Frost.

Use current platform accessibility requirements when exact thresholds matter.
