# Arquitectura portable

## Capas

1. **Nucleo DautIA:** autoridad, cuatro modos, Gitflow, pruebas, seguridad,
   documentacion y cierre. No depende de un modelo o plugin.
2. **Skills:** conocimiento procedural portable. Una skill puede declarar una
   capacidad requerida, pero no imponer un harness cuando existe un equivalente.
3. **Roles:** responsabilidad, mutabilidad, entrada y salida de un especialista.
4. **Adaptadores:** convierten roles a los formatos de Codex y Cursor.
5. **Perfiles:** mapean plataforma, capacidades y modelos disponibles.
6. **Proyecto:** su `AGENTS.md` y `delivery.yaml` prevalecen para hechos locales.

El rigor se mide por resultado, autoridad, evidencia y estado externo. No exige
que Sol, Grok, Fable, GLM u otro modelo usen los mismos pasos internos.

## Repositorios de producto

Los repositorios de producto no reciben una copia completa del workflow.
Conservan solamente:

- contrato local `AGENTS.md`;
- topologia y Gitflow estable en `delivery.yaml`;
- estado mutable en `docs/CURRENT.md` cuando aplique;
- documentacion funcional y tecnica del producto;
- scripts de build, migracion, prueba y release propios.

## Skills y plugins externos

Un plugin externo puede complementar capacidades, pero no cambia autoridad,
ambiente, Gitflow, criterios de aceptacion ni condiciones de parada. Este
repositorio no instala ni configura `pstack`; cualquier experimento de Cursor
vive fuera del perfil estable y se evalua contra `conformance/cases/`.

## Infraestructura compartida

Git es el plano de sincronizacion. Vercel, Supabase, DigitalOcean, OpenClaw y
Google Play pueden operarse desde macOS o WSL cuando el proyecto lo declara y
el host tiene credenciales locales. Xcode, firma Apple, Simulator, TestFlight y
App Store Connect permanecen en macOS.

Una release tiene un solo propietario y fija `(SHA, target, alcance, host)`.
Otro host puede continuar trabajo de codigo, pero no ejecutar simultaneamente
la misma transaccion de release.
