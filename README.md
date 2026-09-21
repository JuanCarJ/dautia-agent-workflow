# DautIA Agent Workflow · contrato 15 / r3

Workflow portable para Codex y Cursor, separado de los productos. Esta revisión es
un candidato de piloto: controles ejecutables y pruebas locales no equivalen a
validación real de modelos, Desktop, dispositivos o proveedores.

Sol 5.6 high permanece en el principal. El implementador definido usa medium;
la ejecución técnicamente exigente usa high. Jev puede evaluar medium/high y
análisis Sol/Astra sin autorizar acciones. Las skills conservan sus criterios.
[Routing r3.2](skills/dautia-project-cycle/references/model-routing.md) describe
selección, destinos generados y verificación del despacho; no activa Jev.
No se incorpora un fork de FirstMate ni un supervisor adicional.

## Fuentes y generación

- `AGENTS.md`: autoridad, modos y obligaciones comunes.
- `skills/`: métodos, referencias y helpers.
- `roles/`: los 16 roles canónicos y una frontera compartida `_boundary.md`.
- `profiles/`: configuración de cada host; no prueba de capacidades disponibles.
- `scripts/render_agents.py`: genera adaptadores desde esas fuentes al instalar.
- `workflow-version.json`: versión del candidato y baseline.

Los adaptadores generados dejaron de ser copias normativas mantenidas en Git:
se generan en un directorio temporal/instalación. No copiar el workflow global a
cada repositorio de producto. Los proyectos conservan sus specs, reglas, delivery,
migraciones y procedimientos propios.

## Comprobar e instalar

Python 3.11+, macOS o Linux/WSL. No se necesita SDK ni red para los tests.

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/render_agents.py --check
python3 scripts/check_portability.py
python3 scripts/install.py --profile codex-macos --scope workflow --check
```

El preview no modifica instalación. Tras reconciliar conflictos:

```sh
python3 scripts/install.py --profile codex-macos --scope workflow --configure-root --apply
```

En WSL usar `--profile wsl-shared`; respeta CODEX_HOME y comparte skills en
`~/.agents/skills`. Ediciones locales desconocidas bloquean la instalación: no usar
`--adopt-existing` sin inspección; ese flag adopta exactamente los archivos previstos
con respaldo. Nunca borra archivos ajenos. No modifica sesiones ni activa hooks.

Guía: [setup y piloto](docs/r3-setup.md). Modelo/capacidades reales y hooks necesitan
smoke en cada host. Cursor hereda su selector: no se anuncia paridad de routing.

## Jev

```sh
dautia-jev setup --mode shadow --store-key
dautia-jev doctor
dautia-jev probe --allow-network
```

Sin setup queda off; la clave nunca va en Git/chat/argumentos. Probe envía contenido
sintético y consume API. La precisión/umbrales requieren evaluación propia.

## Multirepo y auditorías

Delivery schema 3 admite ramas por repositorio y targets/proveedores por componente.
Los validadores y la ejecución de credenciales v1/v2 se preservan en módulos legacy;
no se migran productos automáticamente. Ver [contratos](docs/project-contracts.md).
La auditoría Git se ingiere en lectura; no inicia limpieza o recuperación.
[Estado de implementación](docs/r3-implementation.md) separa código, tests locales,
pruebas pendientes de host y evidencia Git que todavía no se ha recibido.
