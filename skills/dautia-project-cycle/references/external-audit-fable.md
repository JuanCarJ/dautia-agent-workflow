# External UX audit with Fable

Load this reference only when the user explicitly asks to use Fable in the current turn. Its output is an external opinion, not project truth, and sends context to Anthropic using the user's quota.

- Run from the repository root so the applicable `CLAUDE.md` can adapt canonical contracts.
- Prepare one concrete UX decision, user/platform, essential design context, and one to three captures of the same point. Audit one screen, state, or decision per execution.
- Use Claude Code non-interactively, read-only, without session persistence; block write tools.
- Pass a dynamic prompt with objective, surface, constraints, acceptance criteria, and requested finding format.
- Always set `--max-budget-usd 1.50` and `--max-turns 6`. A higher budget or chained call requires new explicit authorization.
- If scope is larger, reduce it to the highest-uncertainty UX decision.
- Normalize each finding against user intent, canonical docs, actual UI/code, and evidence. A `decision_gate` confirms or rejects findings before they alter a risky plan.

Never invoke Fable merely because a supplied prompt came from Fable, or as a default code, architecture, security, migration, or test auditor.
