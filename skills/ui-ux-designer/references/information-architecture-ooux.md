# Information architecture and OOUX

Use this reference when objects, relationships, navigation, search, or visible
permissions are material and still open. Do not require a map for a defined change.

## Questions that change the design

- Name the actor's recognizable objects with real instances and the purpose each serves. A map, feed, selector, or table may represent an object without being the domain object.
- State relationships in both directions and distinguish zero, one, and many where it affects the experience. Confirm business meaning instead of deriving permissions or database structure from the drawing.
- Associate actions with actor, object, state, and actual permission. Do not generate universal CRUD. Read, search, filter, play, and navigation still need resolution if discovery postpones them.
- Separate object content from metadata used to identify, order, or filter. An available database attribute does not automatically deserve a control. Historical snapshots or deliberate denormalization may be valid.
- Define entry points, grouping, orientation cues, searchable attributes, facet combinations, result order, and recovery from no results.

Evidence should show that the actor can find the object from plausible entries,
understand location and state, take only allowed actions, and return without
unintended loss. A map does not prove screens, persistence, taxonomy, accessibility,
or the complete journey.

## Sources and limits

- *Semana 2 - Arquitectura de información*, physical pp. 2–13 and 16–31: organization, navigation, labeling, search, hierarchy, and scan hypotheses. F/Z patterns are prompts, not mandatory layouts or eye-tracking evidence.
- *Semana 2 - OOUX*, physical pp. 11–14: objects, relationships, role actions, attributes, and metadata. Its “ORCAM” and OOP/database analogy are course adaptations, not instructions to generate classes or tables.
- Sophia Prater, *Object Mapping Quick Start Guide V2* (2023), physical pp. 1–6: SIP, relationships, calls to action, and attributes within the Discovery Round of a broader four-round ORCA process. The quick map is intentionally incomplete.

Treat examples as historical teaching material. Product contracts and observed
behavior decide the current design.
