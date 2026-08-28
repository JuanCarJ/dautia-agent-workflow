# Mapa oficial de Yabi API v2

Fuentes primarias consultadas el 2026-08-17:

- [Referencia GraphQL v2](https://developers.yabi.co/api/reference/v2/)
- [Guía v2](https://developers.yabi.co/api/guide/v2/welcome/)
- [Autenticación](https://developers.yabi.co/api/guide/v2/authentication/)
- [Factura estándar](https://developers.yabi.co/api/guide/v2/electronic_billing_documents/invoice/operation_types/standard_invoice/)
- [Nota crédito parcial](https://developers.yabi.co/api/guide/v2/electronic_billing_documents/credit_note/partial_refund/)
- [Estados de factura](https://developers.yabi.co/api/guide/v2/document_status/sales_invoice_status/)
- [Estados de nota crédito](https://developers.yabi.co/api/guide/v2/document_status/credit_note_status/)
- Colección Bruno oficial `bruno_examples_ms_invoice-bruno-v2.0.4-beta-1`, entregada al usuario el 2026-04-22.
- Propuesta Yabi para integradores v14, aportada por el usuario.

## Transporte y ambientes

- API GraphQL mediante HTTP `POST` y `Authorization: Bearer <token>`.
- Endpoint v2 mostrado en la colección: `https://api.yabi.co/co/einvoices/v2/`. Configurarlo; no hardcodearlo.
- La unidad organizacional define el ambiente. La propuesta distingue producción, habilitación asíncrona y pruebas síncronas; los ejemplos describen `TEST` como documentos sin validez fiscal.
- El token y la unidad se configuran como secretos del ambiente.

## Operaciones relevantes

| Propósito | Operación | Input/argumento |
|---|---|---|
| Crear factura | `createInvoice` | `document: InvoiceInput!` |
| Consultar factura | `invoice(uid: UID!)` | UID Yabi |
| Listar facturas | `invoices(...)` | paginación y `InvoiceDocumentQueryInput` |
| Crear nota parcial | `createCreditNote` | `document: CreditNoteInput!` |
| Anular totalmente | `voidInvoice` | `document: VoidInvoiceInput!` |
| Consultar nota | `creditNote(uid: UID!)` | UID Yabi |
| Listar notas | `creditNotes(...)` | paginación y `CreditNoteDocumentQueryInput` |
| Listar unidades | `organizationalUnits(...)` | paginación |
| Consultar unidad | `organizationUnit(id: UID!)` | UUID de unidad |

Yabi documenta anulación total mediante `voidInvoice` y devolución parcial mediante `createCreditNote`.

## Inputs principales

`InvoiceInput`: líneas, modificadores, partes, totales, información general, consecutivo, unidad organizacional, pago, referencias, impuestos y retenciones. Para factura estándar usar `operationCode: STD` y `subtypeCode: SALES_INVOICE`.

`CreditNoteInput`: líneas, modificadores, totales, información general, consecutivo, `invoiceToModify`, pago, referencias e impuestos. No acepta `organizationalUnitId`: Yabi determina la unidad desde la factura indicada por `invoiceToModify.uid`. Para nota parcial usar `operationCode: PARTIAL_REFUND` y `subtypeCode: CREDIT_NOTE`.

`VoidInvoiceInput`: consecutivo propio de la nota, `invoiceToVoid`, sistema emisor, notas y razón.

Los ejemplos beta indican que `issueDateTime` de factura no debe enviarse con el anexo DIAN 1.9 porque Yabi lo genera al firmar. Confirmar el esquema vigente para cada documento.

## Identificadores

- `uid`: UUID del documento en Yabi.
- `id`: prefijo + consecutivo.
- `documentUid`: CUFE/CUDE/CUDS según el documento.
- `organizationalUnitId`: unidad emisora.
- `documentStatus { code description }`: estado funcional.
- `dianState` / `assessmentState`: estado adicional cuando esté presente.

## Estados

- `YABICO_CREATED`: creado en Yabi, aún no equivale a validación DIAN.
- `DIAN_VALIDATING`: en validación.
- `DIAN_REJECTED`: rechazado; conservar causas.
- `DIAN_VALIDATED`: validado; correo puede seguir pendiente.
- `SEND_EMAIL`: correo enviado.
- `SEND_EMAIL_ERROR_YABI` / `SEND_EMAIL_ERROR_RECIPIENT`: validado con falla de correo, cuando aplique.

Consultar eventos de facturas a crédito antes de una nota. La guía advierte restricciones después de aceptaciones expresa o tácita.

## Errores

Inspeccionar transporte HTTP, `errors` GraphQL superiores y `errors`, `warnings`, `notifications` de la operación. Los errores Yabi incluyen normalmente `id`, `type`, `subType`, `message`, `title`, `helpText`, `language`.

Familias documentadas: `001-*` validación, `002` DIAN, `003-*` paginación, `004-*` procesamiento Yabi, `090` autenticación, `100-*` no encontrado y `200*` dato/consecutivo usado. Determinar si el documento fue creado antes de reintentar.

## Discrepancias conocidas

- `InvoiceInput.id` aparece no nulo y marcado opcional en la referencia renderizada.
- `VoidInvoiceInput.reason` aparece no nulo y marcado opcional.
- La página pública de anulación figura “EN PROCESO”, aunque la referencia y Bruno sí incluyen `voidInvoice`.

Resolver por esquema vigente, colección entregada o prueba controlada en `TEST`; nunca asumir en producción.
