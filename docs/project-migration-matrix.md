# Matriz de migracion de proyectos

Corte: 2026-08-28. Esta matriz clasifica compatibilidad y gobernanza; no intenta
registrar SHAs desplegados ni reemplaza el `CURRENT.md` de cada producto.

## Migrados y activos

| Producto | Repositorios gobernados | Integracion | Windows/WSL | Restriccion principal |
| --- | --- | --- | --- | --- |
| Ryven / SideQuest | `sidequest` | `dev` | Web, admin, marketing, docs, Android, Supabase | Xcode, Simulator, firma, TestFlight y App Store solo Mac |
| MyRoof | `myroof` | `dev` | Web, backend, docs, Android y proveedores compatibles | iOS y firma Apple solo Mac |
| Templo Rojo | `templorojo-ecommerce` | `staging` | Web, Supabase, pruebas y release autorizado | Staging integra; produccion sigue en `main` |
| MaderCore | `madercore` | `dev` | Web, worker, OpenClaw, Supabase y servidor | El unico DB externo actual documentado es produccion; pruebas DB siguen bloqueadas sin staging |
| Hommy | `hommy-frontend`, `hommy-backend` | `dev` en ambos | Web, API, PostgreSQL, docs y servidor | El staging de backend existe, pero la rama `staging` sigue planificada |
| Studio Z Academy | `studioz-academy` | `dev` | Next.js, Supabase, Playwright y proveedores web | Resolver identidad de cada Supabase antes de DB o release |
| FTC Solar | `ftc-solar-landing` | `dev` | Landing Vite completa | `master` es el sitio publico; no existe Android vigente |
| Redecarga / RedeCore | governance, backend, landing, descargador Solex, demo y demo backend | `dev` por repo | Web, backend, documentos, OpenClaw y servidor | Cerrar cada incremento con matriz repo-rama-SHA |

Los contratos existentes y validos de SideQuest, MyRoof, MaderCore y Redecarga
se conservan. No se reescriben solo para repetir reglas globales.

## Migrado pero bloqueado

| Producto | Estado | Para activarlo |
| --- | --- | --- |
| Habilis | Repositorio privado publicado en `JuanCarJ/habilis`; contrato `draft` | Provisionar Supabase staging, ramas/ambientes, targets de despliegue y rollback verificable; despues activar el contrato |

## Excluidos deliberadamente

- `Sam/territorios/Territorios`: remoto de terceros. Se puede auditar en lectura,
  pero nunca hacer push ni cambiar su gobernanza.
- familia `CalenAgent`: descartada del alcance vigente; no se revive ni migra por
  presencia en disco.
- `ftc-solar-monitor`: descartado; el unico producto FTC vigente es
  `solarftc.com`.
- worktrees, clones `*-release` y copias operativas: no son productos ni fuentes
  canonicas y nunca reciben contratos propios.

## Inventario no promovido automaticamente

Los repositorios historicos de Auto Damage Advisors, DautIA Web, Huella Global,
Madercenter site, Panagro, Pigasus, Pizzeria y WorldWinds permanecen fuera del
perfil activo hasta que el usuario confirme que vuelven a desarrollo. Su mera
existencia o una fecha reciente no autoriza crear ramas, remotos, ambientes o
despliegues.

## Regla de contenido

Un repositorio de producto no contiene las skills ni los agentes del workflow.
Solo conserva reglas del producto, topologia de entrega, estado, codigo,
migraciones, pruebas y runbooks propios. El workflow se instala desde
`dautia-agent-workflow` en cada host.
