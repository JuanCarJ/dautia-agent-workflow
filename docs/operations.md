# Operacion entre Mac y Windows

## Trabajo paralelo

- Cada host mantiene un clon independiente.
- Dos hosts no escriben simultaneamente la misma rama.
- Cada incremento parte de la rama de integracion remota vigente.
- Un solo integrador incorpora las ramas cortas y actualiza `CURRENT.md`.
- En multi-repo, el cierre informa `repo -> rama -> SHA -> evidencia`.
- No se sincronizan `.git`, worktrees, `.env`, caches ni artefactos de build.

Ryven y MyRoof permiten web, documentacion, Supabase y Android desde WSL. Las
fronteras iOS se cierran en Mac. Los demas proyectos portables pueden trabajarse
en cualquiera de los dos hosts cuando su remoto y `delivery.yaml` esten activos.

## Despliegues

El host ejecutor debe tener un checkout limpio del SHA autorizado y las
credenciales locales. Los scripts del producto son la interfaz de despliegue;
el workflow global no contiene IDs mutables ni secretos.

Antes de desplegar desde otro host, verificar proveedor, target, revision
actual, rollback y que no exista otra transaccion sobre el mismo ambiente.
