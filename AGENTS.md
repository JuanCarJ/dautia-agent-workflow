# Guia global para agentes

Contrato v8 — 2026-08-28T00:00:00-05:00.

Prevalecen la instruccion del usuario y el `AGENTS.md` mas cercano. Las skills complementan; no agregan etapas, documentos, agentes ni gates.

## Limites duros

- No destruir datos, filtrar secretos, inventar estado externo ni modificar produccion sin intencion clara.
- Preservar cambios ajenos. No revertirlos, mezclarlos ni limpiar un worktree para facilitar otra tarea.
- Verificar repo, rama, ambiente, proveedor y revision; la documentacion no prueba estado activo.
- `data_security` es opt-in del turno. Los minimos de Auth, RLS, privacidad, secretos y datos siguen siendo trabajo tecnico normal.
- Un enjambre grande requiere explicar beneficio, costo y riesgo, y aprobacion explicita.
- Una demo privada y reversible no es produccion. Elevar controles ante exposicion publica, datos reales, infraestructura compartida o efectos dificiles de revertir.
- Distinguir sesion activa, token expuesto y credencial comprometida. Rotar solo secretos con exposicion confirmada y solo las identidades afectadas.
- Colima se trata como no disponible: nunca instalarlo, iniciarlo, configurarlo, usarlo ni depender de el. Solo detectar en lectura o retirar por pedido expreso.
- Toda prueba ejecutada localmente que necesite base de datos usa la DB de `staging` verificada; nunca local ni produccion. Sin `staging`, queda bloqueada. Las mutantes aislan y limpian fixtures; reset, truncate, seed global, migracion o limpieza remota requieren autoridad.
- Supabase se autentica una vez por host: sesion de cuenta y una contrasena DB por `project_ref` mediante `dautia-supabase`. El registro canonico local es `~/.config/dautia/supabase-db-credentials.json` con permisos `0600`; macOS puede importarlo una vez desde Keychain y WSL lo llena directamente durante onboarding. Los comandos normales leen el registro y nunca abren un prompt. El wrapper inyecta el fallback oficial `~/.supabase/access-token` con permisos `0600`; ningun secreto se copia entre hosts ni entra a proyectos, argumentos, logs o chat. No pedir que el usuario pegue claves si la sesion, el registro, Keychain en Mac o un `.env.*.local` ignorado permiten recuperarlas. Durante onboarding puede escribirse `SUPABASE_DB_PASSWORD` una sola vez en el env ignorado del ambiente, importarse con `dautia-supabase bootstrap` y retirarse del archivo. Publishable, service-role y access tokens no sustituyen la contrasena DB. Con varios ambientes, guardar una entrada por ref; `run --environment` autoenlaza checkouts nuevos y `activate --environment` queda solo para reparar un link contradictorio. Fuera de `supabase login`, nunca ejecutar `supabase` ni `npx supabase` directamente en un proyecto administrado: usar su comando local o `dautia-supabase run --environment <ambiente> -- <comando>`. Una version ad hoc `npx supabase@...` queda bloqueada hasta incorporarla al wrapper. Si una ruta pide la contrasena otra vez, detenerla como bypass; no volver a pedirsela al usuario.
- La firma Apple se configura una vez por identidad en el Keychain del Mac mediante el onboarding del proyecto, incluyendo el permiso persistente para `codesign`. Nunca guardar la contrasena del Mac, certificado o Apple en Git, env, argumentos o chat. Cuando el proyecto tenga wrapper de archive/export, el `release_operator` debe usarlo; un dialogo de credencial durante un release normal indica bypass o ACL incompleta, se detiene sin reintentos y se corrige en onboarding.

Una implementacion expresa incluye commit y push a `integration_branch` de `delivery.yaml`, o `dev` sin contrato. `staging` solo integra si el contrato lo declara; de otro modo es Release. `main`, deploy, promocion, migracion remota, TestFlight y produccion requieren instruccion al target. Un `release_operator` posee una transaccion inmutable `(revision fuente, ambiente/target, alcance de release autorizado)` y puede ejecutar en orden varios proveedores cuando comparten revision, ambiente, autoridad, dependencias y rollback coordinado. Separar operadores solo si cambia alguno de esos limites, los fallos son independientes o el paralelismo reduce materialmente el camino critico. Nunca crea otro `release_operator`; cualquier ampliacion vuelve al agente raiz.

Un **deploy manual** autoriza solo el target nombrado. Verificar fuente, target, acceso, rollback y smoke focal; no exigir PR ni ampliar autoridad.

## Cuatro modos

Clasificar la frase del usuario por resultado, no por palabras aisladas:

1. **Descubrimiento** — Refinar idea, decisiones y dudas. No mutar codigo o docs canonicas salvo pedido.
2. **Auditoria** — “analiza”, “revisa”, “audita”, “contrasta”. Comparar frase fuente, documentacion funcional, codigo/modelo/datos y superficie observable. Entregar As-Is, delta, To-Be, aceptacion y plan. No mutar.
3. **Implementacion** — Implementar la decision aceptada, probar, actualizar docs relevantes e integrar en la rama de integracion resuelta desde `delivery.yaml` o, por defecto, `dev`.
4. **Release** — Evaluar primero el SHA validado y promoverlo desde esa rama solo al ambiente autorizado cuando el veredicto sea `READY`; después verificarlo.

Los pedidos mixtos se ejecutan en orden. “Audita y corrige” significa Auditoria -> Implementacion. “Corrige y despliega a staging” agrega Release al target nombrado. Un plan no concede autoridad de implementacion.

“Pasar/promover staging a main” activa preflight: fijar SHA y target; separar aplicacion, DB/datos, infraestructura y docs; comprobar orden, pruebas, backup/rollback y verdad externa. Solo `READY` permite promover. Con DB, incluir artefactos exactos, checksum, historial y reconciliacion por ambiente.

Las correcciones sucesivas caben en el mismo hilo: reutilizar baseline, decisiones, evidencia y plan. Ante un cambio material de producto, resultado, autoridad o ambiente, cerrar el subciclo con verdad real, condensar otra baseline y descartar plan, skills y evidencia inaplicables; no exigir otra tarea.

## Ejecucion simple

Para trabajo no trivial, fijar resultado, aceptacion, evidencia, restricciones, autoridad, ambiente y parada. Minimizar ciclos; no crear archivos ni repetir una baseline sin cambio material.

Cuando exista un plan visible, debe reflejar progreso real y no ceremonia interna:

- Usar de 3 a 5 hitos observables; memoria, skills y comandos no son pasos.
- Actualizarlo solo ante cambio de hito, alcance o bloqueo, con uno en progreso.
- Tras compactar, restaurar estados. En Implementacion, condensar una vez baseline, alcance, aceptacion, anti-alcance y residuales.
- Antes de una compilacion, suite, espera externa u operacion previsiblemente larga, comunicar que se ejecutara; al recuperar control, informar el resultado antes de continuar.
- En correcciones sucesivas conservar baseline y modificar solo el delta.
- Si el contexto ralentiza, condensar baseline, decisiones, evidencia y pendientes sin otra tarea ni documentos.

Antes de entrar a Release o a un E2E costoso, y despues de una serie de correcciones que vuelva obsoleto el plan anterior, condensar una sola vez un paquete operativo en contexto: resultado y aceptacion, revision candidata, ambiente, alcance y anti-alcance, proveedores y orden, artefactos DB/checksums cuando apliquen, evidencia vigente, fronteras aun no probadas, rollback, autoridad y parada. No crear un archivo por ceremonia. Descartar del contexto operativo planes reemplazados, salidas extensas, hipotesis resueltas y evidencia invalidada; conservar referencias estables y decisiones.

Antes de cambiar, identificar raiz, rama, Git, codebases, ambiente y anti-alcance. Leer una vez solo contratos relevantes. Si discrepan, comprobar realidad y registrar el delta útil.

Una skill se lee completa una vez por objetivo. Follow-ups, reintentos, validaciones y transiciones reutilizan la carga. No reinvocarla en cada paso. Recargar solo ante objetivo nuevo, archivo cambiado o perdida de instrucciones indispensables; abrir referencias cuando apliquen.

Una skill de proveedor no obliga a consultar changelogs o la web en cada uso. Hacerlo solo ante una duda real de version, API, compatibilidad o comportamiento reciente que el codigo, la configuracion y la documentacion instalada no resuelvan.

Los cambios de workflow no alcanzan tareas activas. Registrar version/hora y revisarlas una vez; una tarea anterior queda `stale_contract`, sin nuevas mutaciones externas hasta reiniciar o recargar el delta. No interrumpirla sin autoridad.

Antes del primer uso de un script o CLI propio cuyo contrato no sea conocido en el hilo, inspeccionar `--help`, uso o fuente una vez; no aprender su interfaz mediante reintentos evitables.

Limitar resultados en origen con filtros y `max_output_tokens`. En exito, conservar resumen; expandir solo fallos o preguntas concretas. Salidas rutinarias mayores a 10.000 caracteres requieren recorte o justificacion. Para una etapa acotada con varias salidas grandes y estructura conocida, filtrar, agregar o deduplicar dentro del runtime programatico y devolver al modelo solo el resultado reducido; conservar llamadas directas cuando cada respuesta cambie el juicio siguiente. No introducir base64, binarios, logs completos ni historiales visuales al contexto: referenciar el artefacto y abrir solo la muestra o fragmento necesario. Agrupar lecturas; para evidencia visual usar una muestra representativa o contact sheet, no capturas por micro-paso.

Para inspeccionar otra tarea de Codex, empezar por listado, snapshot de espera o telemetria estructural. Leer turnos solo cuando una anomalia concreta lo requiera, con limite pequeno y sin outputs; no abrir una tarea con imagenes o artefactos embebidos para obtener un estado que ya ofrece el resumen.

En comandos, builds y suites largas, usar un `yield` inicial razonable y despues consultas espaciadas de 30 a 60 segundos, comunicando antes la espera. Un solo watcher posee cada dependencia. Tras dos resultados consecutivos sin cambio, dejar de consultar hasta que exista una senal o checkpoint razonable; no despertar agentes ni fragmentar la espera para confirmar el mismo estado.

Usar `dautia-project-cycle` al iniciar o reencuadrar trabajo no trivial, no por follow-up. No agrega etapas, agentes, telemetria ni documentos. Cero delegaciones es valido. Con bloques independientes, delegar por oleadas: fijar primero el contrato compartido, luego implementar en paralelo y revisar solo cuando exista un artefacto. Toda delegacion usa por defecto `fork_turns="none"` y recibe un handoff breve con objetivo, baseline/revision, ownership, autoridad, aceptacion, evidencia y parada. Usar un fork parcial o `fork_turns="all"` solo cuando el agente necesite interpretar conversacion no resuelta que no pueda condensarse sin perder una decision material; registrar esa necesidad en el handoff. Conteos de agentes, tools, tokens, skills, esperas o planes no prueban sobreorquestacion: exigir duplicacion, conflicto, resultado no usado, polling ineficaz, gate sin riesgo o una comparacion peor.

Usar `govern-project-documentation` solo cuando el problema sea topologia documental, fuentes de verdad, trazabilidad, scaffolding o normalizacion. Leer o actualizar documentacion ordinaria no la activa.

El perfil del host asigna modelos a roles. Conservar un modelo mas economico solo si iguala aceptacion, correcciones y autoridad y evita regresiones criticas. Medir resultado y costo, no conteos ni marca del modelo.

## Harnesses, modelos y hosts

Este contrato rige igual en Codex y Cursor. Un plugin, modelo o herramienta puede cambiar la ejecucion interna, pero no autoridad, ambiente, Gitflow, aceptacion, evidencia ni parada. Cuando una capacidad no exista, usar un equivalente reproducible o declarar la frontera pendiente; no fingir soporte.

Los perfiles versionados del workflow contienen routing de modelos y capacidades por host. No fijar en skills generales un modelo, tool call o ruta absoluta cuando basta describir la capacidad. Plugins externos son complementos y no pueden convertirse en otro workflow implicito.

macOS posee Xcode, Simulator, codesign, TestFlight y App Store Connect. WSL puede trabajar web, backend, documentacion, Android, Supabase, Vercel, DigitalOcean y otros proveedores declarados; editar Swift no demuestra una validacion iOS. Git sincroniza codigo y documentos. Credenciales, `.env`, caches, sesiones, worktrees y artefactos permanecen locales.

Una release desde infraestructura compartida tiene un solo propietario y fija `(SHA, target, alcance, host)`. Otro host no ejecuta simultaneamente la misma transaccion.

## Proyecto, repositorios y worktrees

Separar dos conceptos:

- **Topologia del producto:** uno o varios codebases, por ejemplo frontend, backend, iOS, Android, datos e infraestructura.
- **Layout Git:** `single-repo`, `monorepo` o `multi-repo`.

`delivery.yaml` describe mapa estable, ramas, ambientes, gates y rollback. Estado mutable vive en `CURRENT.md` o el proveedor.

El destino de Implementacion es la rama `integration_branch` de `delivery.yaml`: trabajar ahi o en una rama corta basada en ella, validar, integrar y subir. Sin contrato, usar `dev`. No declarar cierre si el cambio solo quedo en una rama efimera, salvo resultado local expreso. Default: `feature/* -> dev`; `dev -> staging -> main` son promociones separadas. El contrato puede declarar `staging` como integracion.

Antes de crear una rama corta o PR, inspeccionar una vez las reglas reales del target, patrones de ramas permitidos y checks requeridos. No aprenderlos provocando ejecuciones fallidas.

Si el checkout esta atrasado, eliminado o sucio y no representa integracion, leer una vez el contrato en `origin/<integration_branch>` y usar un worktree aislado desde esa referencia. No adoptar docs obsoletas ni limpiar cambios ajenos.

Usar worktrees solo por cambios ajenos, aislamiento o paralelismo; ubicarlos en `<raiz>/.worktrees/<tarea>`. Retirarlos cuando el trabajo sea recuperable en remoto; conservar ramas con trabajo unico.

En multi-repo, aplicar el mismo incremento a cada repositorio afectado: baseline de su rama de integracion declarada, cambios y pruebas propios, commits trazables, push de cada rama y cierre con la matriz repo -> rama -> SHA -> evidencia. No forzar commits vacios en repositorios no afectados.

## Capacidades, pruebas y cierre

Preferir evidencia reproducible en este orden:

1. skill especializada sin GUI;
2. MCP, conector o API del proveedor;
3. CLI o script;
4. automatizacion nativa;
5. navegador especializado o Playwright;
6. `computer-use`, solo si la operacion depende de una app o estado visual sin interfaz fiable, o si el usuario lo pide.

Probar por riesgo: focal -> modulo -> integracion -> E2E -> regresion, solo hasta cubrir las fronteras afectadas. Suites completas, multi-device, lifecycle, performance, memoria o accesibilidad profunda necesitan un riesgo o gate concreto.

En aplicaciones moviles, una suite amplia usa mocks, fakes o modo offline para proveedores externos. La integracion directa con un proveedor se prueba solo cuando la funcionalidad modificada depende de una frontera que el doble no puede demostrar; se ejecuta un smoke focal sobre esa capacidad, no toda la regresion. Antes de probar, clasificar cada proveedor movil relevante como `mock`, `disabled`, `staging` o `live`. Un proveedor `live` requiere capacidad exacta, revision/build, dispositivo, numero maximo esperado de operaciones, cuota/costo protegido y condicion de parada; una invocacion inesperada detiene el smoke. Si adaptador, configuracion, credencial y contrato de la capacidad no cambiaron, reutilizar la evidencia directa vigente y probar el resto con dobles.

Para Google Navigation, el smoke real puede inicializar el SDK, resolver una sola ruta con un `setDestinations` y comenzar/detener o reabrir esa misma sesion sin recalcularla. Idiomas, menus, layout, Dynamic Type, permisos, lifecycle, llegada, errores y reintentos se prueban con proveedor determinista salvo que uno de ellos sea precisamente la frontera modificada; aun asi, no debe multiplicar solicitudes reales. Sign in with Apple/Google, APNs, StoreKit y otros SDK moviles siguen el mismo criterio: una operacion sandbox/focal por capacidad afectada y regresion con dobles. Esta regla no modifica las pruebas contra Supabase `staging` ni la validacion o promocion de Vercel, que conservan sus contratos actuales.

Reutilizar evidencia verde solo para la misma revision o para una correccion posterior que no invalide su frontera. Mantener en contexto un registro minimo `revision -> frontera -> prueba -> resultado`; ante cada correccion identificar primero que fronteras cambiaron y repetir solo sus pruebas y dependencias. Un cambio de copy o layout no invalida por si mismo migracion, Auth o suites moviles; un cambio de contrato, datos, routing, cache, Auth o journey si invalida sus pruebas relacionadas. Repetir E2E/regresion completa solo cuando cambie el riesgo cubierto, el candidato final o un gate del release lo exija.

Un cambio solo de dependencias usa unitarias, lint, tipos, build, rutas representativas sin mutacion y smokes focales. E2E mutante completo requiere riesgo en routing, cache, auth, datos o comportamiento; no agregar plataformas, navegadores o viewports sin riesgo concreto.

Las pruebas unitarias o puras que no usan base de datos siguen siendo locales. Para cualquier prueba con DB, verificar primero la identidad `staging` mediante `delivery.yaml`, configuracion segura y proveedor; no usar un fallback local si faltan acceso o credenciales.

Con bases staging/produccion independientes, Git transporta la misma migracion versionada e inmutable, nunca filas ni un diff del estado vivo. Aplicar y reconciliar cada ambiente. Ejecutar DDL con el CLI/wrapper del proyecto; MCP queda para inspeccion, advisors, logs y lectura, no `apply_migration` ni `execute_sql`. Produccion exige autoridad, identidad, historial/preflight, backup/PITR proporcional, compatibilidad y verificacion. Cambios incompatibles: expandir -> migrar/backfill -> contraer en releases separados.

La validacion local es el default. GitHub Actions se usa solo como check requerido, gate de rama o release, runner externo necesario, o para un riesgo concreto que no pueda demostrarse localmente. Reutilizar una ejecucion verde del mismo SHA y workflow; no hacer pushes vacios, alternar draft/ready ni reejecutar codigo sin cambios solo para obtener CI.

Abrir un PR de promocion solo al iniciar el Release autorizado; mantenerlo abierto mientras la rama recibe trabajo consume Actions y previews. Si ya existe, reportarlo y no mutarlo sin autoridad.

En workflows, limitar disparadores por rama y rutas, cancelar ejecuciones obsoletas y consolidar cambios en un push ya validado. No subir artefactos exitosos de debug o reportes reproducibles por defecto: reservar artefactos para fallo, ejecucion manual o release, con la retencion minima util. Activar caches solo cuando el ahorro medido de tiempo justifique su almacenamiento.

La calidad incluye mantenibilidad, accesibilidad, rendimiento, seguridad proporcional y observabilidad, sin rediseños no pedidos. En cambios visibles de alto juicio, observar la superficie real y revisar su valor antes de integrar: pruebas verdes no prueban aceptacion visual; cada dato, copy, KPI, badge, tabla, icono o ayuda debe servir al rol y dominio, apoyar una decision, accion, estado no obvio o recuperacion, y concordar con la funcion. Sin valor demostrable se omite; estructura y controles explican el flujo ordinario antes que el copy.

Actualizar documentacion canonica cuando cambien comportamiento, decisiones, arquitectura, operacion o trazabilidad; no crear documentos por ceremonia. Registrar fuentes estables como commit, PR o resultado del proveedor; no crear ciclos de cambios documentales solo para perseguir un `dev` mutable. Un comando, subagente o `task_complete` no prueba CI, deploy, migracion, upload ni release: verificar identidad, ambiente y resultado.

Cerrar con alcance, archivos, pruebas, docs, Git, verdad externa y residuales. Un `turn_aborted`, retiro de autoridad o cambio de objetivo cierra la ventana. Tras dos consultas sin señal, esperar o cerrar honestamente.
