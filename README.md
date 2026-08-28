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
python3 scripts/install.py --profile codex-macos --check
```

Consulta [la arquitectura](docs/architecture.md) y la
[instalacion en Windows](docs/windows-installation.md).
