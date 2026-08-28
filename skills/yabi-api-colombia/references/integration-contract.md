# Contrato MaderCore/Habilis

## Responsabilidades

| Capa | Responsabilidad |
|---|---|
| Producto | Decidir qué transacción es facturable y conservar detalle comercial |
| Adaptador Yabi | Mapear, validar, enviar, consultar y normalizar respuestas |
| Outbox/ledger | Idempotencia, auditoría, reintentos seguros y conciliación |
| Yabi/DIAN | Radicación, validación y archivos electrónicos |

No hacer de Yabi el origen de inventario, caja, pedidos o devoluciones. No hacer del producto el origen del estado DIAN.

## Descubrir el disparador

- En MaderCore, una remisión puede ser candidata; no asumir que toda remisión se factura.
- En Habilis, una venta confirmada puede ser candidata; no acoplar Yabi a la transacción atómica de inventario/caja.
- Una devolución puede originar nota parcial o anulación total; confirmar factura original y decisión comercial.

Persistir primero la operación local y encolar después. Una indisponibilidad Yabi no debe revertir inventario, caja o remisión.

## Adaptador sugerido

```ts
interface ElectronicDocumentProvider {
  createInvoice(command: CreateInvoiceCommand): Promise<SubmissionResult>
  createPartialCreditNote(command: CreatePartialCreditNoteCommand): Promise<SubmissionResult>
  voidInvoice(command: VoidInvoiceCommand): Promise<SubmissionResult>
  getInvoice(uid: string): Promise<DocumentSnapshot>
  getCreditNote(uid: string): Promise<DocumentSnapshot>
}
```

Mantener DTOs internos independientes de GraphQL Yabi y traducir en un adaptador versionado.

## Ledger mínimo

- empresa, ambiente, sistema/tipo/id origen;
- tipo de operación, `operation_key` única, versión/hash del payload;
- estado, intentos, siguiente intento, lease del worker;
- `yabi_uid`, consecutivo, `document_uid`, estado Yabi/DIAN;
- errores/advertencias sanitizados y última conciliación;
- factura original para notas.

Estados mínimos: `draft -> queued -> submitting -> yabi_created -> dian_validating -> dian_validated -> email_sent`; ramas `unknown`, `dian_rejected`, `email_error`.

## Idempotencia

- Derivar `operation_key` de datos estables y aplicar unicidad en DB.
- Calcular hash sobre JSON canónico sin secretos/campos volátiles.
- Misma clave con otro hash es conflicto; no sobrescribir.
- Un solo worker gana `queued -> submitting`.
- Tras timeout, conciliar; no llamar de nuevo a ciegas.

## Mapeo fiscal

Confirmar emisor/adquirente, identificaciones, responsabilidades, dirección, unidad, prefijo, moneda, unidades, cantidades, bases, descuentos, cargos, impuestos, retenciones, pago, email y referencias. Usar decimal exacto y demostrar totales por línea/documento.

## Notas crédito

- No exceder el valor acreditable ni duplicar anulación total.
- En parcial, conservar líneas, cantidades, bases e impuestos proporcionales.
- En total, usar `voidInvoice` y enlazar la nota; la factura permanece emitida.
- Inventario/caja cambian por el flujo local confirmado, no por la respuesta Yabi.

## Configuración

```text
YABI_API_URL
YABI_API_TOKEN
YABI_ORGANIZATIONAL_UNIT_ID
YABI_EXPECTED_ENVIRONMENT=TEST
YABI_WRITES_ENABLED=false
```

Separar valores por empresa/ambiente. Activar en orden: lecturas, mapper puro, worker simulado, unidad `TEST`, conciliación/concurrencia y finalmente producción con autoridad explícita.
