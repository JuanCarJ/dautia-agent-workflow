---
name: gelotra-readonly-research
description: Use when reverse engineering or documenting Redecarga's Gelotra workflows in read-only mode, including GELOTRA/Gelotra screens, Aforo, Clientes, Acuerdos, Centros Logisticos, tarifarios, usuarios/perfiles, cumplidos, EXXE guide/status/barcode flows, guide generation, tracking, billing, or Playwright capture of Gelotra UI. This is for safe discovery and documentation, not changing Gelotra data.
---

# Gelotra Readonly Research

## Overview

Document Gelotra behavior without altering production data. Use this playbook for discovery sessions where the output is Markdown evidence about screens, fields, tables, calculations, and integration contracts.

## Safety Contract

Use browser automation for observation only. Do not press or script actions such as `Guardar`, `Crear`, `Nuevo Registro`, `Eliminar`, `Anular`, `Importar`, `Enviar Archivos`, `Generar guia`, `Enviar factura`, or equivalent state-changing controls.

Do not persist credentials, passwords, session cookies, CSRF tokens, or full personal identifiers in docs or scripts. Prefer credentials via the browser session or environment variables for one command invocation.

After login, install safeguards in any Playwright probe:

- log all network requests with method, URL, status, and route label
- block or fail on unexpected `POST`, `PUT`, `PATCH`, or `DELETE`
- allow authentication requests only before the read-only guard is enabled
- block clicks/submits whose text or accessible name implies save, delete, import, upload, generate, or send

If the user asks "no cambiaste nada verdad?", answer from evidence: list the routes opened, say whether any mutating request happened, and distinguish Gelotra state from local docs/evidence files.

## Local Prep

Resolve the Redecarga governance or technical repository from the current Git checkout and its `delivery.yaml`; use a different checkout only when the user identifies it.

Before writing docs or scripts:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
```

Read existing `docs/gelotra-*.md`, `docs/exxe-*.md`, and `docs/README.md` when present. Keep new docs additive and linked from the closest existing inventory.

Store raw evidence under `output/playwright/<gelotra-topic>/`. Treat this folder as local evidence, not user-facing polished documentation.

## Capture Workflow

Map each inspected module with the same structure:

- route and visible page title
- business purpose
- filters/search fields
- visible table columns and row counts, clearly distinguishing visible page count from total count
- forms, editable fields, readonly fields, disabled fields, and hidden fields only when relevant
- actions visible but not used
- AJAX endpoints observed and whether they appear read-only or calculation-related
- examples with minimal necessary business data
- open questions before migration or redesign

For heavy grids such as tarifarios, prefer paginated or `Todo` GET-style reads only when the site supports it without mutation. Summarize distributions instead of copying full tables.

For calculation flows such as Aforo/Casa Toro, separate:

- observed UI values
- observed endpoint responses
- inferred rule
- unresolved validation needed before rebuilding

## Documentation Output

Write concise Markdown in `docs/`, using names like:

- `docs/gelotra-inventario-funcional.md`
- `docs/gelotra-parametrizacion-maestros.md`
- `docs/gelotra-aforo-venta-encomienda.md`
- `docs/gelotra-clientes-acuerdos-*.md`
- `docs/gelotra-centro-logistico-*.md`
- `docs/exxe-apis-integracion.md`

Link new documents from the existing inventory or README. Keep vehicle/GPS modules out of scope unless the user explicitly brings them back.

Use Spanish business language for user-facing docs. Prefer exact Gelotra labels for modules and fields, but avoid dumping full third-party PII.

## Validation Before Closing

Run targeted checks:

```bash
rg -n "password|contraseña|csrf|token|cookie|Cumplidos2026" docs output/playwright/<gelotra-topic>
git status --short
```

If raw evidence necessarily contains session-shaped data, ensure polished docs do not. Report:

- Gelotra routes inspected
- whether writes were blocked or absent
- docs created/updated
- evidence folder path
- credential/token hygiene result
- unrelated pre-existing dirty files left untouched
