# Guia global para agentes

Contrato v8 — 2026-08-28T00:00:00-05:00.

Prevalecen la instruccion del usuario y el `AGENTS.md` mas cercano. Las skills
complementan: no agregan etapas, documentos, agentes ni gates.

## Limites y autoridad

- No destruir datos, filtrar secretos, inventar estado externo ni modificar
  produccion sin intencion clara. Preservar cambios ajenos.
- Verificar repo, rama, ambiente, proveedor y revision; un documento o comando
  no prueba deploy, migracion, upload ni estado activo.
- `data_security` es opt-in del turno; Auth, RLS, privacidad y secretos siguen
  siendo trabajo tecnico normal. Un enjambre grande exige beneficio, costo,
  riesgo y aprobacion.
- Colima se trata como no disponible: nunca instalarlo, iniciarlo, configurarlo,
  usarlo ni depender de el.
- Toda prueba ejecutada localmente que necesite base de datos usa la DB de `staging`
  verificada; nunca local ni produccion. Sin staging queda bloqueada.
  Las mutantes aislan y limpian fixtures; reset, seed global, migracion o
  limpieza remota requieren autoridad.

Supabase se autentica una vez por host con `dautia-supabase`: sesion de cuenta y
una password DB por `project_ref`. El registro local
`~/.config/dautia/supabase-db-credentials.json` usa `0600`; Mac puede importarlo
una vez desde Keychain y WSL lo llena durante onboarding. Los comandos normales
no abren prompts ni copian secretos entre hosts, proyectos, argumentos, logs o
chat. Publishable, service-role y access tokens no sustituyen la password DB.
`run --environment` autoenlaza checkouts; `activate` solo repara contradicciones.
Fuera de `supabase login`, usar el wrapper, nunca `supabase`, `npx supabase`,
`psql` ni una version ad hoc. Si vuelve a pedir clave, detener el bypass; no
pedirsela otra vez al usuario.

Apple se configura una vez por identidad en Keychain, incluido el permiso
persistente de `codesign`. No guardar contrasenas, certificados ni credenciales
Apple en Git, env, argumentos o chat. Usar el wrapper de archive/export del
proyecto; un dialogo normal de credencial indica bypass o ACL incompleta y se
detiene sin reintentos.

Una implementacion expresa incluye commit y push a la `integration_branch` de
`delivery.yaml`, o `dev` sin contrato. `staging` integra solo si el contrato lo
declara; `main`, deploy, migracion remota, TestFlight y produccion requieren una
orden al target. Un deploy manual autoriza solo ese target y exige fuente,
acceso, rollback y smoke focal; no exige PR por ceremonia.

## Cuatro modos

Clasificar por resultado:

1. **Descubrimiento** — refinar idea, decisiones y dudas; no mutar codigo ni
   documentacion canonica salvo pedido.
2. **Auditoria** — comparar frase fuente, docs funcionales, codigo/modelo/datos y
   superficie observable. Entregar As-Is, delta, To-Be, aceptacion y plan; no
   mutar.
3. **Implementacion** — implementar la decision aceptada, probar, actualizar la
   verdad relevante e integrar.
4. **Release** — evaluar el SHA validado y promover solo el linaje `READY` al
   ambiente autorizado; luego verificarlo.

Los pedidos mixtos corren en orden: “audita y corrige” agrega Implementacion;
“corrige y despliega a staging” agrega Release. Un plan no concede mutacion.
Promover staging a main fija SHA y separa aplicacion, DB/datos, infraestructura y
docs; valida orden, artefactos, checksums, historial, backup/rollback y verdad
externa. Correcciones sucesivas reutilizan baseline y evidencia; un cambio
material de resultado, autoridad o ambiente inicia un subciclo condensado, no
otra tarea obligatoria.

## Ejecucion simple

Para trabajo no trivial fijar resultado, aceptacion, evidencia, restricciones,
autoridad, ambiente y parada. Un plan visible tiene 3 a 5 hitos observables, uno
en progreso; skills, memoria y comandos no son pasos. Actualizarlo solo ante
cambio de hito, alcance o bloqueo.

Antes de Release, E2E costoso o tras muchas correcciones, condensar una vez:
resultado, candidato, ambiente, alcance/anti-alcance, proveedores y orden,
artefactos DB, evidencia vigente, fronteras pendientes, rollback, autoridad y
parada. Descartar planes reemplazados y outputs extensos; no crear un archivo por
ceremonia.

Antes de cambiar, identificar raiz, Git, rama, codebases y ambiente. Leer una
vez los contratos relevantes. Una skill se lee completa una vez por objetivo;
follow-ups y reintentos reutilizan la carga. Una skill de proveedor no obliga a consultar changelogs
o la web salvo duda real de version o API.

Un cambio de workflow no alcanza tareas activas. Registrar version/hora; la
tarea previa queda `stale_contract` y recarga o reinicia antes de nuevas
mutaciones externas. Inspeccionar `--help` o fuente de un CLI propio una vez,
sin aprender por reintentos evitables.

Filtrar resultados en origen. Resumir exitos y expandir fallos; outputs rutinarios
mayores a 10.000 caracteres requieren recorte o justificacion. No introducir
binarios, base64 ni logs completos al contexto. Para UI usar una muestra representativa o contact sheet,
no capturas por micro-paso.

En suites, builds o esperas largas, avisar antes y consultar cada 30–60 segundos.
Un watcher por dependencia; tras dos resultados sin cambio, esperar una señal.
Para otra tarea de Codex usar primero listado o snapshot compacto; leer turnos
solo ante una anomalia concreta y sin outputs grandes.

Usar `dautia-project-cycle` al iniciar o reencuadrar trabajo no trivial, no por
follow-up. Cero delegaciones es valido. Con bloques independientes, delegar por
oleadas: contrato compartido, implementacion con ownership y revision cuando
exista artefacto. Default `fork_turns="none"` con handoff de objetivo, baseline,
autoridad, aceptacion, evidencia y parada. Historia parcial/completa solo cuando
una conversacion no resuelta no pueda condensarse. Sobreorquestacion requiere
evidencia de duplicacion, conflicto, resultado inutil, polling o gate sin riesgo;
no conteos de agentes, tokens, tools o skills.

Usar `govern-project-documentation` solo para topologia, fuentes de verdad,
trazabilidad, scaffolding o normalizacion; no para lectura ordinaria.

## Harnesses, modelos y hosts

Este contrato rige igual en Codex y Cursor. Plugins externos son complementos:
no cambian autoridad, ambiente, Gitflow, aceptacion, evidencia ni parada.
El perfil del host asigna modelos a roles. Conservar un modelo economico solo si
iguala aceptacion y correcciones y reduce costo total sin regresiones; si falla, Sol.
Medir resultado y costo, no conteos ni marca.

Mac posee Xcode, Simulator, codesign, TestFlight y App Store Connect. WSL puede
trabajar web, backend, docs, Android y proveedores declarados; editar Swift no
prueba iOS. Git sincroniza codigo y docs, nunca `.env`, credenciales, sesiones,
caches, worktrees ni artefactos. Una release compartida tiene un propietario y
fija `(SHA, target, alcance, host)`.

## Repositorios y worktrees

Separar topologia del producto (web, backend, iOS, Android, datos, infra) del
layout Git (`single-repo`, `monorepo`, `multi-repo`). `delivery.yaml` guarda el
mapa estable; `CURRENT.md` o el proveedor guardan estado mutable.

El destino de Implementacion es la rama `integration_branch`: trabajar alli o
en una rama corta basada en ella, validar, integrar y subir. Sin contrato, usar
`dev`. No declarar cierre si el cambio solo quedo en una rama efimera, salvo
resultado local expreso. Default `feature/* -> dev`; promociones son separadas.

Antes de una rama/PR, inspeccionar reglas reales del target. Si el checkout esta
sucio, atrasado o no representa integracion, leer el contrato una vez desde
`origin/<integration_branch>` y usar `<raiz>/.worktrees/<tarea>`. No limpiar ni
adoptar docs obsoletas. Retirar el worktree cuando el commit sea recuperable.

En multi-repo, aplicar el incremento solo a repos afectados, desde sus baselines,
con pruebas, commits y pushes trazables. Cerrar `repo -> rama -> SHA -> evidencia`;
no crear commits vacios.

Un `release_operator` posee `(revision fuente, ambiente/target, alcance)` y puede
secuenciar proveedores que compartan revision, autoridad, dependencias y
rollback. Separar solo si cambia un limite o el fallo es independiente. Nunca
crea otro `release_operator`; una ampliacion vuelve al agente raiz.

## Pruebas, UI y cierre

Preferir evidencia reproducible: 1) skill especializada sin GUI; 2) MCP/API; 3)
CLI/script; 4) automatizacion nativa; 5) navegador/Playwright; 6)
`computer-use`, solo si no existe interfaz fiable o el usuario lo pide.

Probar por riesgo: focal -> modulo -> integracion -> E2E -> regresion. Suites
completas, multi-device, performance, memoria o accesibilidad profunda exigen un
riesgo o gate. Reutilizar evidencia verde solo para la misma revision o una
correccion que no invalide su frontera. Mantener
`revision -> frontera -> prueba -> resultado`; repetir solo dependencias
afectadas. Copy/layout no invalida DB/Auth; contratos, datos, routing, cache,
Auth o journey si.

En movil, la regresion usa mocks/fakes. Un proveedor real recibe un smoke focal
solo si cambio esa frontera, con capacidad, build, dispositivo, maximo de
operaciones, cuota/costo y parada. Google Navigation reutiliza una ruta; Apple/
Google Sign-In, APNs y StoreKit siguen el mismo criterio. Supabase staging y
Vercel conservan sus contratos propios.

DB staging y produccion son independientes. Git transporta migraciones
inmutables, nunca filas. DDL usa CLI/wrapper; MCP queda para lectura. Produccion
exige autoridad, identidad, historial, backup/PITR, compatibilidad y postflight;
cambios incompatibles usan expandir -> migrar -> contraer.

Validacion local es default. GitHub Actions solo como check requerido, gate,
runner externo o riesgo no demostrable localmente. Reutilizar runs verdes del
mismo SHA; no pushes vacios ni reejecuciones sin cambios. Abrir PR de promocion
solo al iniciar Release. Limitar triggers/rutas, cancelar obsoletos y reservar
artefactos para fallo, manual o release con retencion minima.

La calidad incluye mantenibilidad, accesibilidad, rendimiento y seguridad
proporcional. En superficies visibles, pruebas verdes no prueban aceptacion visual:
cada dato, copy, KPI, badge, tabla, icono o ayuda debe apoyar una
decision, accion, estado no obvio o recuperacion acorde al rol y dominio. Sin
valor demostrable se omite; una buena estructura explica el flujo ordinario.

Actualizar docs cuando cambien comportamiento, arquitectura, operacion o
trazabilidad, sin documentos ceremoniales. Cerrar con alcance, archivos,
pruebas, docs, Git, verdad externa y residuales. Tras dos consultas externas sin
señal, esperar o cerrar honestamente.
