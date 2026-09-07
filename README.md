# DautIA Agent Workflow

Fuente versionada del workflow agentico de DautIA. Es independiente de los
repositorios de producto y puede instalarse en macOS o WSL para que Codex y
Cursor compartan los mismos contratos, skills y roles sin compartir secretos.

## Que contiene

- `AGENTS.md`: contrato global, neutral respecto al harness y al modelo.
- `skills/`: skills personales portables en el estandar `SKILL.md`.
- `roles/`: definiciones canonicas de roles, sin fijar proveedor de modelo.
- `adapters/`: representaciones generadas para Codex y Cursor.
- `profiles/`: capacidades y routing propios de macOS y WSL.
- `docs/`: arquitectura, operacion e instalacion.
- `scripts/`: instalacion, diagnostico, render y validacion local.

Los proyectos conservan en sus propios repositorios `AGENTS.md`,
`delivery.yaml`, documentacion funcional, migraciones y scripts de release.
Este repositorio no contiene variables de entorno, tokens, passwords,
certificados, sesiones ni memorias.

## Validacion rapida

```bash
python3 scripts/render_agents.py --check
python3 scripts/check_portability.py
python3 scripts/install.py --profile codex-macos --scope routing --check
```

La comprobacion completa `--scope all --check` se ejecuta por separado y puede
mostrar deriva historica en skills que no pertenecen al cambio de routing.

Consulta [la arquitectura](docs/architecture.md) y la
[instalacion en Windows](docs/windows-installation.md). La
[matriz de proyectos](docs/project-migration-matrix.md) define que se migra y la
[pauta de contratos](docs/project-contracts.md) evita copiar el workflow dentro
de cada producto.

Las rutas de instalacion siguen los mecanismos documentados de cada harness:
Codex macOS conserva su home actual; Codex y Cursor en WSL comparten Agent Skills
desde `~/.agents/skills`. El repositorio no instala plugins de Cursor.

## Routing v13

El alcance `python3 scripts/install.py --profile codex-macos --scope routing --apply`
actualiza AGENTS, dautia-project-cycle y los 16 roles con respaldo. El check del
mismo alcance demuestra solo esos assets; `--scope all --check` sigue mostrando
la deriva historica de otras skills. No aplicar todo para corregir routing.
La raiz debe estar en Sol high en la configuracion local; el instalador no edita
config.toml ni cambia sesiones activas. Cursor hereda su selector, no garantiza
los perfiles de Codex. Otros hosts requieren instalacion y validacion propias.

Descubrimiento focal usa Astra low; implementacion sustantiva resuelta usa Sol
medium con bloque independiente y trabajo concurrente util. Sol high implementa
cuando quedan decisiones tecnicas acopladas; Astra medium cuando la incertidumbre
es transversal o arquitectura y ejecucion siguen inseparables. La revision del
head final sigue siendo independiente. Esta asignacion es una politica operativa,
no evidencia de superioridad o ahorro.
