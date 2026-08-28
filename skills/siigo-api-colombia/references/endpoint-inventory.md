# Siigo API Colombia endpoint inventory

Snapshot reviewed: 2026-07-28.

Primary sources:

- <https://developers.siigo.com/docs/siigoapi/>
- <https://developers.siigo.com/search-index.json>
- <https://developers.siigo.com/docs/siigoapi/novedades/>

The official Colombia index contained 86 entries: 77 operational pages and 9 general pages. Two operational pages document the same `GET /v1/account-groups`; the inventory adds the officially announced but currently mislinked `POST /v1/invoices/batch`, resulting in 77 normalized operation signatures.

This snapshot accelerates orientation. Recheck the current official page before implementation because availability, fields, limits, and documentation can drift.

## Authentication and catalogs

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/auth` | Generate access token |
| `GET` | `/v1/account-groups` | Inventory groups/categories |
| `GET` | `/v1/taxes` | Configured taxes |
| `GET` | `/v1/price-lists` | Price lists |
| `GET` | `/v1/warehouses` | Warehouses |
| `GET` | `/v1/users` | Users/sellers |
| `GET` | `/v1/document-types` | Document types |
| `GET` | `/v1/payment-types` | Payment methods |
| `GET` | `/v1/cost-centers` | Cost centers |
| `GET` | `/v1/fixed-assets` | Fixed assets |
| `GET` | `/v1/expenses` | Voucher discounts |
| `GET` | `/v1/misc-incomes` | Miscellaneous-income concepts |
| `POST` | `/v1/account-groups` | Create inventory group |
| `PUT` | `/v1/account-groups/{id}` | Update inventory group |

Known `document-types` filters:

| Query | Document |
|---|---|
| `type=C` | Quotation |
| `type=FV` | Sales invoice |
| `type=FC` | Purchase invoice |
| `type=RC` | Cash receipt/voucher |
| `type=RP` | Payment/expense receipt |
| `type=NC` | Credit note |
| `type=CC` | Journal/accounting entry |
| `type=DS` | Purchase support document |

## Products

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/products` | List/filter products and services |
| `GET` | `/v1/products/{id}` | Get product |
| `POST` | `/v1/products` | Create product |
| `PUT` | `/v1/products/{id}` | Update product |
| `DELETE` | `/v1/products/{id}` | Delete product |

## Customers/third parties

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/customers` | List/filter customers |
| `GET` | `/v1/customers/{id}` | Get customer |
| `POST` | `/v1/customers` | Create customer |
| `PUT` | `/v1/customers/{id}` | Update customer |

## Quotations

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/document-types?type=C` | Quotation document types |
| `GET` | `/v1/quotations` | List quotations |
| `GET` | `/v1/quotations/{id}` | Get quotation |
| `POST` | `/v1/quotations` | Create quotation |
| `PUT` | `/v1/quotations/{id}` | Update quotation |
| `DELETE` | `/v1/quotations/{id}` | Delete quotation |

No official quotation PDF endpoint or quotation-to-invoice/remission conversion endpoint was found in the reviewed portal.

## Sales invoices

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/document-types?type=FV` | Sales-invoice document types |
| `GET` | `/v1/invoices` | List invoices |
| `GET` | `/v1/invoices/{id}` | Get invoice |
| `GET` | `/v1/invoices/{id}/stamp/errors` | Get electronic-submission errors |
| `GET` | `/v1/invoices/{id}/pdf` | Get invoice PDF |
| `GET` | `/v1/invoices/{id}/xml` | Get invoice XML |
| `POST` | `/v1/invoices` | Create invoice |
| `POST` | `/v1/invoices/batch` | Create asynchronous invoice batch |
| `PUT` | `/v1/invoices/{id}` | Update invoice |
| `POST` | `/v1/invoices/{id}/annul` | Annul invoice |
| `POST` | `/v1/invoices/{id}/mail` | Send invoice email |
| `DELETE` | `/v1/invoices/{id}` | Delete invoice |

## Credit notes

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/document-types?type=NC` | Credit-note document types |
| `GET` | `/v1/credit-notes` | List credit notes |
| `GET` | `/v1/credit-notes/{id}` | Get credit note |
| `GET` | `/v1/credit-notes/{id}/pdf` | Get credit-note PDF |
| `POST` | `/v1/credit-notes` | Create credit note |

## Purchases and support documents

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/document-types?type=FC` | Purchase-invoice document types |
| `GET` | `/v1/purchases/{id}` | Get purchase invoice |
| `POST` | `/v1/purchases` | Create purchase invoice |
| `PUT` | `/v1/purchases/{id}` | Update purchase invoice |
| `DELETE` | `/v1/purchases/{id}` | Delete purchase invoice |
| `GET` | `/v1/document-types?type=DS` | Support-document types |
| `GET` | `/v1/purchase-support-documents/{id}` | Get support document |
| `POST` | `/v1/purchase-support-documents` | Create support document |
| `PUT` | `/v1/purchase-support-documents/{id}` | Update support document |
| `DELETE` | `/v1/purchase-support-documents/{id}` | Delete support document |

The introduction advertises list capability for purchases and support documents, but the reviewed endpoint pages specify only detail routes. Do not assume collection `GET` routes without confirmation.

## Cash receipts/customer payments

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/document-types?type=RC` | Voucher document types |
| `GET` | `/v1/vouchers` | List vouchers |
| `GET` | `/v1/vouchers/{id}` | Get voucher |
| `POST` | `/v1/vouchers` | Create debt or advance-payment voucher |
| `POST` | `/v1/vouchers?type=MiscIncome` | Create miscellaneous-income voucher |

## Payment/expense receipts

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/document-types?type=RP` | Payment-receipt document types |
| `GET` | `/v1/payment-receipts` | List payment/expense receipts |
| `GET` | `/v1/payment-receipts/{id}` | Get payment/expense receipt |
| `POST` | `/v1/payment-receipts` | Create payment/expense receipt |
| `DELETE` | `/v1/payment-receipts/{id}` | Delete payment/expense receipt |

The portal advertises edit capability but did not expose a current edit operation page. Do not assume `PUT /v1/payment-receipts/{id}`.

## Journals

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/document-types?type=CC` | Journal document types |
| `GET` | `/v1/journals` | List journals |
| `GET` | `/v1/journals/{id}` | Get journal |
| `POST` | `/v1/journals` | Create journal |

## Reports

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/accounts-payable` | Accounts-payable report |
| `POST` | `/v1/test-balance-report` | Generate trial balance |
| `POST` | `/v1/test-balance-report-by-thirdparty` | Generate third-party trial balance |

Report `POST` operations generate read-oriented reports but remain POST requests and require explicit method allowance.

## Webhooks

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/v1/webhooks` | List subscriptions |
| `POST` | `/v1/webhooks` | Create subscription |
| `PUT` | `/v1/webhooks` | Update subscription |
| `DELETE` | `/v1/webhooks/{id}` | Delete subscription |

## Current documentation discrepancies

| Capability | Current issue | Handling |
|---|---|---|
| Invoice batch | Novedades announces it, but the current link resolves to invoice update | Treat `/v1/invoices/batch` as unresolved before implementation |
| Payment-receipt list | Page exists without a rendered method/route block | Verify through current contract or controlled read |
| Voucher document type | Page lacks a rendered HTTP block | Normalize to `type=RC`, then verify before dependency |
| Purchase-invoice document type | Page incorrectly shows `type=NC` | Normalize semantically to `type=FC` and verify |
| Purchase/support-document lists | Introduction advertises list behavior without current collection pages | Do not invent routes |
| Payment-receipt edit | Introduction/Novedades advertise edit without a current operation page | Do not invent method/path |
