# Design-system evolution

Use this when a change expands, breaks, migrates, or retires a shared component or
token family. Skip it when the accepted local change preserves that contract. It
does not authorize a package, repository, site, publication, migration, or provider.

## Decide from consumers

1. Inventory the affected family through its source, accepted visual reference, implementation, variants/states, and actual consumers. Similar appearance can be legitimate product variation.
2. Choose reuse when semantics, states, behavior, and visual contract fit; extend for a demonstrated repeated need without product-specific branches; create locally when semantics or brand are specific or reuse is hypothetical; retire only when required consumers have a replacement and migration or owned exception.
3. Keep shared mechanisms separate from product identity and business meaning. Accessibility mechanics may be shared while tokens, composition, copy, pricing, permissions, and taxonomy remain product-specific.
4. Define changed props/API, semantics, accessible name, keyboard/focus, content assumptions, responsive layout, tokens/themes, states, and relevant performance boundary.
5. Identify breakage and consumers before central edits. Use versioning only where distribution needs it; provide migration or explicit compatible exceptions.

A resolved broad migration, including many screens, remains a defined implementation;
its size does not reopen discovery. Validate focal states and each affected consumer
boundary. A green isolated story does not prove composition, content, overlays,
responsive behavior, or the journey. Record durable changes in the existing source
of truth rather than creating parallel governance material.

## Sources and limits

- InVision, *InVision's Guide to Benchmarking Your Design System*, physical pp. 4 and 14–24: scope, consumers, contribution, and reuse/extend/create/retire. Its maturity model, publication emphasis, and percentage gains do not establish requirements or ROI.
- InVision, *Design Systems Handbook*, physical pp. 28–39, 67–70, 78–116, 123–161, and 193–215: inventories, contracts, examples, pilots, testing, migration, and multiple identities. Its tooling, branches, separate-repository advice, and synchronization vision are historical examples.
- Brayan Yin Lin, *Atomic Design* course material, physical pp. 2–6: useful composition vocabulary based on the method originated by Brad Frost. It does not require atoms/molecules folders, and extraction alone proves neither accessibility nor reuse value.

Shared infrastructure does not prove that products need shared brand, a central team,
or publication.
