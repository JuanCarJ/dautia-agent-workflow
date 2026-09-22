# Visual composition

Use this when hierarchy, typography, imagery, color, or layout needs material
judgment. Apply explicit authorized visual changes; otherwise preserve accepted
identity and assets. System fonts, native controls, restraint, and dense layouts are
valid when they fit the product and task.

## Decision lenses

- Before enlarging an element, inspect competition, weight, contrast, grouping, and what can be de-emphasized without becoming illegible or appearing disabled.
- Choose semantic elements for meaning and style their visual rank separately. Heading tags are not a size scale.
- Allocate width from content and relationships. Fixed, fluid, and max-width parts may coexist; test intermediate widths, zoom, long content, and translation instead of imposing a 12/8/4 grid.
- Set type scale, measure, line height, and tracking from the actual font/content. A manual scale can be coherent; prose-length heuristics do not govern tables or identifiers.
- Use spacing, background, border, shadow, and overlap as alternatives for separation. Elevation does not replace focus or modal behavior.
- Measure actual foreground/background pairs and supplement color where needed. HSL lightness and perceived-brightness shortcuts are not WCAG contrast.
- Test intended images at real crops and viewports. Overlays do not alone prove contrast; informative images still need an accessible alternative.
- Add icons, accents, selectable cards, or decoration only when they aid recognition, hierarchy, state, or action. “Boring” is not an observable defect.

## Sources and limits

- Steve Schoger and Adam Wathan, *Refactoring UI*, physical pp. 20–27, 36–62, 66–99, 102–168, 172–217, and 220–246: hierarchy, density, responsive width, type, color, depth, images, and polish. Treat numbers and style preferences as heuristics. Its p.162 “18px” shortcut and p.153 brightness formula are not WCAG definitions.
- *Semana 4 - Diseño UI*, physical pp. 13–18, 21–32, and 34–54: grids, type, Gestalt, color, contrast, and systems. Grid counts, modular scales, color quotas, tinted grays, and fixed ramps are examples.
- Current [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) classifies large text as 18pt regular or 14pt bold, not 18 CSS px generally. Measure computed colors and the applicable criterion.

A screenshot can support hierarchy or crop observations; it cannot prove focus,
touch behavior, responsive transitions, or task completion.
