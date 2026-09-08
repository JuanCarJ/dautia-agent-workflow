# Infraestructura compartida · v9

Leer solo la seccion del proveedor/host afectado. El proyecto conserva identidades,
comandos propios, ramas y ambientes; esta referencia no prueba estado activo.

## Supabase

Autenticar una vez por host con dautia-supabase: sesion de cuenta y password DB
por project_ref. El registro ~/.config/dautia/supabase-db-credentials.json usa
0600; Mac importa una vez de Keychain, WSL lo completa en onboarding. No copiar
secretos entre hosts, proyectos, argumentos, logs, Git o chat. Tokens publishable,
service-role o access no sustituyen password DB. run --environment autoenlaza
checkouts; activate repara contradicciones. Fuera de supabase login usar wrapper,
nunca supabase directo, npx supabase, psql o version improvisada. Un prompt de
clave repetido es fallo de onboarding/bypass; detenerlo, no pedirla de nuevo.
Para comandos, consultar la referencia de credenciales de dautia-ci-cd.

Tests con DB requieren staging verificado; no DB local ni produccion. MCP es
lectura; DDL via wrapper con autoridad de ambiente. Git transporta migraciones
inmutables, no filas. Produccion exige identidad, historial, backup/PITR,
compatibilidad y postflight; incompatible: expandir -> migrar -> contraer.

## Apple y movil

Identidad y ACL de codesign se configuran una vez en Keychain. No guardar
contrasenas/certificados en Git/env/argumentos/chat. Usar wrapper archive/export
del proyecto; prompt recurrente de credencial implica bypass/ACL pendiente,
sin reintentos. Mac posee Xcode, Simulator y signing; WSL no prueba iOS.
Regresion con mocks/fakes; smoke real focal solo si cambia frontera, declarando
capacidad, build, dispositivo, maximo de operaciones, cuota y parada. Reutilizar
ruta Google Navigation; mismo criterio para Sign-In, APNs y StoreKit.
Fuente, archive, upload, build procesado y distribucion son evidencias distintas.
Cuando cambien empaquetado, configuracion o cache persistente, comprobar valores
e identidades esperadas dentro del artefacto sin exponer secretos y probar el
upgrade desde el estado anterior afectado; una instalacion limpia no lo sustituye.

## Hosts y proveedores

Mac y WSL conservan credenciales/sesiones propias. WSL puede web/backend/docs/
Android segun herramientas verificadas. Colima no esta disponible. No copiar
caches, worktrees, binarios ni .env mediante Git. Un responsable de release fija
(SHA, target, alcance, host); otros hosts aportan evidencia sin promover por su cuenta.

El mapa estable del proyecto contiene repo/codebase -> proveedor -> identidad no
secreta -> ambiente -> writer -> procedimiento/check/rollback. Estado mutable:
revision/despliegue/fecha de observacion/incidente/pendiente en CURRENT o proveedor.
No extrapolar staging a produccion, mirror a cutover ni health a transaccion.
Tras un cambio de configuracion viva, reconciliar CURRENT con el readback fechado
y la frontera pendiente: habilitado no equivale a login, entrega o transaccion
probados. Una respuesta fail-closed tampoco demuestra el camino de exito.
DO/Railway/Vercel se operan con interfaz pertinente dentro del target autorizado;
servicio instalado o MCP expuesto no concede provisioning o deploy.

En `servidor_do_1`, un diagnostico focal puede hacerlo directamente el principal
con Sol. El autor prepara codigo y un revisor independiente valida el head exacto;
una mutacion remota autorizada la ejecuta un unico `release_operator` Sol medium.
Astra entra solo por una decision transversal real. Verificar siempre alias,
host, proyecto, ruta, servicio, candidato, rollback y readback; un fallo de acceso
no autoriza cambiar de host, key, usuario o target.

SSH y SCP usan exclusivamente el alias `servidor_do_1` con `BatchMode=yes`,
`StrictHostKeyChecking=yes`, `ConnectTimeout` acotado y `ConnectionAttempts=1`. No exponer argumentos/env de
procesos ni logs crudos. El Git remoto selecciona el SHA exactamente revisado y
limpio, no un pull flotante. Un copied-tree usa allowlist/manifest propio del
proyecto, excluye `.env*`, credenciales, sesiones y runtime de artefacto, backup
y overlay, y verifica por readback cada archivo administrado. Sin borrado
autorizado, un overlay es parcial; borrar solo paths removidos expresamente.
