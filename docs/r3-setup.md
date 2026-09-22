# Instalación r3: primero el candidato, después el host piloto

Estado: código candidato; no implica una instalación ni prueba del runtime Codex.
Python 3.11+ y Git son necesarios. No se instala ningún servidor, base de datos,
SDK de IA ni framework. Trabajar desde un checkout completo del workflow con el overlay aplicado, no desde
la carpeta de overlay incompleta del paquete. No cambiar la rama de un hilo activo para instalar.

## Comprobación offline

```sh
python3 scripts/check_portability.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/render_agents.py --check --profile codex-macos
python3 scripts/install.py --profile codex-macos --scope workflow
```

El último comando es una previsualización. Para WSL usar `--profile wsl-shared`.
`CODEX_HOME` y `XDG_CONFIG_HOME` deben ser rutas absolutas. En macOS las skills
van bajo CODEX_HOME/skills; en WSL las compartidas van bajo ~/.agents/skills.
El launcher utiliza exactamente la misma raíz, con espacios entre comillas.
`--scope routing` deja intactas las skills CI/CD y el launcher Supabase existentes.
`--skill NOMBRE` es repetible y añade únicamente las skills seleccionadas del repo
al scope base; no usar `--scope all` para actualizar unas pocas skills.

## Aplicación protegida

Revisar diferencias de instrucciones globales, skills y perfiles locales. Un archivo
modificado que no coincide con el último hash administrado se declara conflicto.
No se restaura a ciegas la versión del repositorio sobre personalizaciones locales.
Tras reconciliar el destino concreto, la adopción explícita puede respaldarlo:

```sh
python3 scripts/install.py --profile codex-macos --scope workflow --apply
# Solo después de revisar los conflictos:
# python3 scripts/install.py --profile codex-macos --scope workflow --apply --adopt-existing
python3 scripts/install.py --profile codex-macos --scope workflow --check
```

`--configure-root` es opt-in: solo actualiza model y model_reasoning_effort del
nivel raíz y los dos defaults de `[agents]` en config.toml. Conserva credenciales,
MCP y demás campos; genera las definiciones administradas según el perfil. No modifica
sesiones activas ni límites administrados. Los defaults de los trabajadores
canónicos se instalan según la matriz GPT-6 de la política: principal Sol medium,
explorador Luna high, perfiles analíticos Astra low y esfuerzo por tarea.
Astra high no forma parte del catálogo activo; cualquier definición heredada queda
fuera del despacho permitido. No activar perfiles por mera presencia de un TOML.
Los archivos de versiones anteriores que ya no administra esta revisión no se
borran automáticamente. Reconciliarlos si colisionan con el catálogo activo.

El instalador registra hashes y revisión de fuente; un working tree con cambios
se etiqueta `uncommitted`, nunca como una revisión exacta. Conserva un respaldo
restrictivo por transacción con bytes, permisos y manifest. La reversión usa la
ruta exacta devuelta por la instalación y rechaza ediciones posteriores:

```sh
python3 scripts/install.py --rollback /ruta/absoluta/al/respaldo/r3-...
```

No revierte productos, archivos ajenos, operaciones externas ni estado de sesiones.

## Routing determinista

La política local selecciona el perfil antes del dispatch. Principal GPT-6 Sol
medium; ejecución exigente Sol high; ejecución desconocida requiere clasificación.
Astra low/medium solo análisis y Luna high solo bloques de exploración/documentación
acotados. Consultar `skills/dautia-project-cycle/references/model-routing.md`.
Ninguna selección local prueba que el host cargó el modelo; verificar definición,
contexto runtime y resultado terminal por separado.

Una instalación previa puede conservar un launcher local de Jev o una personalización
fuera del conjunto administrado. El rollback no lo borra automáticamente: primero se
comprueba su origen y se conserva el respaldo; cualquier retirada explícita requiere
autoridad separada y lectura posterior. Que exista ese comando heredado no lo vuelve
parte del dispatch ni del camino crítico de esta versión.

## Hooks y límites efectivos

Se genera `hooks.r3.candidate.json`, NO se copia a hooks.json ni se otorga confianza.
Revisar/combinar con los hooks existentes, hacer smoke aislado y aprobar en `/hooks`
solo cuando la versión instalada soporte ese protocolo. No sustituir otros hooks.

`dautia-workflow bind packet.json --session ID --generation G --cwd ROOT` vincula
un objetivo real. El packet debe provenir del trabajo investigado; los ejemplos
marcados fixture_only no se pueden vincular a una sesión real. El principal mantiene
el packet en fronteras materiales; no se analiza automáticamente el transcript.
Una nueva generación después de revisar el contexto reanuda un objetivo interrumpido.

La cobertura inicial es parcial: raíz vinculada, herramientas PreToolUse soportadas,
Stop acotado, Interrupt y preservación para compactación. Un hijo no hereda el permiso
del padre por compartir su session_id. Herramientas remotas no soportadas siguen bajo
sus controles nativos. No existe un parser universal seguro de shell.
Para un diagnóstico SSH de lectura, el principal puede preparar en work.read_commands
las órdenes EXACTAS amparadas por la solicitud/runbook y la autoridad de lectura del
target. No se incorporan automáticamente comandos recibidos del hook. Un comando
no previsto se reencuadra, no se convierte en una mutación autorizada.

El sandbox read-only de auditores protege producto, pero algunas herramientas QA
necesitan escribir caches/artefactos. Eso se prueba en un workspace de validación
separado y con permisos explícitos del host; no se otorga workspace-write sobre
producto solo porque compilar falle. Si hace falta preparar tests, lo hace el
escritor autorizado y QA valida después. No se afirma equivalencia App/CLI/Cursor.

## Prueba del host antes de adopción

Verificar versión/descubrimiento de roles, perfil realmente aplicado (principal GPT-6 Sol medium,
implementer medium o high según el encargo), retorno de un hijo,
consulta analítica Astra sin escritura, rechazo de contradicción, pausa/reanudación,
artefactos QA y preservación de cambios ajenos. La medición de modelos reportados
queda unknown si el runtime no la expone. El routing local no activa proveedores
externos ni llamadas de red.

El CLI registra automáticamente metadatos mínimos de bind/gate/hooks y routing
local; no lee transcripciones completas. DAUTIA_TELEMETRY=off desactiva ese
registro sin conceder permisos ni cambiar los criterios. Las brechas de cobertura
no se contabilizan como ceros.
