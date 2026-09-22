# Rutas por resultado · v13

Consultar solo al elegir una familia de tarea. Esto no agrega modalidades: siguen
Descubrimiento, Auditoria, Implementacion y Release. Mantener un solo objetivo,
candidato y evidencia al combinar rutas. [Modelos](model-routing.md) fija perfiles;
[revision](audit-evidence.md) fija el bucle de codigo. No cargar un catalogo completo.

| Peticion | Recorrido y criterio de salida |
|---|---|
| Consulta/estado | Leer evidencia focal y responder; sin implementar ni crear agentes por ceremonia. Estado externo exige fuente actual o limite explicito. |
| Descubrimiento | Frase fuente -> actor/resultado -> decisiones/aceptacion candidatas; no convertir ideas en requisitos aprobados. |
| Auditoria funcional/UX/seguridad | Aceptacion y candidato -> evidencia original -> delta/To-Be/plan. UX juzga tarea/jerarquia/recuperacion; QA prueba comportamiento; seguridad prueba fronteras plausibles. No son equivalentes ni autorizan arreglos por si solas. |
| Prototipo/implementacion inicial | Hipotesis o primer resultado util -> contratos minimos -> corte vertical -> evidencia. Resolver solo interfaces necesarias; no arquitectura completa ni equipo universal. Distinguir mock/prototipo de producto operativo. |
| Feature/cambio definido | Mapear impacto -> implementer con el perfil de la politica vigente para bloque independiente resuelto con trabajo concurrente util -> comprobar comportamiento nuevo y recorrido previo afectado -> revision/integracion autorizada. Sin discovery o redesign cuando ya esta resuelto. |
| Regla de negocio/API | Decidir semantica vigente y consumidores -> compatibilidad -> cambios ordenados -> positivos/negativos -> spec actualizada. No inventar permisos/precios/taxonomia. |
| Bug/RCA/CI | Reproducir -> comparar camino fallido y sano -> hipotesis falsable -> fix/regresion si autorizado. Diferenciar producto, test, fixture y runner; no debilitar aserciones para fabricar verde. |
| Refactor/upgrade | Invariantes/compatibilidad -> delta acotado -> checks afectados. No cambiar producto por limpieza ni suites universales. Versiones y guias oficiales se verifican al ejecutar. |
| Performance/costo | Baseline/carga/calidad a preservar -> cuello o gasto atribuible -> cambio autorizado -> comparacion y regresion. Sin mejora proclamada por intuicion ni costo de plan inferido de tokens. |
| QA/E2E/movil | Actor/recorrido/ambiente/fixtures/proveedores permitidos -> evidencia por frontera. Fakes para regresion amplia; smoke real focal. Una plataforma no prueba otra. |
| Auth/datos/integracion | Actores/tipos/estados -> idempotencia/errores -> permitido/denegado -> persistencia/cola/proveedor separados. Pruebas DB solo staging verificado; falta de staging bloquea esa frontera, no lo puro. |
| Checklist staging -> main/produccion | Preparar/verificar readiness del candidato segun [revision](audit-evidence.md): auditoria independiente vigente, pruebas por impacto, checks y recuperacion. Entregar listo/bloqueado/pendiente con evidencia; pedir checklist no ordena merge ni deploy. |
| Migracion/release/cutover | Candidato/target/autoridad -> compatibilidad/recuperacion -> orden de proveedores -> readback/postflight. PR de migracion no autoriza apply; mirror no equivale a cutover. |
| Incidente | Impacto -> primera falla -> contencion autorizada -> recuperacion util -> RCA residual. Contencion sin codigo no espera PR ficticio; hotfix de codigo conserva revision focal. |
| Manual/documento/lote | Entrada y universo -> transformacion/operacion autorizada -> artefacto y excepciones -> readback. Preservar originales y campos reservados; muestra no equivale a lote completo. Codigo reusable asociado sigue revision. |
| OpenClaw | Orientacion viva -> capas pertinentes hasta primera falla -> reparacion autorizada -> prueba tecnica y resultado de negocio. Usar su skill, no copiar el runbook aqui ni recorrer siempre todas las capas. |
| Specs/contratos | Conservar fuente canonica, decisiones y autoridad. delivery guarda mapa estable; CURRENT/proveedor estado mutable. Contrato comercial se valida como documento; no confiere firma/envio ni sustituye asesoria legal solicitada. |
| Hilo largo/reactivacion | Reconciliar aceptacion/candidato/autoridad/evidencia -> marcar reemplazado -> continuar delta. Resolver repo/host/contrato real; no inventar dev/staging ni crear archivos por turno. |
| Workflow/skills | Casos reales -> causa -> delta minimo -> pruebas proporcionadas. Reusar skills/roles antes de crear; configurado no significa invocado. |

## Adaptadores del proyecto

Antes de actuar, leer las reglas reales del repo/target. Una rama puede integrar
staging, main puede ser demo, otro proyecto puede carecer de staging o prohibir
ramas cortas. No convertir esos ejemplos en nuevos defaults globales. Resolver la
topologia necesaria al reactivar; no crear contratos para carpetas inactivas.
Supabase/Apple/hosts conservan [infraestructura](infrastructure.md); no trasladar
identidades, credenciales, wrappers o autoridad entre productos.

## Operaciones y artefactos

El dueño verifica entrada/fuente, objeto/canal/destino, efectos permitidos, resultado
util y excepciones. Ante una operacion incierta no idempotente, reconciliar antes
de repetir. Config viva, cron, media, PDF/Excel y operaciones en consolas no generan
PR; codigo/config de producto versionado si. Snapshot de estado no programa monitor.
Recurrencia, envios a terceros, publicacion y efectos externos requieren intencion
vigente; preparar todo el trabajo independiente antes de pedir la decision faltante.
