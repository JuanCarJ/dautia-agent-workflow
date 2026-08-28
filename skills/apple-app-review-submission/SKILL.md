---
name: apple-app-review-submission
description: Create or explicitly prepare to create an Apple App Review submission in App Store Connect for a concrete app version and build, including a resubmission after rejection. Use this skill only when the user is going to create that submission request. Do not use it for generic App Review questions, TestFlight or review-status checks, local release audits, isolated What's New or review-note copy, rejection analysis without intent to resubmit, or general release closeout. It preserves the separate authority required for upload, Add for Review, Submit for Review, expedite, and release actions.
---

# Apple App Review Submission

Make the submitted app easy to review while preserving the truth of each release gate. Optimize for a complete, reproducible review path, not for tricks that speculate about reviewer behavior.

## Activation gate

Apply this workflow only when the user is creating, or explicitly preparing to create, an App Review submission in App Store Connect for an identified candidate. A concrete candidate includes at least the app/platform plus the intended version/build, or an active App Store Connect submission whose candidate can be verified.

Do not activate it merely because App Review, TestFlight, release notes, review status, guidelines, rejection text, attachments, or expedited review are mentioned. If the user is only asking a question, auditing readiness, checking provider state, drafting isolated copy, or analyzing a rejection without an intention to resubmit, answer through the narrower applicable workflow instead.

## Establish scope and authority

Identify the app, platform, version, build, environment, submission type, current Apple state, and the exact action the user authorized. Distinguish:

- first submission;
- routine update;
- resubmission after rejection;
- critical bug fix;
- event-timed submission.

Treat preparation, upload, TestFlight distribution, adding an item for review, submitting it, approval, and release as separate actions. Drafting metadata or a checklist does not authorize any external mutation. Stop before upload, attachment upload, `Add for Review`, `Submit for Review`, expedited-review request, or release unless the user expressly authorized that target.

When preparing or creating the real submission, verify Apple requirements from official Apple Developer or App Store Connect sources. Read [references/apple-official-sources.md](references/apple-official-sources.md) for the source map. Project documentation and old submissions are context, not proof of the active Apple requirement or provider state.

## Build a reviewer-sized path

Inspect only the changed and review-relevant surfaces. Fix or report blockers before polishing copy:

1. Confirm the exact build and that it represents the claimed changes.
2. Confirm relevant on-device behavior, stability, live support/privacy URLs, complete metadata, and accessible backend services.
3. Check recurring rule boundaries that actually apply, such as account deletion, login choices, permissions and purpose strings, privacy answers, purchases/subscriptions, UGC safety, regulated functionality, and placeholder or stale content.
4. Provide a working, non-expiring demo account or an approved full-featured demo mode when login is required. Include additional roles, sample data, QR codes, test streams, setup, or authentication instructions only when the reviewer needs them.
5. Make the route deterministic: state where to start, what to tap, what should happen, and any required precondition.

Do not invent a universal script. Prefer the project's existing checks, then add a small deterministic check only for a recurring failure mode that can be verified mechanically.

## Keep the two audiences separate

Prepare two different texts when applicable:

- **What's New:** concise, user-facing changes and benefits. Do not put reviewer instructions, compliance arguments, credentials, internal implementation, or rejection discussion here.
- **App Review Notes:** private, reviewer-facing instructions for non-obvious changes, exact navigation, setup, test accounts or roles, purchases, hardware, location, UGC safeguards, and the reason for any attachment.

For a routine update, notes should usually answer: what changed, where it is, how to exercise it, and what result proves it works. Avoid turning a short deterministic path into a long release narrative.

## Decide whether a video is necessary

Default to **no video**. A video has value only when it materially removes ambiguity that concise notes plus working review access cannot remove.

Mark the video **necessary** when one or more of these conditions apply:

- the flow depends on special hardware or an environment Apple cannot easily reproduce;
- it requires multiple users, roles, devices, location, timing, external events, or a state transition that is difficult to stage reliably;
- it demonstrates a safety or compliance path such as UGC reporting, blocking, moderation, or another non-obvious safeguard;
- Apple requested evidence or a prior rejection shows that written navigation was insufficient;
- the relevant feature is intentionally hidden, conditional, or otherwise hard to discover, and a deterministic demo path alone is inadequate.

Omit the video for routine bug fixes, straightforward UI changes, and flows that a reviewer can reach quickly with the supplied account and notes. Do not suggest an optional recording “just in case”: if the evidence does not justify `necessary`, the decision is `omitted`. Do not attach a video merely to appear trustworthy or to speculate that it will accelerate approval.

If a video is necessary:

- record the submitted build or a faithfully identical review environment;
- show only the shortest complete path and the evidence Apple needs;
- identify the version/build and any setup in the notes;
- keep credentials, personal data, unrelated screens, and internal secrets out of the recording;
- prefer one focused recording over several overlapping attachments;
- re-record stale evidence when UI, data, or the route no longer matches the build.

State the decision as `video: omitted` or `video: necessary`, followed by one sentence of evidence. A plan to record is not proof that the attachment exists, uploaded successfully, or was reviewed.

## Handle expedited review conservatively

Recommend an expedited-review request only for an evidenced critical bug or an imminent event directly associated with the app. Capture the current impact, reproduction steps when applicable, event/date and association when applicable, candidate build, and why the ordinary queue cannot meet the need. Do not use it for impatience, a routine UI change, or an artificial deadline.

Submitting an expedited-review request is an external action and requires explicit authority.

## Produce the submission package

Return a compact package with:

1. **Verdict:** `READY`, `BLOCKED`, or `READY TO PREPARE`.
2. **Candidate:** app, platform, version, build, revision if known, and environment.
3. **Evidence:** changed route, relevant tests/device checks, URLs, backend/access readiness, and unresolved gaps.
4. **What's New:** final user-facing copy, or `not applicable`.
5. **App Review Notes:** final private copy, with sensitive values referenced through an approved secure channel rather than reproduced unnecessarily.
6. **Review access:** demo roles, setup, and expiration/availability status.
7. **Attachment decision:** video `omitted` or `necessary`; other documents may be `omitted`, `optional`, or `necessary`. Include the reason and exact content when an attachment is needed.
8. **Expedite decision:** `not justified`, `candidate`, or `authorized and requested`, with evidence.
9. **External truth and stop:** last verified App Store Connect state and the next action that still needs authority.

Use Apple's current state labels when observed. Never collapse a local archive, upload receipt, processing, TestFlight availability, ready-to-submit state, submission, review, approval, and public release into one claim.
