# Siigo MCP adapter evaluation

## Jelow Siigo marketplace adapter

Reviewed: 2026-07-28.

Public sources:

- <https://jelou.ai/es/marketplace/siigo>
- <https://docs.jelou.ai/guides/integraciones/integraciones>
- <https://docs.jelou.ai/guides/integraciones/como-usar-integraciones-en-brain>

Verdict: useful as an optional conversational execution adapter, not as an authoritative or complete Siigo API layer.

The public marketplace page advertises 11 tools. The mapping below is inferred from public descriptions; inspect the connected MCP's actual tool schemas and implementation before use.

| Jelow tool | Likely Siigo operation | Class | Required handling |
|---|---|---|---|
| Crear Factura | `POST /v1/invoices` | Financial/business write | Explicit authority, prerequisite catalogs, idempotency, follow-up invoice/DIAN verification |
| Crear Proforma | `POST /v1/quotations` | Business write | Explicit authority and follow-up read; do not assume native conversion to invoice |
| Obtener Historial del Cliente | `GET /v1/invoices` filtered by customer/date | Sensitive read | Minimize PII and financial history; require bounded pagination/date range |
| Obtener Estado de Inventario | `GET /v1/products` or `/v1/products/{id}` | Read | Verify product resolution and warehouse freshness |
| Obtener Estado de Factura | `GET /v1/invoices/{id}` | Sensitive read | Separate created, DIAN, email, annulment, balance, and payment states |
| Listar Clientes | `GET /v1/customers` | PII read | Filter and paginate; do not dump full customer lists |
| Listar Tipos de Documento | `GET /v1/document-types` | Read | Filter by the exact document family |
| Listar Métodos de Pago | `GET /v1/payment-types` | Read | Filter by document type and active status |
| Listar Productos | `GET /v1/products` | Read | Paginate; do not treat one page as global search |
| Listar Usuarios | `GET /v1/users` | Sensitive read | Return only fields needed to choose a seller |
| Registrar Pago | `POST /v1/vouchers` | Financial/business write | Explicit authority, debt/advance type validation, idempotency, follow-up voucher and balance verification |

## What it adds

- Ready-made conversational operations for common sales and collection questions.
- A compact read set covering customer, product, inventory, invoice, document, payment-method, and seller lookup.
- Three useful but high-impact write tools for quotations, invoices, and customer payments.
- Compatibility with agent surfaces and granular tool selection in Jelow.

## What it does not cover publicly

The 11-tool public surface does not provide full coverage of:

- customer/product update or delete;
- credit-note operations;
- purchase invoices and purchase support documents;
- journals;
- accounts-payable and trial-balance reports;
- webhooks;
- price lists, taxes, warehouses, cost centers, fixed assets, expenses, and miscellaneous-income catalogs as standalone tools;
- invoice XML, stamp-error, mail, annul, or delete operations as distinct tools;
- all endpoint filters and response schemas.

Do not use the adapter as a replacement for the official inventory or a custom integration when the missing families matter.

## Safe adoption

1. Inspect the live MCP server identity, provider, version, tool names, descriptions, schemas, and authentication model.
2. Prefer Jelow's granular mode and enable only the read tools required by the agent.
3. Keep `Crear Factura`, `Crear Proforma`, and `Registrar Pago` disabled until the exact flow has explicit write authority, confirmation, idempotency, and follow-up verification.
4. Confirm whether credentials are stored by Jelow, how company/environment selection works, and what audit logs or version pinning exist.
5. Test read tools first against the intended non-production or otherwise authorized account.
6. Treat tool output as adapter evidence. Verify financial or DIAN outcomes through an independent Siigo read.
7. Reinspect schemas and rerun focal tests after an MCP version update.

## Claims requiring verification

- “Quotation can later be converted to invoice” may describe Jelow orchestration, not a public Siigo conversion endpoint.
- “Create Invoice returns the PDF URL” may be an adapter-composed result; verify the returned field and invoice PDF availability.
- “Register Payment” must be mapped to the intended customer voucher type and invoice balance behavior before use.
