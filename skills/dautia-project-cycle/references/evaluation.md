# Evaluacion y adopcion · v13

Para evaluacion solicitada usar dautia-workflow-evaluation: scripts/run_replay.py
compara casos sanitizados con el CLI Codex real. El piloto inicial prueba decisiones
de contrato; no sustituye un benchmark de implementacion ni atribuye fallos historicos
a un modelo. Casos: copy, auditoria de mirror, staging ausente, transaccion incierta,
linaje visual, paridad movil, proveedor y handoff.

Para comparar implementaciones reales: mismo baseline y fixtures/aceptacion, salida
anonimizada para revision independiente, frontera funcional/visual y mismo presupuesto
de operaciones. Medir aceptacion, defectos escapados, correcciones, minutos humanos,
tiempo y consumo por tramo/perfil (raiz + hijos + handoff). Valores no observados son
unknown; segmentar resets y ventanas. Tokens de razonamiento ya pertenecen a salida.
No interpretar precio API como credito de cuenta. Un resultado verde aislado no prueba
superioridad de esfuerzo. Empezar con pocos casos; ampliar solo incertidumbres decisivas.

El recolector de project-cycle se documenta en observability.md; no es gate ni fase.
No activar una automatizacion sin cadencia solicitada. Sol high es la base habitual provisional; no implica mejora medida.
Version nueva se carga en
sesiones nuevas; antes de mutacion externa desde una tarea previa, reconciliar contrato.

## Evidencia historica v11

Astra low y Sol xhigh no participaron en el piloto inicial. Un replay verde solo
prueba su contrato de respuesta y routing, no calidad UI ni implementacion. No
extrapolar a producto. Comparar artefactos con aceptacion y baseline iguales,
revision sin etiqueta de modelo cuando viable y casos reservados. Comparaciones:
Sol medium/high (ejecucion definida), Astra low/medium (juicio focal),
Sol high/xhigh/Astra low (logica profunda), Astra medium directo/handoff (acoplado).
No correr todas las combinaciones ni duplicar pagos/despliegues reales. Si cambia
la rubrica, preservar resultados originales y regraduar todos por igual.
La cuota global concurrente no atribuye consumo por tarea. Separar tiempo humano,
herramientas y espera; distinguir omisiones de nuevas decisiones del usuario.

## Aceptacion de adopcion vigente

Separar replay de decisiones, prueba de resolucion de roles y simulacion real con
herramientas/artefactos. El replay read-only deshabilita subagentes por diseño;
no prueba despacho. Las simulaciones deben verificar parentesco y turn_context
propios y perfil al producir respuestas con consumo, artefacto/aceptacion,
regresion focal y ausencia de mutaciones externas. Un contexto de inicializacion
sin respuesta no demuestra ejecucion con ese esfuerzo.
Los catalogos/resultados v11/v12 son historicos: para v13 congelar una rubrica
nueva con product_discovery Astra low e implementer Sol medium para el bloque
resuelto. No usar sus expectativas antiguas para diagnosticar una violacion v13
ni modificar retrospectivamente resultados originales. Despacho forzado no
demuestra seleccion autonoma; explicitar cual de los dos se esta midiendo.
Incluir casos simples sin delegacion, cambio de fase y correcciones materiales.
No dar expected answers al ejecutor; congelar rubrica, conservar fallos originales
y exigir casos negativos (hijo ausente, perfil distinto, requisito omitido).

Revisar las siguientes diez implementaciones no triviales cuando se solicite o
se este trabajando en ellas; no crear monitor automatico sin cadencia autorizada.
Cada incumplimiento queda abierto hasta corregirse; exitos ajenos no lo compensan.
Cero incumplimientos conocidos en una muestra no garantiza ausencia universal.
