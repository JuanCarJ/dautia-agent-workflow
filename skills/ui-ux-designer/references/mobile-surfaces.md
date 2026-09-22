# Mobile surfaces

Use this only for an actual mobile or multiwindow surface where touch, system UI,
posture, connectivity, rotation, or window size can change the experience. Do not
load it for unrelated responsive copy or desktop work.

## What to observe

- Test supported device/window, orientation, text scaling, keyboard, safe areas, overlays, and relevant connection state. Do not assume one-handed use, phone urgency, or tablet leisure.
- Preserve navigation location, selection, input, scroll, and filter state through supported return, rotation, resize, and deep-entry paths such as notifications when they exist.
- Measure interactive hit area and separation, not only the icon. Use current platform criteria and record the unit; a heuristic target is not automatically a conformance threshold.
- Localize loading/progress to affected content when other navigation can safely remain available. Do not invent percentages or announce success before confirmation.
- Keep selection geometry stable. Focus, hover preview, touch selection, persistence, and save/commit are separate states.
- Provide alternatives for drag, meaningful reading order and announcements, scalable content, and user control over timed interaction.
- For commerce, surface material eligibility, coverage, stock uncertainty, fees, and timing before avoidable effort. Follow delivery, help, and recovery instead of stopping at order receipt.

Desktop viewports and captures leave device input, system UI, touch hit testing, and
lifecycle behavior unobserved.

## Sources and limits

- *Diseñando apps para móviles* (2013–2014), physical pp. 91–119, 121–157, 167–190, and 219–227: interaction, states, testing, assets, and tablet recomposition. Its iOS 7/Android 4 and raster-export recipes are historical.
- Samsung, *One UI Design Guidelines*, physical pp. 5–14, 18–56, and 84–92: reach, architecture, localized progress, stable selection, multiwindow, and accessibility. Its dimensions, breakpoints, snap behavior, and component placement are platform examples.
- UXalliance/Usaria, *Delivery Apps en tiempos de COVID-19* (2020), physical pp. 60–94 and 122–162: communication, availability, payment, delivery, and support. It does not prove current provider or market behavior.
- Multiplica, *Claves de la experiencia móvil perfecta* (2015), physical pp. 8–34: commercial heuristics from a narrow historical sample; use as questions, not a feature checklist.
