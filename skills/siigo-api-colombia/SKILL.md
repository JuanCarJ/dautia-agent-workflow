---
name: siigo-api-colombia
description: "Use whenever designing, implementing, reviewing, debugging, or answering doubts about a connection to Siigo API Colombia or Siigo Nube: authentication, Partner-Id, endpoints, products, customers, quotations, invoices, DIAN, credit notes, purchases, vouchers/payments, journals, reports, webhooks, catalog sync, MCP adapters, errors, rate limits, idempotency, or account-backed verification. Default to current official evidence and read-only behavior; business writes require explicit authority. This skill is not authoritative for Siigo Mexico."
---

# Siigo API Colombia Expert

Design and verify Siigo integrations from the current Colombia contract, the real application, and observable account behavior. Use this skill both when building a connection and when a Siigo doubt could change architecture, data, accounting state, or user-facing truth.

## Core outcome

Produce the smallest correct design, implementation, diagnosis, or answer while keeping four truths separate:

1. what Siigo currently documents;
2. what the application or MCP actually implements;
3. what the connected company and plan allow;
4. what happened to the specific business document.

Never turn a documented capability into a claim that it is enabled, connected, or successful in the target account.

## Orient before deciding

Resolve only what the task needs:

- country: Colombia; stop and research separately if the target is Mexico;
- surface: direct API, Siigo Nube UI, SDK, custom proxy, or MCP adapter;
- company and environment: test or production, without exposing identifiers;
- result: discovery, audit, implementation, diagnosis, or an explicitly authorized business mutation;
- source of truth for customers, products, prices, inventory, quotations, invoices, payments, and operational documents;
- repo, branch, runtime, provider, current revision, and existing Siigo client or adapter;
- read/write authority and stop condition.

Treat `POST /auth` as technical authentication, not a business write. Creating or changing a customer, product, quotation, invoice, note, voucher, journal, webhook, or payment is a business mutation.

## Source hierarchy

Use sources in this order:

1. [Official Siigo API Colombia portal](https://developers.siigo.com/docs/siigoapi/).
2. [Official search index](https://developers.siigo.com/search-index.json) and the current endpoint page.
3. Current application code, runtime configuration, MCP tool schema, SDK version, or provider contract.
4. Credential-backed read-only verification against the intended company and environment.
5. Legacy Apiary material only to explain a missing, broken, or contradictory current page.

Browse the current official source whenever an endpoint, field, limit, error, DIAN rule, or capability may have changed. Do not rely on an old inventory alone. Read [references/endpoint-inventory.md](references/endpoint-inventory.md) when the task needs family coverage, route selection, or contradiction handling. Read [references/mcp-adapters.md](references/mcp-adapters.md) when an MCP or conversational tool is involved.

## Authentication and request contract

- Base URL: `https://api.siigo.com`.
- Obtain a JWT through `POST /auth` using `username` and `access_key`.
- Keep credentials and tokens server-side. Never place them in browser code, logs, documentation, screenshots, prompts, fixtures, or committed files.
- Send the real application identity in `Partner-Id`; do not invent or vary it per request.
- Send the access token and `Partner-Id` on `/v1` requests according to the current official contract and the verified client behavior.
- Cache the token in server memory or an equally protected short-lived store and renew it before expiry.
- Do not log full request/response bodies when they contain personal, tax, financial, invoice, payment, or credential data.

The current official documentation reports 100 requests per minute per production company and 10 per minute for the test company. Implement bounded concurrency, exponential backoff for `429` and transient availability errors, and pagination instead of unbounded reads. Recheck those limits before designing a high-volume sync.

## Selecting endpoints

For every operation that matters, record:

- HTTP method and normalized route;
- business purpose and source-of-truth role;
- required path, query, headers, and prerequisite catalog IDs;
- pagination, dates, filters, limits, and timeout behavior;
- request and response fields actually consumed;
- read, technical auth, business write, destructive write, or external side effect;
- idempotency eligibility;
- company/plan/configuration dependency;
- evidence status: documented, implemented, account-verified, or user-visible.

Do not infer missing routes from resource naming. If the portal advertises a capability but lacks a valid method/path page, label it unresolved and confirm it with Siigo or a controlled read before implementation.

## Designing a reliable integration

Keep Siigo access behind a server boundary with:

- an explicit resource, method, path, and query allowlist;
- request validation and response normalization;
- timeouts, bounded retries, and rate-limit handling;
- structured errors that preserve Siigo `Status`, `Code`, `Message`, `Params`, and `Detail` without leaking sensitive payloads;
- audit correlation that does not store access tokens or full personal documents;
- tests for auth failure, `429`, timeout, unavailable service, invalid reference, and duplicate creation.

For broad product or customer search, prefer a durable indexed cache populated by paginated `GET` synchronization, then refresh the selected record from Siigo before using it. Expose freshness and fallback state. Do not mistake one rendered page for the full catalog or use production Siigo pagination as a free-text search engine.

Preserve historical snapshots in accepted quotations, operational documents, or issued artifacts. A later change in Siigo must not silently rewrite what the customer accepted.

## Business mutations

Never execute a business write from an audit, question, example, or design request. Require explicit authority for the exact company, environment, resource, and action.

Before an authorized mutation:

1. read the current target and prerequisite catalogs;
2. validate customer/product/document/seller/payment/tax identifiers without printing sensitive values;
3. show or internally validate the exact bounded payload and expected side effects;
4. use `Idempotency-Key` only for the supported creation POSTs documented by Siigo: invoices, credit notes, journals, and vouchers;
5. never send `Idempotency-Key` on `GET`, `PUT`, or `DELETE`;
6. do not blindly retry a timed-out write—query by the idempotency key or business reference first;
7. verify the returned resource and every downstream state separately.

Deletion, annulment, electronic submission, email delivery, webhook changes, and payment registration are distinct side effects. Do not bundle authority across them.

## Invoice and DIAN state model

Always distinguish:

- document saved or created in Siigo;
- electronic submission requested;
- DIAN accepted, rejected, pending, or errored;
- PDF/XML available;
- email requested and delivered or failed;
- balance pending, partially paid, or paid;
- document annulled or related to a credit note.

HTTP success proves only the API request. A created invoice is not automatically DIAN-approved, emailed, or paid. Use the invoice detail and, when relevant, the stamp error, PDF/XML, and mail operations to verify the requested outcome.

## Diagnosing failures

Find the first failing boundary:

1. server configuration and company/environment identity;
2. token generation and expiry;
3. `Authorization` and `Partner-Id`;
4. route, method, query, and endpoint availability;
5. company plan, document configuration, active catalog IDs, and user blocking;
6. rate limit, timeout, or Siigo service availability;
7. payload validation and accounting rules;
8. document lifecycle, DIAN, email, balance, or related-document constraints;
9. application cache, sync, proxy, UI, or MCP interpretation.

Report the exact boundary and evidence. Do not blame Siigo infrastructure before testing auth, route, payload, and application handling separately.

## MCP and agent adapters

Treat an MCP as an optional execution adapter, never as the Siigo source of truth. Before use:

- inspect its live tool names, descriptions, input schemas, output schemas, version, auth model, and provider;
- map each tool to the likely official Siigo operation;
- classify read tools, sensitive reads, business writes, and destructive or externally visible side effects;
- enable the minimum granular tool set;
- require explicit confirmation for invoice, quotation, customer/product, payment, email, annulment, or webhook writes;
- verify a mutation through a follow-up read from Siigo, not only the MCP success message.

An adapter claim such as “convert quotation to invoice” or “returns the PDF URL” is not an official Siigo capability until its implementation and result are verified.

## Validation and closeout

Validate proportionally:

- contract: official page and normalized method/route;
- code: allowlist, secret boundary, retry/idempotency logic, and focused tests;
- integration: intended test or verified non-production company when available;
- business state: follow-up reads for the exact document;
- UI or agent: truthful state labels and no leaked sensitive data.

Close with:

- endpoint or tool used;
- company/environment class and revision, without sensitive identifiers;
- files or components changed;
- tests and account-backed evidence;
- business mutations and side effects, or confirmation that none occurred;
- Git/deploy truth;
- unresolved documentation, plan, DIAN, or provider risks.
