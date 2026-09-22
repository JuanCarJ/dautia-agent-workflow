# Execution profiles · GPT-6

La fuente canónica es `../config/routing-policy.json`. Principal: GPT-6 Sol medium.
Un override de esta conversación no cambia el default del host ni el de los hijos.
Los perfiles son un punto inicial; la aceptación y permisos son comunes a todos.

## Matriz de entrada

| Rol | Perfil inicial | Criterio para otra selección |
|---|---|---|
| principal | sol_medium | high si la coordinación/análisis realmente lo requiere |
| code_explorer | luna_high | sol_medium/high para contratos o dependencias difíciles |
| product_discovery | sol_medium | astra_low ante decisiones importantes contradictorias; medium si la incertidumbre transversal lo exige |
| systems_analyst | astra_low | medium para alternativas transversales especialmente difíciles |
| implementer | sol_medium | high para ejecución exigente con decisiones resueltas |
| implementer_complex | sol_high | xhigh solo con autorización explícita vigente |
| systems_implementer | sol_high | si se descompone en bloques rutinarios, usar implementer |
| ux_auditor | astra_low | medium para juicio UX/arquitectura de información especialmente difícil |
| independent_reviewer | sol_medium | high para lógica/contratos/migraciones y regresiones complejas |
| data_security | sol_high | consulta Astra low/medium si aporta; solo petición explícita, solo lectura |
| decision_gate | sol_high | consulta Astra medium para alternativas transversales materialmente riesgosas |
| documental | sol_medium | luna_high para extracción/inventario; Astra low para contradicciones sustantivas |
| qa_web, qa_ios, qa_android, qa_e2e | sol_medium | high por estados, concurrencia, lifecycle o recorridos complejos |
| release_operator | sol_medium | high para reconciliación operativa excepcional |

No invocar todos los roles para cada tarea. Una consulta breve queda con el
principal. `systems_analyst`/`ux_auditor` entran cuando hay una pregunta analítica
sustantiva; su nombre no demuestra que esa pregunta exista. Sol también resuelve
trabajo ambiguo y complejo. No añadir una consulta Astra para ratificar cada paso.

## Preparación y selección

Para escritores de producto/tests, declarar `decisions_resolved: true` y
`execution_difficulty: routine|demanding|unknown`. Unknown bloquea el despacho hasta
clasificar la ejecución; decisiones abiertas vuelven al análisis pertinente.
El bloque rutinario usa su perfil de entrada; demanding requiere Sol high. Usar
`implementer` para un bloque rutinario, no inflar el rol por tamaño del proyecto.

Luna high solo participa en exploración/documentación acotada, con salida definida,
sin producto ni operaciones externas. Astra low/medium solo análisis. La limitación
es una política de DautIA, no una incapacidad de esos modelos. No rebajar revisiones,
pruebas, aceptación o permisos por seleccionar un perfil más económico.

`runtime.principal_choice` selecciona entre perfiles elegibles con evidencia.
Un fallo no provoca una escalera automática: distinguir contexto incompleto,
hipótesis refutada, herramienta/proveedor y dificultad del razonamiento.
Sol xhigh exige `explicit_override` de usuario; no habilitar max/ultra ni Astra
por encima de medium. Ausencia/capacity no autoriza sustitución silenciosa.

## Generación y despacho

El generador deriva los TOML base y `ROLE__PROFILE` de política y perfil del host.
No escoger el modelo por una declaración del propio agente. El TOML personalizado
puede tener prioridad sobre el modelo solicitado: comprobar definición y ejecución.

```sh
dautia-workflow dispatch-plan PACKET --agents-dir CODEX_HOME/agents --cwd WORKSPACE
```

Preparar el packet, usar el destino exacto, `fork_turns: "none"` y contexto suficiente:
aceptación, alcance, fuentes, candidato, entorno y dependencias resueltas. No pasar
el historial completo ni crear nietos. Conservar `runtime.required_agent_type` y
recibo terminal con perfil observado, referencia del hijo y evidencia. Genérico,
perfil distinto o hijo incompleto bloquean cierre; no reemplazarlos por trabajo
propio del principal. Un callback que repite la petición no prueba enforcement.

Conservar modelo completo, esfuerzo, revisión/hash de política y procedencia de
observación. Un antiguo `sol_medium` no equivale a GPT-6 Sol medium. La configuración,
la petición, el contexto observado y el resultado aceptado son afirmaciones distintas.
No modificar sesiones activas para hacerlas coincidir con los nuevos defaults.

## Skills y evidencia

Las skills conservan método, autoridad y aceptación compartidos. No crear copias
por modelo. Las diferencias de prompting, si aportan, deben cargarse explícitamente
por configuración comprobada; cambiar el modelo no cambia automáticamente las skills.
Leer solo referencias pertinentes. Conservar comandos de prueba y guardas de entorno.
En UI, verificar significado/contenido visible y diseño preservado, también para
cambios focales. Un test verde o captura sin interpretación no prueba el requisito.

## Adopción

Comparar primero 5.6/6 con esfuerzo comparable y luego medium/high de GPT-6, con
aceptación y fixtures congelados. Replays de decisiones no son benchmarks de producto.
Medir correcciones, defectos, tiempo y uso de raíz+hijos; unknown no es cero.
Fuentes: https://learn.chatgpt.com/docs/models y
https://developers.openai.com/codex/agent-configuration/subagents.
