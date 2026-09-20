# Infraestructura compartida — r3

Leer solo la frontera de proveedor/host afectada. Identidades y procedimientos
pertenecen al proyecto; esta referencia no demuestra su estado externo actual.
La selección de modelos pertenece únicamente a model-routing.md y su política.

## Supabase

Conservar `dautia-supabase`, sesión de cuenta por host y password por project_ref.
El registro protegido ~/.config/dautia/supabase-db-credentials.json usa 0600.
No copiar secretos entre hosts, proyectos, argumentos, logs, Git o chat. Tokens
publishable, service-role o access no sustituyen password DB. Ejecutar el wrapper
fijado por el proyecto; nunca supabase/npx directo, psql o versión improvisada.
Un prompt repetido revela onboarding/ACL/bypass pendiente, no permiso para pedir
otra clave. Consultar solo la referencia de credenciales pertinente de CI/CD.

Tests con DB requieren staging verificado, nunca DB local o producción. MCP es
lectura; DDL versionado via wrapper con autoridad de ambiente. Git transporta
migraciones inmutables, no filas. Producción requiere identidad, historial,
backup/PITR, compatibilidad y postflight; usar expansión/migración/contracción si
corresponde. Un esquema de delivery válido no acredita ninguna de esas ejecuciones.

## Apple y móvil

Codesign/ACL se prepara en Keychain; no publicar contraseñas o certificados. Usar
el wrapper archive/export del proyecto, no introducir otro pipeline por una skill.
Prompt recurrente implica una frontera de acceso, no reintentos infinitos.
Mac posee Xcode, Simulator y firma; WSL no certifica iOS.

Regresión amplia con mocks/fakes; smoke real focal cuando cambie la frontera, con
build, dispositivo, provider mode, operaciones máximas, cuota y parada. Mantener
Google Maps/Navigation, Sign-In, APNs o StoreKit según contrato real del producto.
Una prueba offline no se presenta como live por conservar el mismo nombre de caso.
Fuente, build instalado, archive, upload, procesamiento y distribución son estados
distintos. Si cambian empaquetado/config/cache, inspeccionar el artefacto y el
upgrade pertinente sin revelar secretos. Una instalación limpia no prueba upgrade.

Un operador controla cada simulador/dispositivo/browser mutable. Otros auditores
pueden leer evidencia o usar recursos aislados, no interferir con el gesto activo.
QA que necesita preparar código/tests vuelve al principal para el escritor;
completar lo automatizable antes de devolver únicamente la acción física pendiente.

## Hosts y proveedores

Mac y WSL conservan credenciales/sesiones propias. No sincronizar por Git caches,
worktrees, binarios o env. Colima permanece no disponible. Un operador de release
posee candidato/target/alcance/host; otros hosts aportan pruebas, no promocionan.

El mapa estable vincula repo/codebase/proveedor/entorno/identidad/procedimiento;
el estado mutable tiene fecha y readback. No extrapolar staging a producción,
mirror a cutover o health a transacción. Una respuesta fail-closed tampoco prueba
el camino de éxito. No instalar/provisionar por tener una herramienta disponible.

En servidor_do_1 se permite diagnóstico focal directo autorizado. Para SSH/SCP
usar su alias con BatchMode=yes, StrictHostKeyChecking=yes, ConnectTimeout acotado
y ConnectionAttempts=1. No revelar argumentos/env de procesos o logs crudos.
Verificar host, proyecto, ruta, servicio, candidato, recuperación y resultado.
Fallo de acceso no autoriza otro usuario, host, clave, proveedor o target.

Git remoto selecciona el SHA revisado, no pull flotante. Un copied-tree usa
allowlist/manifest, excluye env/credenciales/sesiones/runtime y verifica readback.
Borrar solo rutas removidas expresamente y con autoridad; un overlay sin esa
reconciliación es parcial. Si una operación pudo tener efecto antes de fallar,
reconciliar por identidad antes de repetirla. Nunca contabilizar/enviar dos veces
para completar la evidencia. Config viva y computer-use tienen sus propias
fronteras de lectura/guardar/enviar/publicar; no necesitan un PR ficticio.
