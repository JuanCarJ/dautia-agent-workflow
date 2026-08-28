# Operaciones GraphQL mínimas

Usar variables; no interpolar datos ni secretos en el documento GraphQL.

## Verificar unidad de pruebas

```graphql
query OrganizationalUnit($id: UID!) {
  organizationUnit(id: $id) {
    organizationalUnitId
    unitName
    unitNit
    unitSettings { environment }
    unitState { active }
  }
}
```

## Crear factura

```graphql
mutation CreateInvoice($document: InvoiceInput!) {
  createInvoice(document: $document) {
    document {
      uid id documentUid assessmentState dianState
      documentStatus { code description }
      updatedAt
    }
    errors { id type subType title message helpText language }
    warnings { id type subType title message helpText language }
    notifications { id type subType title message helpText language }
  }
}
```

## Crear nota parcial

```graphql
mutation CreateCreditNote($document: CreditNoteInput!) {
  createCreditNote(document: $document) {
    document {
      uid id documentUid assessmentState dianState
      documentStatus { code description }
      updatedAt
    }
    errors { id type subType title message helpText language }
    warnings { id type subType title message helpText language }
    notifications { id type subType title message helpText language }
  }
}
```

## Anular factura

```graphql
mutation VoidInvoice($document: VoidInvoiceInput!) {
  voidInvoice(document: $document) {
    document {
      uid id documentUid assessmentState dianState
      documentStatus { code description }
      updatedAt
    }
    errors { id type subType title message helpText language }
    warnings { id type subType title message helpText language }
    notifications { id type subType title message helpText language }
  }
}
```

## Consultar documentos

```graphql
query Invoice($uid: UID!) {
  invoice(uid: $uid) {
    uid id documentUid assessmentState dianState
    documentStatus { code description }
    files {
      attachedDocument { filename fileType data }
      graphicalRepresentationHtml { filename fileType data }
      graphicalRepresentationPdf { filename fileType data }
    }
    insertedAt updatedAt
  }
}

query CreditNote($uid: UID!) {
  creditNote(uid: $uid) {
    uid id documentUid assessmentState dianState
    documentStatus { code description }
    files {
      attachedDocument { filename fileType data }
      graphicalRepresentationHtml { filename fileType data }
      graphicalRepresentationPdf { filename fileType data }
    }
    insertedAt updatedAt
  }
}
```

`files.*.data` es contenido Base64, no una URL. Decodificarlo en backend, validar `fileType` y la firma del archivo antes de persistirlo o servirlo. No registrar el contenido.

## Envelope y evaluación

Enviar `POST <YABI_API_URL>` con bearer, JSON `{ query, variables, operationName }` y timeout explícito. Redactar token, PII y payload fiscal.

Evaluar en orden:

1. HTTP;
2. `body.errors`;
3. resultado de la operación;
4. `result.errors`, warnings y notifications;
5. presencia de `document.uid` antes de confirmar;
6. conciliación posterior por UID.

No reintentar una mutación desde el manejador de error sin descartar creación remota.
