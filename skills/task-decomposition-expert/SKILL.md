---
name: task-decomposition-expert
description: Decompose a substantial or fuzzy frontend increment into buildable views, shared components, dependencies, interaction/data boundaries, and implementation order. Use only when direct implementation would be ambiguous or risky, or when the user asks for a UI implementation plan. Do not use for ordinary screens, small edits, critique, direct bugs, copy-only work, or backend-only work.
---

# Task Decomposition Expert

Turn a broad frontend request into the smallest buildable sequence that preserves product intent.

## Boundary

- This skill plans; it does not implement, audit visual quality, run QA, create documentation, choose a stack without need, or expand scope.
- `frontend-developer` implements a clear brief.
- `ui-ux-designer` resolves product, hierarchy, interaction, accessibility, or contextual-value questions.
- Existing project architecture and components win over a generic recommendation.
- Do not invoke another skill merely to complete the plan.

## Method

1. Identify the user outcome, affected roles and acceptance criteria.
2. Map only the affected views, states and shared components.
3. Mark data/API/auth dependencies and interaction boundaries.
4. Order work to prove the riskiest dependency early and minimize rework.
5. Split only where a block can be built and validated independently.

Use one execution block when a normal page or feature is already coherent. Split by view, subsystem, state boundary or independently testable dependency, not by arbitrary section count.

## Output

Include only relevant fields:

```text
OUTCOME
- ...

VIEWS / STATES
- ...

SHARED COMPONENTS
- ...

DEPENDENCIES AND DATA
- ...

IMPLEMENTATION ORDER
1. ...

ACCEPTANCE / RISKS
- ...
```

Keep it concise and immediately buildable. Recommend a stack only for a new project or an explicit architecture decision. Do not create a separate planning document unless the user requests it or the repository requires a durable artifact.
