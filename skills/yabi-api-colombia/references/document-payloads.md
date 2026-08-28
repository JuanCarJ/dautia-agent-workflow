# Payloads fiscales mínimos y archivos

Estos ejemplos fueron contrastados el 2026-08-17 con el esquema GraphQL activo de la unidad `test`. Los payloads de IVA 19 %, IVA 0 % y nota crédito parcial derivan de documentos aceptados y conciliados en esa unidad. Sustituir todos los marcadores `<...>` y volver a comprobar prefijo, rango, adquirente, tratamiento tributario y totales antes de escribir.

## Reglas comunes

- Enviar importes decimales como cadenas con punto decimal, nunca con separador de miles ni coma decimal.
- No enviar `issueDateTime` para factura bajo el anexo DIAN 1.9; Yabi lo fija al firmar.
- Repetir los impuestos coherentemente en cada línea y en el total del documento.
- Para el caso simple sin descuentos, cargos, anticipos ni retenciones:
  - `lineExtensionAmount = sum(cantidad * precio)` antes de impuestos;
  - `taxAmount = taxableAmount * percent / 100`;
  - `taxExclusiveAmount = lineExtensionAmount`;
  - `taxInclusiveAmount = taxExclusiveAmount + impuestos`;
  - `payableAmount = taxInclusiveAmount`.
- Con descuentos, cargos, anticipos o retenciones, reconstruir y demostrar toda la aritmética; no adaptar estos totales por intuición.
- `CO_01` identifica IVA en estos ejemplos. Confirmar el código tributario real de cada producto.
- “Sin impuesto” es ambiguo. IVA a tarifa 0 %, exento, excluido y no sujeto no son equivalentes. El segundo ejemplo representa **IVA 0 %** porque ese fue el caso probado; no reutilizarlo para un producto excluido sin validar su clasificación fiscal.
- Los adquirentes incluidos son datos ficticios de prueba. Nunca copiar identificaciones de ejemplo a producción.

## Factura estándar con IVA 19 %

Variables de `createInvoice`:

```json
{
  "document": {
    "organizationalUnitId": "<OU_UUID>",
    "id": {
      "prefix": "<PREFIJO_FACTURA>",
      "number": 12345
    },
    "generalInformation": {
      "currency": "COP",
      "operationCode": "STD",
      "subtypeCode": "SALES_INVOICE"
    },
    "documentLines": [
      {
        "lineId": 1,
        "unitCode": "CO_ZZ",
        "quantity": 2,
        "description": {
          "locale": "ES_CO",
          "text": "Producto gravado con IVA 19 %"
        },
        "itemDescription": {
          "brandName": "Marca de prueba",
          "standardItemId": {
            "id": "SKU-IVA-19",
            "standardId": "TAXPAYER_STANDARD"
          },
          "incomeType": "SELF_OWNED"
        },
        "lineExtensionAmount": "10000",
        "price": {
          "priceAmount": "5000",
          "baseQuantity": 1,
          "unitCode": "CO_ZZ",
          "priceType": "COMMERCIAL_VALUE"
        },
        "taxDescription": [
          {
            "taxName": "CO_01",
            "taxAmount": "1900",
            "roundingAmount": "0",
            "taxSubtotal": [
              {
                "taxAmount": "1900",
                "percent": 19,
                "taxableAmount": "10000"
              }
            ]
          }
        ]
      }
    ],
    "documentParties": {
      "accountingCustomerParty": {
        "additionalAccountId": "NATURAL_PERSON",
        "personId": {
          "idType": "CC",
          "identifier": "222222222222"
        },
        "personName": {
          "firstName": "Consumidor",
          "firstSurname": "Final"
        },
        "physicalLocation": {
          "address": "Bogotá D.C.",
          "country": "CO",
          "city": "11001"
        }
      }
    },
    "taxDescription": [
      {
        "taxName": "CO_01",
        "taxAmount": "1900",
        "roundingAmount": "0",
        "taxSubtotal": [
          {
            "taxAmount": "1900",
            "percent": 19,
            "taxableAmount": "10000"
          }
        ]
      }
    ],
    "documentTotals": {
      "lineExtensionAmount": "10000",
      "taxExclusiveAmount": "10000",
      "taxInclusiveAmount": "11900",
      "allowanceTotalAmount": "0",
      "chargeTotalAmount": "0",
      "prePaidAmount": "0",
      "payableAmount": "11900"
    },
    "paymentDescription": {
      "paymentMeans": [
        {
          "paymentMeanId": "IN_CASH",
          "paymentMeanCode": "CO_10"
        }
      ]
    }
  }
}
```

Control aritmético: `2 * 5000 = 10000`; `10000 * 19 % = 1900`; `10000 + 1900 = 11900`.

## Factura estándar con IVA 0 %

No omitir `taxDescription`: se informa IVA con tarifa cero y valor cero.

```json
{
  "document": {
    "organizationalUnitId": "<OU_UUID>",
    "id": {
      "prefix": "<PREFIJO_FACTURA>",
      "number": 12346
    },
    "generalInformation": {
      "currency": "COP",
      "operationCode": "STD",
      "subtypeCode": "SALES_INVOICE"
    },
    "documentLines": [
      {
        "lineId": 1,
        "unitCode": "CO_ZZ",
        "quantity": 1,
        "description": {
          "locale": "ES_CO",
          "text": "Producto con IVA 0 %"
        },
        "itemDescription": {
          "brandName": "Marca de prueba",
          "standardItemId": {
            "id": "SKU-IVA-0",
            "standardId": "TAXPAYER_STANDARD"
          },
          "incomeType": "SELF_OWNED"
        },
        "lineExtensionAmount": "10000",
        "price": {
          "priceAmount": "10000",
          "baseQuantity": 1,
          "unitCode": "CO_ZZ",
          "priceType": "COMMERCIAL_VALUE"
        },
        "taxDescription": [
          {
            "taxName": "CO_01",
            "taxAmount": "0",
            "roundingAmount": "0",
            "taxSubtotal": [
              {
                "taxAmount": "0",
                "percent": 0,
                "taxableAmount": "10000"
              }
            ]
          }
        ]
      }
    ],
    "documentParties": {
      "accountingCustomerParty": {
        "additionalAccountId": "NATURAL_PERSON",
        "personId": {
          "idType": "CC",
          "identifier": "222222222222"
        },
        "personName": {
          "firstName": "Consumidor",
          "firstSurname": "Final"
        },
        "physicalLocation": {
          "address": "Bogotá D.C.",
          "country": "CO",
          "city": "11001"
        }
      }
    },
    "taxDescription": [
      {
        "taxName": "CO_01",
        "taxAmount": "0",
        "roundingAmount": "0",
        "taxSubtotal": [
          {
            "taxAmount": "0",
            "percent": 0,
            "taxableAmount": "10000"
          }
        ]
      }
    ],
    "documentTotals": {
      "lineExtensionAmount": "10000",
      "taxExclusiveAmount": "10000",
      "taxInclusiveAmount": "10000",
      "allowanceTotalAmount": "0",
      "chargeTotalAmount": "0",
      "prePaidAmount": "0",
      "payableAmount": "10000"
    },
    "paymentDescription": {
      "paymentMeans": [
        {
          "paymentMeanId": "IN_CASH",
          "paymentMeanCode": "CO_10"
        }
      ]
    }
  }
}
```

## Nota crédito parcial sobre factura con IVA 19 %

La nota no recibe `organizationalUnitId`. Yabi determina la unidad desde `invoiceToModify.uid`. Antes de construirla, consultar la factura, comprobar `documentUid`, unidad, notas previas y saldo acreditable.

```json
{
  "document": {
    "id": {
      "prefix": "<PREFIJO_NOTA_CREDITO>",
      "number": 12345
    },
    "invoiceToModify": {
      "uid": "<UID_YABI_FACTURA>"
    },
    "generalInformation": {
      "subtypeCode": "CREDIT_NOTE",
      "operationCode": "PARTIAL_REFUND",
      "reasonOfIssuance": {
        "locale": "ES_CO",
        "text": "Devolución parcial de una unidad"
      }
    },
    "documentLines": [
      {
        "lineId": 1,
        "unitCode": "CO_ZZ",
        "quantity": "1",
        "description": {
          "locale": "ES_CO",
          "text": "Devolución de producto gravado IVA 19 %"
        },
        "itemDescription": {
          "brandName": "Marca de prueba",
          "standardItemId": {
            "id": "SKU-IVA-19",
            "standardId": "TAXPAYER_STANDARD"
          }
        },
        "lineExtensionAmount": "5000",
        "price": {
          "priceAmount": "5000",
          "baseQuantity": 1,
          "unitCode": "CO_ZZ"
        },
        "taxDescription": [
          {
            "taxName": "CO_01",
            "taxAmount": "950",
            "roundingAmount": "0",
            "taxSubtotal": [
              {
                "taxAmount": "950",
                "percent": 19,
                "taxableAmount": "5000"
              }
            ]
          }
        ]
      }
    ],
    "taxDescription": [
      {
        "taxName": "CO_01",
        "taxAmount": "950",
        "roundingAmount": "0",
        "taxSubtotal": [
          {
            "taxAmount": "950",
            "percent": 19,
            "taxableAmount": "5000"
          }
        ]
      }
    ],
    "documentTotals": {
      "lineExtensionAmount": "5000",
      "taxExclusiveAmount": "5000",
      "taxInclusiveAmount": "5950",
      "allowanceTotalAmount": "0",
      "chargeTotalAmount": "0",
      "prePaidAmount": "0",
      "payableAmount": "5950"
    },
    "paymentDescription": {
      "paymentMeans": [
        {
          "paymentMeanId": "IN_CASH",
          "paymentMeanCode": "CO_10"
        }
      ]
    }
  }
}
```

Control aritmético: se acredita una de las dos unidades de la factura ejemplo; base `5000`, IVA `950`, total `5950`.

## Anulación total

`voidInvoice` crea una nota crédito de anulación; no elimina ni modifica la factura original. No recibe `organizationalUnitId`; la unidad se deriva de `invoiceToVoid.uid`.

```json
{
  "document": {
    "id": {
      "prefix": "<PREFIJO_NOTA_CREDITO>",
      "number": 12347
    },
    "invoiceToVoid": {
      "uid": "<UID_YABI_FACTURA>"
    },
    "reason": {
      "locale": "ES_CO",
      "text": "Anulación total autorizada de la factura"
    }
  }
}
```

Antes de enviar, comprobar que la factura está validada, pertenece a la empresa y ambiente esperados, no tiene una anulación previa y no presenta eventos incompatibles. Usar un consecutivo nuevo del prefijo de nota crédito.

## Consultar y recuperar PDF/XML

La consulta funciona tanto para `invoice` como para `creditNote`:

```graphql
query InvoiceFiles($uid: UID!) {
  invoice(uid: $uid) {
    uid
    id
    documentUid
    documentStatus { code description }
    files {
      attachedDocument { filename fileType data }
      graphicalRepresentationHtml { filename fileType data }
      graphicalRepresentationPdf { filename fileType data }
    }
  }
}
```

- `attachedDocument.data` contiene el XML adjunto en Base64.
- `graphicalRepresentationPdf.data` contiene el PDF en Base64.
- `graphicalRepresentationHtml` puede ser nulo.
- Decodificar solo en backend. Comprobar `fileType`, nombre seguro, tamaño máximo y firma real del contenido (`%PDF-` para PDF y XML bien formado) antes de almacenarlo.
- No registrar Base64, XML, PDF ni datos personales.
- La presencia del PDF no sustituye la comprobación de `documentUid` y estado DIAN.

Ejemplo Node.js de decodificación en memoria:

```js
const pdf = Buffer.from(document.files.graphicalRepresentationPdf.data, "base64")
if (!pdf.subarray(0, 5).equals(Buffer.from("%PDF-"))) {
  throw new Error("Yabi devolvió una representación PDF inválida")
}
```

## Selección de la mutación

Usar las mutaciones de [graphql-operations.md](graphql-operations.md) con estos objetos en `variables.document`. No interpolar el JSON dentro del documento GraphQL. Antes de considerar éxito, evaluar HTTP, errores GraphQL superiores, `result.errors`, advertencias, notificaciones y luego conciliar por `uid`.
