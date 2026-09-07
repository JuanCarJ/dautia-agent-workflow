# Continuidad de producto y entrega · v13

Usar cuando cambien requisitos, diseño, frontera de entrega o decisiones durante
un hilo largo. Para una correccion pequeña basta mantenerlo en contexto.

## Conversar y especificar

El usuario puede hablar naturalmente y decir E2E. Traducir a actor, resultado,
recorrido, restricciones, ambiente, ejemplos positivos/negativos y señal final.
No hacerlo reescribir un prompt perfecto ni convertir una correccion en nuevo
proyecto. Distinguir preferencia nueva, aclaracion, defecto y requisito olvidado.
Conservar la frase fuente cuando una decision cambie el significado del producto.

La conversacion libre, por voz o texto, es entrada valida aunque tenga errores,
repeticiones o alternativas incompatibles. Reconstruir intencion sin convertir
una idea exploratoria en requisito aceptado o autorizacion. Distinguir lo dicho
por el usuario, inferencia del agente y propuesta; conservar ejemplos y motivos
que cambien la interpretacion. Al cambiar materialmente alcance o fase, devolver
una sintesis breve de objetivo, restricciones, decisiones vigentes y dudas
materiales. No resumir cada mensaje ni imponer confirmacion rutinaria: continuar
si aceptacion y autoridad son claras. Preguntar solo cuando la ambiguedad cambie
materialmente resultado, datos, autoridad o reversibilidad; mientras tanto,
continuar el trabajo independiente. Nuevas ideas durante ejecucion se clasifican
como correccion, cambio autorizado o propuesta futura; no ampliar alcance
silenciosamente ni crear documentos o agentes solo por conversar.

Usar la spec/requisitos canonicos existentes. Versionar cambios durables de
comportamiento, contratos, arquitectura o decisiones necesarias para mantenimiento.
Separar propuesto -> aceptado -> implementado -> verificado -> desplegado.
Registrar decision reemplazada y nuevo criterio, no dos verdades vigentes.
Auditoria no cambia la spec salvo captura autorizada; implementar ya autorizado
no necesita otra aprobacion de rutina. Una duda material de negocio sigue abierta.

## Hilos largos

Continuar mientras el resultado sea coherente. Condensar al cambiar de fase o
tras correcciones materiales: decision actual, alcance y exclusiones, baseline,
SHA/candidato, autoridad/target, evidencia valida, pendientes por plataforma y
parada. Un resumen no elimina contexto y un fork conserva historia; no afirmar
ahorro automatico. Abrir tarea nueva por objetivo independiente o preferencia,
con handoff vigente; no por un numero universal de turnos. Descartar planes
reemplazados y outputs voluminosos sin olvidar restricciones del usuario.

## Preservar diseño

Antes de editar: localizar referencia aceptada, componentes/tokens, assets/copy,
estados y delta permitido. Reutilizar sistema del proyecto; no imponer shadcn,
Radix, fuentes, nueva libreria o proveedor por una skill. Comparar candidato y
referencia en mismo estado/viewport, con muestra de desktop/movil pertinente.
Comprobar composicion, jerarquia, legibilidad, recuperacion y valor desde el rol.
No rebaselinar capturas automaticamente para silenciar regresiones.

Controlar linaje: un asset en otro worktree no pertenece al build actual. Antes
de archive/deploy comprobar fuente visual esperada -> commit -> artefacto.
Tests funcionales/overflow no prueban aceptacion visual; reportar pendiente si
no se observa el candidato. Preservar entregables de negocio existentes al
cambiar entradas o flujos (por ejemplo reportes de incidencias).

## Trazabilidad suficiente

Unir requisito/decision -> cambio -> repo/rama/SHA -> prueba/frontera -> artefacto
-> ambiente/target -> estado externo observado. Usar IDs existentes; una correccion
pequeña no necesita matriz nueva. En multi-repo incluir solo repos afectados.
Una plataforma verde no cierra otra: mantener pendientes de iOS/Android/web y
proveedores. Login/health no prueba el campo, WhatsApp o contabilizacion final.
Release conserva orden, artefactos DB, compatibilidad, backup/rollback y postflight.
No repetir operaciones inciertas no idempotentes: reconciliar identidad/estado.

## Aceptacion al delegar y cerrar

Mantener requisito aceptado -> delta -> evidencia -> pendiente en el contexto o
fuente canonica existente. Entregar al ejecutor decisiones, estados, interfaces,
referencia visual, exclusiones y comprobacion; no solo un resumen de conclusiones.
El auditor accede a evidencia original. Un pendiente material no desaparece por
tests verdes, un cambio de modelo ni una frase de cierre. Una decision nueva o
contradiccion vuelve al responsable. No duplicar auditoria por cada correccion.
