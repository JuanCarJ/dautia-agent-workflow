# Contratos de proyecto y entrega heterogénea

El workflow global no se copia dentro de cada producto. AGENTS contiene límites
locales y procedimientos; delivery identifica topología, ramas, componentes y
entornos; CURRENT conserva únicamente estado observado que no deba consultarse
en otra fuente vigente. No instalar aquí skills globales, sesiones o telemetría.

## Compatibilidad

Los contratos 1 y 2 conservan su validador exacto en validate_delivery_legacy.py.
El esquema 3 añade ramas de integración por repositorio y targets por componente.
No se migra ningún producto automáticamente. El ejemplo sintético se encuentra en
`skills/dautia-project-cycle/examples/delivery-v3-multirepo.json`.

El formato continúa siendo JSON compatible con YAML 1.2, no YAML arbitrario.
Campos principales: schema_version=3, project, product_topology, repository_layout,
configuration_status, production_enabled, repositories, codebases, targets y
provider_projects opcional. Configuración draft deshabilita producción y contiene
un motivo, no destinos que aparenten estar activos.

Cada repository declara id/path/integration_branch. Cada codebase declara
id/repository/path/kind/status y opcionalmente required_capabilities. Cada target
vincula id/component/environment/state/deploy_enabled/target/checks/rollback_ref,
y branch/provider cuando corresponda. El target integration coincide con la rama
DE SU repositorio, no con una rama global. Cada componente activo tiene target de
integración. El nombre main no concede despliegue y dev no es una rama universal.

provider_projects vincula id/provider/component/environment/target_id/workdir;
workdir es relativo al repositorio del componente. Supabase añade project_ref,
conserva validación específica y solo staging/production para estos destinos.
Dos componentes pueden usar el mismo proveedor y entorno sin colisionar. Una
selección ambigua se rechaza; nunca se escoge el primer destino silenciosamente.
Los proveedores distintos se representan sin fingir que el validador los consultó.

```sh
python3 skills/dautia-ci-cd/scripts/validate_delivery.py delivery.yaml --repo .
python3 skills/dautia-ci-cd/scripts/check_checkout.py delivery.yaml --repo . --json
# Para varios destinos Supabase v3, después de verificar el contrato:
# dautia-supabase --component backend --target-id backend-staging run --environment staging -- ...
```

Los comandos de Supabase y credenciales siguen perteneciendo al wrapper existente.
Esta revisión cambia resolución de target, no concede DDL/MCP, psql ni nuevos
fallbacks. Las consultas Git son locales: no certifican la frescura del remoto.
check_checkout observa el espacio; su closeout requiere un packet de objetivo y no
obliga a cambiar de rama a un hilo activo. La evidencia de integración se obtiene
independientemente, no se inventa a partir de un status limpio.

## Candidato y cierre

Un cambio multirepo fija el conjunto compatible de revisiones, contratos,
configuraciones y artefactos. Ordena integración/promoción por dependencias.
Una variación material invalida solo evidencias dependientes. Un rollback entre
proveedores no es una transacción atómica: explicitar compensaciones y límites.

Config/operación sin Git usa host/servicio/fingerprint/readback, no PR ficticio.
Mac y WSL conservan credenciales y herramientas propias. No se sincronizan .git,
caches, certs, sesiones ni logs activos. iOS/Xcode requiere su host real; los
fixtures de política en Linux no validan un dispositivo Apple.

El output por cierre distingue cambio propio preservado/integrado, validación,
estado externo y workspace reconciliado. Los cambios ajenos pueden seguir allí.
Retirar un workspace exige revisar trabajo posterior, artefactos valiosos y uso
activo; no se decide por la edad o por ver un PR merged.
