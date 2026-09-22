# Voice and TV surfaces

Use only the section matching an actual voice or TV surface. These patterns do not
justify adding a modality, choosing a provider, or changing product scope.

## Voice

- Preserve goals, entities, constraints, corrections, and negations across turns. Ask only for a material missing or ambiguous value; do not restart after “Boston, not Austin” or drop a pending goal from “both, hotel first.”
- Distinguish heard/transcribed, interpreted, authorized, in progress, and completed. Confirm according to consequence, ambiguity, and what the user can perceive.
- Signal listening, processing, response, cancellation, and exit. Tune pauses to the task, accessibility needs, and current engine instead of historical timeouts.
- Recover differently from silence, audio not understood, understood but unsupported intent, and incorrect entity. Preserve progress and offer only existing alternatives.
- Keep multimodal alternatives coherent without forcing a channel the user cannot use. Separate wake word, recognition, language understanding, speaker identity, and authorization.
- Before recording real voice research, define purpose, consent, access, retention, and minimum necessary capture.

Source: Cathy Pearl, *Designing Voice User Interfaces* (2016), physical pp. 38–91,
129–177, 183–207, and 213–264. Engines, thresholds, timeouts, avatar preferences,
and biometrics are historical or contextual; verify current capabilities.

## TV

- Verify the supported control path: directional movement, confirm, back, and declared alternatives. Focus must be perceptible and move coherently without trapping the user.
- Test from intended viewing distance with long titles and light/dark artwork. Check essential controls against the platform's supported visible area and display configuration.
- Confirm current platform, units, resolution, overscan, and safe-area guidance. Do not copy a fixed grid, font size, spacing scale, or device ranking.
- Treat “lean back” and fewer paths as context-specific; retain needed search, recovery, and accessibility.

Source: Zemoga, *Designing Interactive Experiences for TV Screens* (2022), physical
pp. 3–15. Its “95%” safe-area statement conflicts with its 1920×1080 margin example
(1740×960, about 90.6% by 88.9% per axis). The 24px type and 12-column grid are
examples, not current universal requirements.

A mouse-driven screenshot does not verify remote focus, distance legibility, or the
supported display boundary.
