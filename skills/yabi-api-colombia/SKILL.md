---
name: yabi-api-colombia
description: Diseñar, implementar, revisar y diagnosticar integraciones con la API GraphQL v2 de Yabi para facturación electrónica colombiana, notas crédito parciales, anulación total de facturas, consulta de unidades organizacionales, estados DIAN, archivos y conciliación. Usar cuando una tarea mencione Yabi, developers.yabi.co, createInvoice, createCreditNote, voidInvoice, CUFE, CUDE, facturación electrónica o notas crédito mediante Yabi, especialmente en MaderCore o Habilis.
---

# Yabi API Colombia

Integrar Yabi como proveedor tecnológico entre el sistema operativo y la DIAN. Mantener la decisión comercial en el producto y la verdad de radicación/validación en Yabi/DIAN.

Fuentes oficiales canónicas:

- Guía API v2: https://developers.yabi.co/api/guide/v2/welcome/
- Referencia GraphQL v2: https://developers.yabi.co/api/reference/v2/

## Orientar la tarea

1. Clasificar el pedido como lectura, diseño, implementación, prueba o escritura externa.
2. Identificar producto, empresa, ambiente, endpoint real, unidad organizacional, prefijo, credencial y documento origen.
3. Inspeccionar el flujo que vuelve facturable una venta o remisión. No asumir que crear una venta, cerrar caja o convertir una remisión autoriza facturar.
4. Mantener toda escritura bloqueada hasta que el usuario autorice el ambiente y el tipo de documento. Producción, DIAN y correo al cliente son efectos externos reales.

Leer [official-api-map.md](references/official-api-map.md) al trabajar con operaciones, inputs, estados o errores. Leer [integration-contract.md](references/integration-contract.md) al diseñar o implementar MaderCore/Habilis. Leer [graphql-operations.md](references/graphql-operations.md) al construir consultas o mutaciones. Leer [document-payloads.md](references/document-payloads.md) al mapear facturas con IVA 19 %, facturas con IVA 0 %, notas crédito parciales, anulaciones o archivos PDF/XML.

## Fijar las fronteras

- Invocar Yabi solo desde backend, CLI privada o worker; nunca desde navegador o cliente móvil.
- Guardar el bearer token fuera de Git, base de datos de negocio, logs, errores y respuestas al cliente. Separar credenciales por empresa y ambiente.
- Tratar el endpoint como configuración entregada por Yabi. No deducir staging o producción por el hostname.
- Verificar `unitSettings.environment` de la unidad organizacional antes de cualquier mutación. La documentación privada distingue `TEST` sin validez fiscal, habilitación y producción.
- Separar `internal_id`, `operation_key`, `payload_hash`, `uid` Yabi, consecutivo `id` y `documentUid` DIAN.
- Calcular dinero con decimal exacto, serializar con punto decimal y reconciliar líneas, descuentos, cargos, impuestos, retenciones, anticipos y total pagable antes de enviar.

## Ejecutar escrituras con seguridad

1. Construir un comando local inmutable desde el documento origen confirmado.
2. Asignar una `operation_key` única por empresa, ambiente, tipo de operación y documento origen.
3. Persistir en outbox/ledger el comando, su hash y estado `queued` antes de llamar a Yabi.
4. Enviar una sola mutación con variables GraphQL y una selección mínima de respuesta.
5. Evaluar transporte HTTP, `errors` GraphQL superiores y `errors`, `warnings`, `notifications` del resultado.
6. Persistir `uid`, consecutivo, `documentUid`, estado, error y archivo retornado antes de confirmar al usuario.
7. Consultar por `uid` hasta conocer el estado DIAN dentro de una ventana acotada; después conciliar de forma asíncrona.

No considerar un HTTP 200 como factura emitida. Distinguir al menos: aceptada por Yabi, validando en DIAN, validada por DIAN, rechazada por DIAN y correo enviado.

## Resolver resultados ambiguos

- Ante timeout, desconexión o 5xx después de enviar, marcar `unknown`; no reintentar automáticamente.
- Consultar Yabi por `uid` conocido o por los filtros vigentes de consecutivo/unidad antes de otra mutación.
- No consumir un nuevo consecutivo ni crear un segundo documento para probar.
- Reintentar automáticamente solo fallos demostrablemente anteriores al envío o lecturas idempotentes con política acotada.
- Tratar `200 data + errors` como resultado fallido o parcial; conservar `warnings` y `notifications`.

## Emitir notas crédito

1. Confirmar que la factura original pertenece a la misma empresa/ambiente y fue radicada en DIAN.
2. Consultar sus notas previas, saldo acreditable y eventos. Bloquear duplicados, sobredevoluciones y estados incompatibles.
3. Usar `createCreditNote` para devolución parcial y reconstruir líneas/totales acreditados.
4. Usar `voidInvoice` para anulación total. La respuesta es una nota crédito, no una eliminación.
5. Persistir la relación con la factura, consecutivo propio, `uid`, `documentUid` y estado DIAN.

No borrar ni mutar la factura original. Registrar la nota como documento adicional y derivar el saldo neto.

## Validar por ambiente

- Empezar con consultas autenticadas de unidad organizacional y prefijos; no registrar el token.
- Ejecutar mutaciones únicamente en la unidad `TEST` confirmada hasta recibir autoridad explícita para otro ambiente.
- Probar factura estándar, rechazo controlado, conciliación, nota parcial y anulación total sin reutilizar consecutivos.
- Verificar reinicio, concurrencia y entrega al menos una vez sin duplicar documentos.
- Para producción, fijar empresa, unidad, prefijos vigentes, rango disponible, correo, rollback compensatorio y responsable de conciliación.

## Cerrar con verdad verificable

Reportar por documento: sistema origen, ambiente, operación, `operation_key`, consecutivo, `uid` Yabi, `documentUid` DIAN, último estado consultado, errores/advertencias y archivos disponibles. Separar código validado, llamada aceptada por Yabi, validación DIAN y notificación por correo.
