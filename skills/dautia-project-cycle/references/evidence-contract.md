# Contrato de evidencia y contexto de proyecto

Este contrato aporta una entrada recuperable para discovery, auditoría,
implementación y release. No concede autoridad, no certifica una entrega y no
sustituye la aceptación del proyecto. Un registro describe lo que se observó,
su fuente y sus límites; una propuesta o una inferencia no se debe presentar
como observación externa.

## Registro mínimo

Cada observación se guarda como JSON acotado con estos campos:

```json
{
  "schema_version": 1,
  "evidence_id": "obs-ryven-maps-001",
  "objective_id": "RY-RF-006",
  "project_id": "sidequest",
  "stage": "audit",
  "source_kind": "simulator",
  "source_ref": "simulator-run-20260921-01",
  "observed_at": "2026-09-21T14:30:00Z",
  "candidate_sha": "abc1234",
  "acceptance_hash": "def5678",
  "observation": "La cámara no se centra al cambiar el destino.",
  "status": "observed",
  "strength": "E3",
  "supports": ["finding-map-camera-001"],
  "contradicts": [],
  "metadata": {"device": "simulator"}
}
```

`evidence_id` (también se acepta el alias `id` en integraciones existentes),
`objective_id`, `project_id` y las referencias a requisitos son
identificadores; no deben contener secretos ni transcripciones. Los hashes de
candidato y aceptación vinculan una observación a una versión concreta cuando
se conocen. Si todavía no existen se usa explícitamente `"unknown"`, no se
inventa un hash. `source_ref` debe ser una referencia recuperable (run, ruta,
artefacto o expediente), no una copia completa de logs.

El validador en
[`scripts/evidence_contract.py`](../scripts/evidence_contract.py) normaliza
espacios, etapas y estados, limita el tamaño de texto/listas y rechaza valores
con forma de credencial. Se puede usar con una función o desde CLI:

```sh
python3 skills/dautia-project-cycle/scripts/evidence_contract.py evidence evidence.json
python3 skills/dautia-project-cycle/scripts/evidence_contract.py project-context context.json
cat evidence.json | python3 skills/dautia-project-cycle/scripts/evidence_contract.py evidence -
```

La salida contiene `valid`, `errors`, `warnings` y el registro normalizado. Un
error estructural devuelve código de salida distinto de cero. Un warning no
autoriza a cerrar el objetivo: el gate correspondiente decide si falta esa
frontera.

## Fuerza y estado

La fuerza describe la naturaleza de la fuente, no la confianza subjetiva del
agente:

| Nivel | Fuente | Puede demostrar |
| --- | --- | --- |
| E0 | Afirmación del usuario, intención o contexto | Qué se pidió o qué se espera |
| E1 | Código, spec, configuración, manifiesto o hash | Consistencia del candidato local |
| E2 | Test automatizado, build o análisis reproducible | Comportamiento cubierto por esa prueba |
| E3 | Browser, simulador, dispositivo, proveedor o servidor | Observación fuera del código |
| E4 | Revisión independiente y readback posterior | Dictamen del head y estado entregado |

`observed`, `inferred`, `proposed`, `superseded` y `contradicted` distinguen la
naturaleza del registro. `unknown` e `in_progress` son estados válidos: generan
un warning `evidence_state_incomplete` y mantienen visible el límite. Nunca se
convierten en `passed`, `verified` o `accepted` por defecto.

Si la fuerza aún no se puede clasificar, `strength: "unknown"` también es válido
y genera `evidence_strength_unknown`; no se debe elevar a E1--E4 sin observar la
fuente correspondiente.

## Contexto de proyecto

Cada objetivo puede referenciar un manifiesto pequeño, separado de `AGENTS.md`
y de la especificación de producto:

```json
{
  "schema_version": 1,
  "project_id": "sidequest",
  "documentation_status": "partial",
  "repositories": [
    {"name": "ios", "path": "...", "integration_branch": "dev"},
    {"name": "admin", "path": "...", "integration_branch": "main"}
  ],
  "components": ["ios", "admin", "database"],
  "environments": ["local", "staging", "testflight", "production"],
  "providers": ["supabase", "apple", "vercel"],
  "canonical_sources": {
    "product_spec": "docs/specs/",
    "acceptance": "docs/acceptance/",
    "release": "docs/releases/"
  },
  "notes": "El mapa de dependencias se completa durante discovery."
}
```

El único requisito bloqueante del manifiesto es `project_id`. `repositories`,
`components`, `environments`, `providers` y `canonical_sources` pueden estar
vacíos mientras el proyecto sea scratch o la documentación esté en curso. El
validador devuelve `context_incomplete` y warnings por secciones ausentes para
que discovery los convierta en trabajo pendiente. No rechaza
`documentation_status: "scratch"`, `"partial"`, `"unknown"` o
`"in_progress"`.

El manifiesto se interpreta para el alcance activo de la tarea. Si un proyecto
tiene varios frentes, `active_workstream` identifica el registro correspondiente
en `workstreams`; así una parte funcional documentada puede cerrarse mientras
una demo separada conserva estado `scratch` o `in_progress`. Si no se declara
un frente activo, se usa `documentation_status` del proyecto completo.

El manifiesto no reemplaza reglas locales, contratos de API, runbooks,
credenciales ni fuentes canónicas. Solo indica dónde buscar y qué fronteras
pueden verse afectadas. Una ruta desconocida se conserva como `"unknown"` hasta
que se observe, sin fabricar una ruta de repositorio.

## Uso por etapa

- **Discovery:** registrar E0/E1 y el manifiesto, declarar desconocidos y
  decisiones abiertas. No usar una afirmación como prueba de comportamiento.
- **Audit/diagnosis:** añadir hipótesis, predicción y observación separadas;
  enlazar E2/E3 y conservar evidencia negativa o contradictoria.
- **Implementation:** vincular cada cambio a `candidate_sha`, aceptación y
  checks. El agente entrega evidencia, pero no se autoaprueba.
- **Release:** exigir la frontera que corresponda al riesgo, revisión
  independiente (E4), artefacto y readback del ambiente. Merge, deploy,
  TestFlight y promoción siguen siendo estados distintos.

En proyectos scratch se mantiene el mismo esquema, pero el cierre queda
`in_progress` o `pending` hasta completar la sección necesaria. La ausencia de
documentación no se tapa con un build verde; se registra como pendiente y se
continúa únicamente con el trabajo independiente autorizado.

## Comparación y calibración

Las comparaciones de perfiles se realizan fuera del contrato de ejecución, con casos
equivalentes, aceptación independiente y resultados observados. Una ausencia de
etiqueta, prueba o perfil efectivo permanece desconocida; no se trata como cero.
La telemetría del workflow informa selección, dispatch, revisión, regresiones y
residuos, pero no autoriza acciones ni convierte un modelo en ground truth.
