# Execution profiles · routing r3.2

La política canónica está en `../config/routing-policy.json`. El principal permanece
`gpt-5.6-sol/high`. El implementador usa `gpt-5.6-sol/medium` únicamente cuando el
bloque está definido, las decisiones están resueltas y la ejecución es rutinaria.
La ejecución exigente o desconocida usa Sol high.

## Preparación e implementación

Para `implementer`, `implementer_complex` y `systems_implementer` que escriben
producto o tests, el handoff debe declarar `work.decisions_resolved: true` y
`work.execution_difficulty` como `routine`, `demanding` o `unknown`.

- La ejecución rutinaria y definida puede usar Sol medium.
- La ejecución demanding usa Sol high sin downgrade automático.
- La dificultad unknown usa Sol high como fallback.
- Decisiones de producto o arquitectura abiertas vuelven a análisis; no se resuelven
  aumentando el esfuerzo del escritor.

## Análisis y Astra

Los roles analíticos pueden usar Sol high, Astra low o Astra medium cuando el
principal aporta evidencia y el alcance justifica el coste. Astra nunca escribe
producto ni ejecuta operaciones externas bajo esta política. No se elige por nombre
del rol, número de archivos, marca o sensibilidad.

`runtime.principal_choice` permite seleccionar un perfil ordinario elegible con
referencias de evidencia. No es una aprobación, no cambia la autoridad y no prueba
que el host haya cargado el modelo.

Perfiles explicit-only, como Sol xhigh, requieren un override explícito del usuario
ligado a sus referencias. El techo de Astra es medium. La disponibilidad observada,
los perfiles denegados, capacidades y presupuesto se validan antes del dispatch.
Nunca se hace un downgrade silencioso ni se inventa un perfil disponible.

## Generación y dispatch

El generador valida los defaults de cada host y crea nombres cualificados
`ROLE__PROFILE`. Las variantes de Astra solo se generan para roles analíticos. Una
variante es configuración, no un agente ejecutándose ni un supervisor adicional.

```sh
dautia-workflow dispatch-plan PACKET --agents-dir CODEX_HOME/agents --cwd WORKSPACE
```

El comando valida el packet, selecciona el perfil local, enlaza la decisión al
contexto y política, y comprueba el TOML exacto. El principal debe invocar ese
`agent_type` con el mismo handoff. El callback nativo debe registrar el perfil
reportado; un archivo generado no prueba runtime efectivo.

`workflow_dispatch.dispatch_prepared` consume una sola vez el callback del host,
separa perfil solicitado/configurado/reportado y exige reconciliación ante un
resultado incierto. No reintenta automáticamente y no usa red ni otro proveedor.

## Evaluación

La calidad se evalúa con tareas comparables, esfuerzo total aceptado, regresiones,
tiempo, intervención humana y resultado real. Los conteos de tests o una opinión
de un modelo no son ground truth. Las skills aportan método; esta política decide
el perfil y no modifica autoridad ni aceptación.
