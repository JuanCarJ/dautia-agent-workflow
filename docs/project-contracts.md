# Contrato minimo de un proyecto

Esta pauta sirve para incorporar un proyecto nuevo o migrar uno existente sin
copiar el workflow global dentro del repositorio.

## Archivos del producto

- `AGENTS.md`: hechos locales, limites de dominio, comandos propios y
  restricciones por plataforma. No duplica el contrato global.
- `delivery.yaml`: repositorios, codebases, rama de integracion, ambientes,
  checks, targets, provider refs no secretos y rollback.
- `docs/CURRENT.md`: ultimo estado externo realmente comprobado. Puede omitirse
  si el producto no tiene estado mutable externo.
- documentacion funcional, arquitectura, datos y runbooks solo cuando el
  comportamiento u operacion los necesite.

No agregar `.agents/skills`, `.cursor/skills`, agentes globales, perfiles de
modelo, telemetria del harness ni copias de este repositorio.

## Migracion inicial

1. Identificar el repo canonico y descartar copias, worktrees y proyectos
   retirados.
2. Verificar remoto, rama de integracion, ramas de ambiente y proveedores sin
   inferir deploys desde documentos.
3. Crear o validar `delivery.yaml`. Si falta infraestructura esencial, dejarlo
   `draft` con el bloqueo concreto; no inventar un contrato activo.
4. Reconciliar `AGENTS.md` y `CURRENT.md` con codigo y proveedor observado.
5. Validar localmente y publicar en la rama de integracion. Documentacion sola
   usa `[skip ci]` cuando no existe un check remoto obligatorio.
6. Registrar el producto en la matriz central; no copiar skills.

## Trabajo entre Mac y WSL

- Cada host usa un clon independiente y credenciales propias.
- Git sincroniza commits; nunca `.git`, worktrees, env, sesiones, caches,
  certificados o artefactos de build.
- Dos hosts no escriben la misma rama simultaneamente. El segundo parte de la
  rama remota vigente o trabaja en una rama corta distinta.
- Web, backend, Android, DB, docs y CLI de proveedores pueden ejecutarse en WSL
  si `delivery.yaml` lo permite. iOS/Xcode/codesign/TestFlight/App Store se
  cierran en Mac.

## Implementacion y despliegue

- Implementacion termina en la `integration_branch` de cada repo afectado.
- Un push de integracion no concede deploy. Release fija SHA, ambiente, alcance,
  proveedores, orden, rollback y condicion de parada.
- En multi-repo, fijar todos los SHAs compatibles; no mezclar una version nueva
  de un contrato con un consumidor viejo.
- DB transporta migraciones inmutables, no filas. Aplicar por ambiente con
  preflight, backup proporcional y reconciliacion.
- Validar localmente por riesgo. GitHub Actions solo cuando sea gate requerido o
  haga falta un runner que no exista localmente.

El comando canonico de validacion es:

```bash
python3 ~/.codex/skills/dautia-ci-cd/scripts/validate_delivery.py \
  delivery.yaml --repo .
```

En WSL, donde las skills compartidas viven en `~/.agents/skills`, usa:

```bash
python3 ~/.agents/skills/dautia-ci-cd/scripts/validate_delivery.py \
  delivery.yaml --repo .
```
