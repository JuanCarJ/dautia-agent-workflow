# Guia global para agentes

Contrato v13 — 2026-09-07.

Prevalecen la instruccion del usuario y el AGENTS.md mas cercano. Las skills
complementan: no conceden autoridad ni agregan fases, documentos o agentes.

## Intencion, autoridad y limites

Conservar el resultado que busca el usuario y sus exclusiones durante todas las
iteraciones. No destruir datos, filtrar secretos, inventar estado externo ni
revertir cambios ajenos. Produccion, deploy, migracion remota y upload requieren
intencion clara al target. Una autorizacion vigente no se pide de nuevo.

Una implementacion de codigo de producto incluye pruebas, verdad relevante,
commit/push y PR segun reglas reales: autor -> revision independiente -> correcciones
del autor -> dictamen del head final -> merge a integration_branch con autoridad
vigente. Si se pidio ver el informe antes, esperar ese go; no pedirlo de nuevo si
la integracion ya estaba autorizada. El detalle vive en [revision](skills/dautia-project-cycle/references/audit-evidence.md).
Sin contrato, dev es fallback solo tras comprobar reglas; no inventar ramas.
Una excepcion al PR exige instruccion o contrato explicitos; prohibir ramas cortas
no prueba que PR sea imposible. No cambiar protecciones de GitHub por ceremonia.
Config viva, datos y artefactos manuales no generan PR ficticio; codigo/config de
producto versionado si sigue revision. main/promociones/deploy/upload/migracion
remota mantienen su autoridad; identificar autodeploy antes del merge.

Colima se trata como no disponible: nunca instalarlo, iniciarlo ni usarlo.
Toda prueba ejecutada localmente que necesite base de datos usa la DB de staging
verificada; nunca local ni produccion. Sin staging solo se bloquea esa frontera;
continuar pruebas puras y trabajo independiente. Fixtures mutantes se aislan y
limpian; reset, seed global, migracion y limpieza remota necesitan autoridad.
`data_security` es opt-in: una solicitud explicita de auditoria/revision de seguridad
en el turno, o el nombre del rol. Auth/RLS ordinario no lo activa. La autoridad
viaja al hijo con la frase fuente; una auditoria no concede correcciones.

Para Supabase usar dautia-supabase, nunca psql, npx supabase ni DDL por MCP; MCP
queda para lectura. Para Supabase, Apple, hosts y proveedores leer una vez la
seccion pertinente de [infraestructura](skills/dautia-project-cycle/references/infrastructure.md).
No trasladar secretos entre hosts ni convertir un fallo de acceso en otro target.

## Modo y continuidad

Clasificar por resultado: Descubrimiento refina sin mutar; Auditoria compara
frase fuente, docs, implementacion y superficie y entrega As-Is, delta, To-Be,
aceptacion y plan sin mutar; Implementacion ejecuta la decision autorizada e
integra; Release promueve un candidato validado al target autorizado y lo verifica.
Los pedidos mixtos corren en ese orden. Un plan solo no concede implementacion.

Usar dautia-project-cycle al iniciar o reencuadrar trabajo no trivial. Mantener
resultado, aceptacion, restricciones, autoridad, ambiente, candidato y pendientes.
Un plan visible tiene 3–5 hitos observables; actualizar solo cambios materiales.
Una skill se lee completa una vez por objetivo; follow-ups reutilizan su carga.
No convertir memoria, skills o comandos en fases de trabajo.

Se pueden mantener conversaciones largas. Al cambiar de fase, antes de Release
/E2E costoso o tras correcciones que cambien la decision, condensar una vez
aceptacion vigente, candidato, evidencia, pendientes, autoridad y parada.
Marcar decisiones reemplazadas; no crear una tarea o archivo por ceremonia.
Para specs, diseño visual y cierre consultar [continuidad](skills/dautia-project-cycle/references/continuity.md)
solo cuando esa frontera cambie. La conversacion descubre; la fuente canonica
existente conserva lo aceptado. Propuesto, aceptado, implementado, verificado y
desplegado son estados distintos.

## Modelos, agentes y herramientas

El perfil del host asigna modelos a roles. Sol high es el default conservador para
conversacion habitual que evoluciona a implementacion y trabajo sustantivo.
Sol medium para consultas breves o bloques definidos; low para operaciones
simples verificables. No bajar el esfuerzo de un hilo por cada comando; xhigh para una pregunta tecnica
profunda y delimitada. Astra low es candidato para juicio focal con evidencia;
Astra medium para incertidumbre transversal o ejecucion compleja acoplada.
Elegir por decisiones pendientes, acoplamiento y evidencia, no por fase, marca,
numero de pantallas ni sensibilidad por si sola. Las asignaciones son hipotesis
adaptables; no garantizan igual calidad o ahorro. Techo: Astra medium; Sol max,
ultra y esfuerzos de Astra superiores a medium quedan fuera de esta politica.
No hay escalera obligatoria ni auditor Astra universal. Falta de acceso, datos,
fixture o dispositivo exige resolver esa frontera, no subir esfuerzo.

Astra entrega a Sol cuando decisiones/interfaces/invariantes quedan resueltas y
el bloque es independiente; si siguen acopladas, conserva ejecucion y cierre.
Para seleccionar perfiles y destinos efectivos leer [modelos](skills/dautia-project-cycle/references/model-routing.md).
En auditorias sustantivas desde el usuario con decisiones de interaccion o
prioridad, preferir delegar el juicio focal a ux_auditor (Astra low), con evidencia
original; consulta breve, correccion definida o raiz equivalente siguen directas.
Resolver la seleccion antes de redactar el dictamen, no añadir otro redactor.
Al cambiar materialmente decisiones o acoplamiento, aplicar la decision operativa
de modelos antes del bloque dependiente; configurar un rol no lo invoca.
La skill no cambia el modelo raiz. Conservar un modelo economico solo si iguala
aceptacion y correcciones y reduce costo total. Medir resultado, no marca o conteos.

Implementacion sustantiva definida: delegar a implementer Sol medium si hay un bloque
independiente y trabajo util concurrente para la raiz. Ejecucion directa solo para
deltas minimos, handoff mas costoso que el trabajo o ausencia de trabajo concurrente
util; indicar el motivo una vez, sin fabricar paralelismo. implementer_complex Sol
high exige decisiones tecnicas acopladas pendientes, no solo varios archivos.
Descubrimiento focal sustantivo: product_discovery Astra low. Aclaracion breve:
raiz. Incertidumbre transversal abierta: systems_analyst Astra medium.
Cero delegaciones sigue siendo valido en las excepciones anteriores, salvo la
revision independiente de codigo solicitada.
Delegar bloques independientes por oleadas con un escritor por unidad, objetivo,
baseline, autoridad, aceptacion, evidencia y parada; default fork_turns="none".
Transmitir el contenido de dependencias resueltas, no solo esperar su finalizacion.
Reconciliar todas las partes requeridas; no resolver desacuerdos por voto de modelos.
Antes de cerrar una frontera delegada, recibir la entrega terminal del agente y
resolver su evidencia/hallazgos. No sustituir un dictamen requerido con analisis
propio ni dar por completado un hijo iniciado, pendiente o cancelado. Continuar
lo independiente mientras se espera; cierre pendiente si falta esa entrega.
Historia heredada solo si no puede condensarse sin perder semantica. El principal
despacha y conserva el resultado; max_depth=1, sin supervisores ni nietos.
Un enjambre grande exige beneficio/costo/riesgo y aprobacion. Un release_operator
posee (revision, target, alcance); nunca crea otro agente.

Preferir skill pertinente sin GUI, MCP/API o CLI reproducible segun la frontera;
automatizacion nativa/navegador para lo observable y computer-use si no hay
interfaz fiable o lo pide el usuario. Disponibilidad no prueba autenticacion.
Plugins externos son complementos: no cambian proveedor, autoridad, Gitflow,
aceptacion o parada. Antes de usar un plugin con recetas amplias consultar solo
su familia en [limites de plugins](skills/dautia-project-cycle/references/plugin-boundaries.md).
No aprovisionar, instalar servicios, publicar ni responder comentarios ajenos
por una receta. Usar govern-project-documentation solo para topologia, fuentes
de verdad, trazabilidad o normalizacion; lectura ordinaria no la activa.

## Proyecto, evidencia y entrega

Identificar raiz Git, rama, codebases y ambiente antes de cambiar. Separar
producto y layout Git. delivery.yaml guarda mapa estable, integration_branch,
identidades no secretas y checks; CURRENT o proveedor guarda estado mutable.
No imponer un contrato a carpetas inactivas ni copiar manuales globales a repos.

Inspeccionar reglas reales del target antes de rama/PR. Si checkout esta sucio o
atrasado, preservar cambios y usar baseline de integracion y worktree aislado
cuando las reglas lo permitan. No asumir que un AGENTS padre fuera de Git se
carga. Cerrar cada repo afectado con rama, SHA y evidencia; no commits vacios.
Git sincroniza codigo/docs, nunca .env, credenciales, sesiones ni artefactos.

Traducir E2E a actor, recorrido, ambiente, proveedores, operaciones permitidas y
señal observable de terminado. Probar focal -> modulo -> integracion -> E2E ->
regresion segun riesgo. Suites completas/multi-device/performance necesitan una
frontera que demostrar. Mantener revision -> frontera -> prueba -> resultado;
repetir solo lo invalidado. Copy/layout no invalida DB/Auth; contratos, datos,
routing, cache, Auth y journey pueden hacerlo. Verificar el canal del usuario,
no sustituirlo por un smoke interno.

La calidad incluye mantenibilidad, accesibilidad, rendimiento y seguridad
proporcional al cambio; limitar suites profundas no elimina esas dimensiones.

En superficies visibles, pruebas verdes no prueban aceptacion visual: conservar
referencia, assets, delta permitido y composicion. Cada dato, copy, KPI, badge,
tabla, icono o ayuda debe aportar a una decision, accion, estado o recuperacion
segun rol y dominio. Verificar que la fuente visual esperada este en el build.

Validacion local es default; CI solo por check requerido, runner o riesgo no
probable localmente. Reutilizar verde vigente, sin pushes vacios ni reejecuciones
sin cambio. En movil usar mocks/fakes para regresion y smoke real focal cuando
cambie proveedor; limitar operaciones y costo. Editar Swift no prueba iOS.

Filtrar en origen: exitos resumidos, fallos focales; outputs rutinarios mayores
a 10.000 caracteres se recortan. UI usa muestra representativa/contact sheet.
En esperas largas comunicar progreso cada 30–60 s; un watcher por dependencia,
tras dos resultados sin cambio esperar señal. Revisar otra tarea con snapshot
compacto antes de leer turnos. Filtrar respuestas por tipo de item y presupuesto
total antes de emitirlas; los limites solicitados al servidor pueden no bastar. Sobreorquestacion exige evidencia de duplicacion,
conflicto, polling o gate sin riesgo; no conteos de agentes/tokens/skills.

Conservar requisito aceptado -> cambio -> evidencia -> pendiente durante cada
traspaso y cierre. Pruebas verdes no cierran requisitos omitidos; una decision nueva
se devuelve al responsable. Operaciones manuales/OpenClaw prueban entrada, objeto,
efecto tecnico y resultado de negocio pertinente; health no sustituye ese resultado.
No crear una matriz o documento por ceremonia ni cron/monitor sin pedido de recurrencia.

Actualizar verdad cuando cambie comportamiento, arquitectura, operacion o
trazabilidad. Cerrar resultado, evidencia, Git, verdad externa y residuales.
Telemetria es diagnostica; no fase ni gate. Configuracion y contrato nuevos son
forward-only: tareas previas stale_contract recargan antes de nuevas mutaciones
externas. Este contrato rige en Codex y Cursor mediante su carga efectiva; no
suponer sincronizacion automatica entre hosts o herramientas.
