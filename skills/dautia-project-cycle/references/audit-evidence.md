# Dictamen y evidencia de auditoria · v12

Aplicar a auditorias sustantivas de producto, UI o tecnica. Una consulta breve
puede resolverse en un parrafo; no crear una matriz, documento o agente por rito.

## Afirmar solo lo demostrado

Separar observacion reproducida, explicacion inferida del codigo y propuesta.
Por hallazgo material conservar estado/actor, evidencia, impacto, confianza o
limite y criterio de correccion. No confirmar la hipotesis del usuario por cortesia.
Si se usan severidades, usar primero la escala del proyecto. En ausencia de ella:
P0 exige impacto critico demostrado que requiera atencion inmediata; P1 afecta
seriamente un recorrido principal; P2 es friccion o defecto acotado; P3 es mejora.
Un nombre interno visible no demuestra fuga de informacion sensible. Indicar lo
observado y la incertidumbre sin rebajar un incidente confirmado.

"Sin errores de consola" prueba esa observacion; no prueba toda la funcionalidad,
accesibilidad, conversion o seguridad. Un antes/despues visual no demuestra mejora
de conversion sin medicion. No prometer que un patron generico es el diseño final.
Distinguir candidato local y entorno observado. Vincular SHA/artefacto cuando
se atribuya un defecto desplegado al codigo; si no se puede, declarar atribucion
no confirmada y conservar la observacion de UI. No bloquear la auditoria por eso.

## Evidencia compacta, con fuente recuperable

Leer las instrucciones completas una vez; para codigo, logs, tablas o DOM buscar
primero el simbolo/estado y recuperar contexto suficiente alrededor. Guardar un
resultado grande solo en el lugar privado de artefactos permitido, sin secretos;
mostrar fragmentos pertinentes, fallos, identidad y ruta. No imprimir el resultado
completo para luego resumirlo. Los limites de herramientas pueden no bastar:
filtrar por tipo y presupuesto total antes de emitir. Un texto rutinario mayor
a 10.000 caracteres necesita reduccion o una razon concreta; nunca cortar el
fallo relevante. Imagen/binario no se cuentan como ruido textual.
No repetir snapshot si la accion ya entrego uno vigente del mismo estado; renovar
refs tras cambios reales. Capturas representativas conservan la evidencia visual.

## De auditoria a implementacion

La recomendacion sigue propuesta hasta quedar aceptada por el usuario o el
contrato vigente. Distinguir discrecion reversible de layout de decisiones sobre
precios, elegibilidad, permisos, datos o taxonomia. Estas ultimas no se inventan.
Resolver la contradiccion material antes del bloque dependiente y continuar el
trabajo independiente. No preguntar por detalles ya autorizados o convencionales.
Conservar referencia visual, tokens/assets, estados y delta permitido; comparar
el candidato en estado/viewport equivalente. No sustituir el sistema del proyecto.

En busqueda/filtros, definir cuando afecte el delta: OR/AND dentro y entre facetas,
conteos disyuntivos o combinados, producto frente a variante disponible, aplicacion
inmediata o pendiente, URL/retroceso y tratamiento de cero resultados. No declarar
incorrecto un conteo global sin explicitar que promete la UI. Ocultar, deshabilitar
y conservar una opcion seleccionada son decisiones distintas. Evitar absolutos
como "nunca cero resultados": enlaces viejos y cambios de stock necesitan una
recuperacion verificable. El mapeo de familias de color no elimina variantes.
Otros dominios conservan sus invariantes equivalentes, no copian esta taxonomia.

Verificar la frontera afectada y declarar lo no probado. Tras una correccion,
reutilizar evidencia vigente y repetir solo lo invalidado. Un revisor recibe
fuentes originales y una pregunta material, no solo conclusiones del autor.

## Revision independiente y entrega de codigo

El autor prepara codigo/config de producto versionado, pruebas/docs pertinentes y
PR sobre la base permitida. La revision recibe intencion/aceptacion originales,
exclusiones, repo/PR/base/head, diff y evidencia recuperable. No basta el resumen
del autor. El principal solicita un revisor independiente del candidato; no un
panel por defecto. Una correccion pequeña recibe una revision pequeña.

Cada hallazgo material enlaza requisito o invariante, evidencia, impacto y reparacion
minima; separar bloqueante de mejora opcional e incertidumbre. El revisor puede
inspeccionar y probar, pero no cambia el producto ni se autocertifica. El autor
corrige dentro del alcance aceptado; decisiones nuevas vuelven al responsable.

Comparar aceptacion original con lo que afirman las pruebas, no solo con su verde.
Una prueba contradictoria no autoriza reemplazar el requisito ni aprobar el
candidato. El revisor devuelve ese hallazgo al autor; nunca corrige el test. El
autor puede corregir la prueba dentro de autoridad vigente si la intencion es
inequivoca. Si fuente/test son inmutables o falta una decision, conservar conflicto
y frontera pendiente, sin dictamen favorable de esa aceptacion.

Publicar checklist/comentarios del PR cuando esa comunicacion esta autorizada por
el encargo. Con la misma cuenta GitHub no fingir aprobacion nativa independiente.
Un nuevo head invalida el dictamen favorable hasta revisar el delta; cambios de base
requieren reconciliar compatibilidad. Repetir solo pruebas cuya frontera cambio.
Merge exige dictamen favorable del candidato vigente, checks requeridos y autoridad
al target ya concedida o el go pendiente. No pedirla otra vez si estaba vigente.
El autor delegado devuelve el candidato; principal u operador autorizado integra.

Releer candidato/checks remotos antes de merge; no inferir GitHub desde un archivo.
Identificar autodeploy; merge no concede apply de migracion, cutover, upload ni otro
target. Una excepcion al PR necesita instruccion/contrato explicitos; prohibir ramas
cortas no demuestra imposibilidad. Preparar el candidato mientras se resuelve una
incompatibilidad real. No añadir protecciones, daemon de merge ni vigilancia perpetua.
Config viva/datos/artefactos manuales siguen su autoridad y readback, sin PR ficticio.
Fuentes globales sin Git usan respaldo, diff y revision proporcionada.

## Checklist de promocion

"Haz el checklist para pasar de staging a main/produccion" pide preparar y
verificar readiness; no ejecuta merge/deploy por si solo. Resolver el mapa real
rama -> ambiente/proveedor (main no siempre es produccion), base/head y artefacto
observado en staging. Conservar la autoridad previa y distinguirla de la orden de
ejecutar; no pedir otro go cuando ya se ordeno promover al quedar conforme.

Comprobar aceptacion, delta acumulado desde produccion, revision independiente
favorable del candidato vigente y ausencia de bloqueantes. Reutilizar el dictamen
vigente; si falta o cambio head/base, obtener revision independiente de lo no cubierto.
Elegir pruebas por impacto: focales y regresion del modulo para cambios acotados;
integracion y E2E del recorrido afectado cuando contratos, Auth, datos, routing,
cache o proveedores cambian esa frontera. No exigir suite completa por ceremonia
ni sustituir evidencia necesaria por build verde. Registrar revision -> frontera ->
prueba -> resultado y el alcance no observado; reutilizar verde aun valido.

Antes de declarar listo comprobar checks requeridos, compatibilidad de ambientes,
migraciones si aplican, secuencia y rollback concreto, y autodeploy al mergear.
Entregar listo, bloqueado o pendiente con evidencia y autoridad por separado; un
E2E necesario sin acceso/fixture queda pendiente y no se certifica. El checklist
puede ejecutar comprobaciones dentro de autoridad vigente; si requieren un efecto
no autorizado, completar lo independiente y señalar esa frontera. La promocion
posterior autorizada exige readback del artefacto/SHA servido y smoke pertinente;
merge, deploy y verificacion externa siguen siendo estados diferentes.
