# Implementación del plan r3 — candidato 15.0.0-rc1

Base inspeccionada: 720248e39c01093b76037de2ed9edfaae551f8c0. Cambios de workflow,
no de SideQuest, otros productos o hosts. No hay prueba con modelos reales, API
Jev, SSH, despliegues o Codex Desktop en esta implementación local.

## Componentes implementados

- workflow_core: consistencia de packets, permisos declarados, normativa/cambios,
  contexto/fuentes/skills, impacto, diagnóstico, oráculos, revisión, dependencia,
  candidato y cierre. La semántica y la procedencia real siguen requiriendo lectura
  e inspección; un JSON no autentica una aprobación ni entiende código por sí solo.
- workflow_cli/store: frontera explícita, vínculo de raíz, adaptador de hooks
  acotado, leases cooperativos por recurso/generación, eventos de metadatos y export
  deduplicado. Sin supervisor nuevo ni permisos remotos implícitos.
- jev_support: cliente HTTP directo, preguntas Choice para ocho fronteras, setup,
  privacidad, presupuesto, caché e invalidación. Off por defecto, shadow reversible,
  aplicación selectiva requiere capacidad/destino verificados. El selector no crea
  trabajadores: entrega el destino que el principal debe invocar y correlacionar.
- workspace_audit: snapshot/reconciliación de lectura, estado propio/ajeno, sin
  git clean/reset/stash/add. No declara descartable ningún worktree.
- audit_ingest: valida estructura e integridad de ZIP futuros sin extraer/ejecutar.
  No certifica la verdad o privacidad semántica del contenido ni ordena limpieza.
- skill_catalog: descripciones frontmatter correctas y colisiones por procedencia;
  discovery no se etiqueta como carga/uso del agente.
- delivery_v3: ramas por repo y destinos por componente; wrappers preservan los
  validadores/operadores originales para contratos anteriores.
- generación/instalación: roles canónicos y boundary común, principal y roles
  analíticos con Sol high; implementadores definidos usan Sol medium para trabajo
  rutinario y high cuando la dificultad lo exige. Las variantes Astra son
  analíticas hasta medium; Astra high queda bloqueado por la política vigente
  aunque exista una definición heredada. Sin copias derivadas
  versionadas que se puedan quedar obsoletas. Preview, conflictos, backup,
  reversión y paths Mac/WSL/codex personalizados; no activa hooks ni sesiones.

## Telemetría y límites

Se añade el stream r3 a la observabilidad existente, no se sustituye ni reimplementa
el contador de sesiones dautia_cycle_telemetry.py. Este mantiene ventanas, epochs y
atribución de tokens. export conserva la referencia/hash del snapshot legado y no
vuelve a sumarlo. La correlación nativa y la exportación conjunta semántica completa
requieren el smoke del host; no están demostradas por mocks de eventos.

El código no convierte receipt/booleano del implementer en prueba externa. Comprueba
consistencia entre artefactos suministrados; la honestidad del emisor/procedencia se
complementa con reviewer y herramientas. No elimina la posibilidad de un agente
que no ejecute la comprobación; por eso los hooks permanecen candidatos hasta
verificar cobertura, confianza y permisos en el host.

## Lo que permanece pendiente

La auditoría Git local aún no llegó: su ingesta está disponible, su recuperación
puntual no se ha decidido ni ejecutado. También faltan revisión independiente del
candidato, integración del PR, piloto App/CLI y permisos QA, medición real Sol/Astra,
probe autenticado de Jev, calibración/activación selectiva e instalación en el Mac/WSL.
El catálogo de 52 escenarios es una aceptación de plan, no 52 agentes ejecutados.
`conformance/r3/implementation-status.json` separa esas fronteras por cambio.

## Verificación local del candidato

Pruebas locales stdlib unittest y repositorios temporales, mocks HTTP tipados,
instalaciones de fixture con espacios/CODEX_HOME/WSL, rechazo de symlinks, rollback,
conflictos y pausa. La batería completa actual ejecuta 105 pruebas y termina en OK;
el aplicador aislado ejecuta 11 pruebas y termina en OK. Portabilidad, render de los
perfiles Codex/WSL y `git diff --check` también pasan. Durante la integración se
detectó y corrigió la compatibilidad de los alias legítimos `/var` y `/tmp` de macOS
sin relajar el rechazo de symlinks externos. El preview/apply/check del instalador se
probó en un HOME temporal preservando una tabla de configuración ajena y produciendo
un backup transaccional. El archivo CI propuesto comprueba la fuente completa y hashes
de módulos legados preservados; CI remoto y el comportamiento de un agente real aún
requieren el head publicado. No hay secretos ni fuentes de producto copiadas a estos
fixtures.

## Estado de publicación antes del PR

El overlay está aplicado en la rama aislada `feat/r3-integrated`, basada en el
baseline exacto, y queda listo para commit y revisión independiente. Todavía no se
ha abierto el PR ni se ha fusionado `main`; la instalación real en el host, el smoke
del launcher y cualquier piloto nativo se mantienen deliberadamente pendientes hasta
obtener el SHA integrado. Jev sigue `off` y los hooks permanecen como candidato sin
confianza. El paquete ZIP original y el backup del aplicador se conservan fuera del
checkout.
