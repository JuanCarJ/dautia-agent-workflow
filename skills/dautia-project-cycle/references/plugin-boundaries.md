# Limites de plugins en DautIA · v9

Adaptacion mantenida fuera del cache administrado. Leer solo la familia usada;
las instrucciones de AGENTS y la intencion vigente prevalecen sobre recetas de
skills. Preservar requisitos reales de API y capacidades; no cargar paquetes
enteros ni inventar permisos. Una actualizacion puede requerir volver a revisar
la familia; el inventario no demuestra salud de MCP.

| Familia | Aplicacion en DautIA |
|---|---|
| Supabase | Identidad y wrapper DautIA, DB staging; MCP solo lectura, no psql/DB local/fallback de credencial. Ver infrastructure.md. |
| Vercel marketplace/bootstrap/knowledge-update | Solo repos que dependen de Vercel y proveedor decidido. No aprovisionar Shopify/Stripe/DB/Gateway por defecto. Linking/env pull no debe sobrescribir configuracion ajena. |
| Vercel AI SDK/elements/gateway/persistence | Preservar arquitectura, proveedor, libreria UI y politica de datos. No Radix/Gateway/agente/almacenamiento universal; elegir por necesidad. Version mas reciente no prueba mejor resultado. |
| Vercel auth/payments | Clerk/Auth0/Descope o Stripe cuando sean el proveedor del proyecto; auth o pago generico no reemplazan Supabase/Bold/Wompi. |
| Vercel investigation/verification/observability | Frontera concreta, evidencia vigente y parada; no arrancar coordinacion por frustracion, dev server o conteos. Drains, suites y waits solo si prueban riesgo pertinente. |
| Vercel shadcn/satori/firewall/storage | Conservar base UI/runtime; instalar/provisionar solo en alcance. Usar interfaz soportada para regla autorizada sin gate humano inventado. |
| Figma | Usarlo por referencia o resultado Figma; SwiftUI o diagrama generico no lo activan. Mantener prerequisitos reales de las llamadas, no cuotas/fases universales. Componente aislado no implica publicar libreria. |
| Canva | Edicion autorizada no exige reconfirmacion rutinaria. Editar no autoriza responder comentarios a terceros. Resolver mapping/marca desde contexto cuando inequívoco; aclarar ambiguedad material. |
| Notion | Lectura/investigacion no autoriza publicar paginas o crear tasks; capturar solo cuando pedido. No convertir implementacion en proyecto Notion por defecto. |
| Sites / Superdesign / Creative / Appllama | Adoptar herramienta por resultado real. No cuotas de referencias, agentes obligatorios, WebMCP, video ni hosting fuera de alcance. |
| Artefactos / visualize | Preservar datos, formato y comunicacion. Verificacion visual por delta y al cierre; no por cada micromutacion. |

No desinstalar una integracion por no aparecer en una muestra. Duplicados locales
se deshabilitan por config, conservando recursos recuperables. No modificar caches
administrados como solucion durable ni crear copias de cada plugin. Para necesidad
que no satisfaga estos limites, estrechar/deshabilitar la skill con configuracion
soportada antes de adoptar una capacidad propia; no silenciar su API necesaria.
