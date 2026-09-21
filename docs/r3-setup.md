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
nivel raíz de config.toml. No modifica credenciales, MCP, roles personalizados,
sesiones activas ni límites administrados. Los defaults de los trabajadores
canónicos se instalan según el perfil del host: principal high, implementer medium
y variantes Sol medium/high para el despacho. Una definición Astra high heredada
puede existir para roles read-only, pero queda bloqueada por la política y no se
selecciona ni despacha; los workers no heredan Astra accidentalmente.
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

La política local selecciona el perfil antes del dispatch. El principal usa Sol high;
un implementador solo usa Sol medium cuando las decisiones están resueltas y la
ejecución es rutinaria. La ejecución exigente o desconocida usa Sol high. Astra
low/medium queda limitada a análisis con evidencia del principal. Ninguna selección
local constituye prueba de que el host cargó el modelo: el adaptador debe comprobar
el archivo de definición y el perfil efectivo.

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

Verificar versión/descubrimiento de roles, perfil realmente aplicado (principal high,
implementer medium o high según el encargo), retorno de un hijo,
consulta analítica Astra sin escritura, rechazo de contradicción, pausa/reanudación,
artefactos QA y preservación de cambios ajenos. La medición de modelos reportados
queda unknown si el runtime no la expone. El routing local no activa proveedores
externos ni llamadas de red.

El CLI registra automáticamente metadatos mínimos de bind/gate/hooks y routing
local; no lee transcripciones completas. DAUTIA_TELEMETRY=off desactiva ese
registro sin conceder permisos ni cambiar los criterios. Las brechas de cobertura
no se contabilizan como ceros.
