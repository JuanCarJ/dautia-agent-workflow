# Modelos y perfiles efectivos · v13

Politica revisada el 7 sep 2026; high es una base conservadora provisional. La evidencia disponible no demuestra
igual calidad o ahorro en implementaciones. Elegir por decisiones pendientes,
acoplamiento, profundidad tecnica, evidencia disponible y costo total del ciclo.
La sensibilidad aumenta exigencia de evidencia; no fija por si sola el esfuerzo.

| Bloque | Perfil | Destino efectivo |
|---|---|---|
| Operacion simple verificable | Sol low | dautia-quick; script cuando determinista |
| Conversacion habitual, aceptacion y orquestacion | Sol high | raiz / dautia-talk / dautia-build |
| Consulta breve o ejecucion definida | Sol medium | dautia-defined / implementer |
| Descubrimiento focal sustantivo de requisitos, estados e impactos | Astra low | product_discovery |
| Interacciones tecnicas moderadas | Sol high | dautia-technical / implementer_complex |
| Pregunta tecnica profunda y delimitada | Sol xhigh | dautia-reason o agente default con override explicito |
| Juicio focal con evidencia suficiente | Astra low | dautia-review / ux_auditor; hipotesis a evaluar |
| Auditoria transversal o decisiones abiertas acopladas | Astra medium | dautia-analysis / systems_analyst |
| Implementacion con decisiones todavia acopladas | Astra medium | dautia-complex / systems_implementer |
| QA profundo o revision tecnica material | Sol high | especialistas QA / independent_reviewer / decision_gate |
| Runbook de release resuelto | Sol medium | release_operator; devuelve incompatibilidades al responsable |

Techo Astra medium. Sol max/ultra y Astra high/xhigh/max/ultra quedan fuera.
No hay equivalencia demostrada entre Astra low y Sol xhigh ni escalera obligatoria.
Una pantalla puede contener incertidumbre transversal; una tarea larga por builds
puede ser mecanica. Sol high no es seguro universal ni xhigh paso previo a Astra.
Falta de acceso, fixture o dispositivo requiere resolver evidencia, no esfuerzo.

Astra pasa a Sol con decisiones/interfaces/invariantes/aceptacion resueltas y un
bloque independiente cuyo ahorro compense el handoff. systems_implementer conserva ejecucion
breve o acoplada; systems_analyst permanece exclusivamente en lectura. En este host max_depth=1: un hijo Astra devuelve el bloque
resuelto al principal para que este despache a Sol; no crea nietos. No añadir auditoria Astra final ni separar redaccion por defecto.
El dueño conserva requisito -> cambio -> evidencia -> pendiente. Revisores reciben
fuentes originales, candidato y pregunta de riesgo; no solo conclusiones del autor.
Smokes conocidos se ejecutan directamente sin convocar especialistas de QA profundo.

systems_analyst (Astra medium) devuelve a la raiz un plan ejecutable: decisiones
resueltas y pendientes, bloques con limites de propiedad, dependencias y orden,
aceptacion y pruebas focales por bloque. Puede recomendar roles/perfiles; solo
la raiz los selecciona y despacha con el contexto resuelto. El analista no edita
codigo, specs o archivos de plan, no integra ni crea o dirige subagentes. Puede
inspeccionar fuentes y realizar comprobaciones no mutantes. Si la arquitectura
sigue inseparable de implementar, informa esa frontera a la raiz; no asume
el rol systems_implementer por iniciativa propia.
Revision focal del contrato de este rol: 2026-09-07.

## Aplicacion real

config.toml fija Sol high para raiz y default subagente. implementer permanece
Sol medium como destino de implementacion sustantiva definida; product_discovery usa Astra low cuando el
descubrimiento es focal y sustantivo. No usarlo para una aclaracion breve. Cada agents/<rol>.toml
fija su modelo/esfuerzo y puede prevalecer sobre argumentos de spawn. No fingir un
override incompatible: usar perfil, rol apropiado o agente default con override
admitido. La skill no cambia el modelo raiz. La app conserva selector por tarea.
CLI: codex -p dautia-build; perfiles v2 ~/.codex/dautia-*.config.toml.
dautia-deep se retiro; no reutilizarlo como alias silencioso de otro esfuerzo.
El selector compartido oculta max/ultra; high/xhigh deben seguir visibles para Sol,
por lo que el techo especifico de Astra es politica y perfiles, no un bloqueo
tecnico contra una seleccion manual. Verificar modelo/esfuerzo observado.
Sesiones existentes requieren recarga efectiva; otros hosts no se sincronizan solos.

Compartir skills y verdad de dominio, sin catalogos duplicados por modelo. Adaptar
handoff a decisiones pendientes, no a estereotipos de marca. Medir raiz, hijos,
relectura y reintentos. Tokens no son facturacion del plan; razonamiento pertenece
a salida. Standard por defecto; Fast solo por necesidad de latencia autorizada.

## Seleccion y evaluacion

Conservar Sol high como base habitual provisional y Sol medium para bloques
definidos. El cambio corrige una adopcion insuficientemente validada; no demuestra
que medium causara defectos ni que high los impida. Astra low y
Sol xhigh son rutas disponibles a evaluar, no defaults por etiqueta UI/concurrencia.
Comparar medium/high en cambios definidos, Astra low/medium en juicio focal y
Sol high/xhigh/Astra low en logica profunda; probar Astra medium directo frente a
handoff cuando el acoplamiento haga dudoso el ahorro. Mismas condiciones de calidad.
Si falla una comprobacion, distinguir requisito omitido, decision nueva, defecto
tecnico y problema de herramienta antes de cambiar perfil. No bajar esfuerzo para
ocultar consumo ni subirlo para evitar observar el producto. [Evaluacion](evaluation.md).

Fuentes: https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6
https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra
https://learn.chatgpt.com/docs/pricing

## Decision operativa por bloque

Distinguir obligaciones de resultado, reglas condicionales de ruta y preferencias
de eficiencia. Autoridad, requisito aceptado, evidencia pertinente y perfil real
no admiten excepcion silenciosa. Una preferencia de paralelismo no obliga a crear
trabajo inutil. La raiz conserva la responsabilidad de integracion y cierre.

Al iniciar trabajo sustantivo o cambiar materialmente decisiones/acoplamiento,
resolver en el plan/contexto existente: requisito vigente, decision pendiente,
perfil/ruta, frontera de regresion y señal de terminado. No repetir por comando.
Antes de actuar sobre el bloque dependiente:

- Si la implementacion sustantiva esta definida, delegar a implementer Sol medium
  cuando haya bloque independiente y trabajo util concurrente. Raiz high conserva
  aceptacion, coordinacion y cierre. Directo solo para delta minimo, handoff mas
  costoso que el trabajo o ausencia de trabajo concurrente util; indicar motivo
  una vez. No fabricar paralelismo ni usar la excepcion para absorber una feature.
- Si requiere reconciliar requisitos, estados e impactos sustantivos, resolver
  descubrimiento focal con product_discovery Astra low si existe bloque
  independiente y trabajo util concurrente. Una aclaracion breve queda en raiz.
  Incertidumbre transversal abierta pasa a systems_analyst Astra medium.
- Si coordina contratos tecnicos como consulta/URL/disponibilidad, usar Sol high
  o superior dentro del techo: raiz compatible o implementer_complex para un
  bloque independiente. No continuar silenciosamente en medium por inercia.
- Para auditoria sustantiva de producto/UI con alternativas abiertas y evidencia,
  usar juicio Astra low; raiz Astra low/medium equivalente puede resolverlo.
  Delegar ux_auditor cuando exista bloque independiente y trabajo util concurrente
  (por ejemplo, revisar cobertura de regresion sin duplicar el juicio).
- Incertidumbre transversal abierta requiere Astra medium: systems_analyst para
  resolver decisiones o systems_implementer cuando ejecucion siga acoplada.

Estas instrucciones solicitan delegacion en los bloques independientes descritos;
no una cadena universal. Si el perfil necesario no esta disponible o no existe
forma compatible de ejecutar el bloque, declarar perfil real y limitacion antes
del trabajo dependiente y continuar trabajo independiente. Nunca simular cambio
de modelo raiz ni crear paralelismo artificial. La instruccion explicita del
usuario puede solicitar una prueba de despacho aun sin beneficio productivo.

Al delegar, usar el rol disponible y comprobar su perfil efectivo en metadatos
propios cuando el harness los exponga. Un campo TOML fijo puede prevalecer sobre
un override de spawn; usar default con override compatible para Sol xhigh.
Perfil no observado es unknown, no una atribucion desde el nombre o la respuesta.
Si se detecta discrepancia, corregir el destino antes de seguir ese bloque; la
ausencia de telemetria no exige abrir un collector para cada tarea.

| Escenario y decision pendiente | Ruta proporcionada |
|---|---|
| Ajuste minimo de copy/espaciado aceptado | Directo; Sol low si empieza un bloque separado, mantener modelo actual si cambiarlo no aporta |
| Consulta de gusto o explicacion breve | Sol medium si es bloque separado; raiz high puede responder directo, sin segundo reporte |
| Auditoria de filtros, formulario o dashboard con prioridades abiertas | Evidencia focal del principal; juicio ux_auditor Astra low o raiz Astra equivalente |
| Panel/acordeones/estados con comportamiento resuelto | implementer Sol medium; no auditar otra vez por defecto |
| Filtros con consultas, URL y disponibilidad coordinadas | implementer_complex Sol high si existe esa complejidad; no subir por tocar varios archivos |
| Logica algoritmica profunda y aislada | default con override Sol xhigh o perfil dautia-reason; no reutilizar rol fijo incompatible |
| Taxonomia, inventario y publicacion con decisiones acopladas | systems_analyst Astra medium; devolver ejecucion resuelta a Sol |
| Arquitectura y ejecucion siguen inseparables | systems_implementer Astra medium, sin handoff artificial |
| Entrega de codigo de producto | independent_reviewer Sol high independiente del autor; profundidad proporcional al delta, sin panel |
| Smoke conocido / verificar una correccion | Principal o implementador; no qa_web por defecto |
| Matriz profunda de estados, navegadores o dispositivos | QA de plataforma Sol high con frontera explicita |
| Error de acceso/MCP, fixture ausente o build esperando | Resolver herramienta/ambiente; no escalar modelo ni sustituir proveedor |
| Cambio de requisito en conversacion larga | Actualizar aceptacion y evidencia invalidada; no repetir auditoria completa |
| Runbook de release resuelto | release_operator Sol medium; incompatibilidad nueva vuelve al responsable |

Una auditoria/revision de seguridad explicitamente pedida en lenguaje natural,
o por nombre del rol, activa data_security Sol high para la frontera solicitada.
El principal transmite esa frase fuente y alcance al hijo; su handoff conserva el
opt-in aunque el mensaje del hijo no sea un turno nuevo del usuario. Auth/RLS o
migraciones ordinarias siguen con autor/revisor, sin especialista automatico.
Auditoria no autoriza corregir; con "audita y corrige", el autor realiza los fixes
y el auditor verifica independientemente. Astra medium solo si queda incertidumbre
transversal; seguridad sensible por si sola no fija modelo/esfuerzo.

decision_gate, qa_e2e y documental no forman una cadena de cierre. Reservarlos
para una decision de riesgo, aceptacion transversal o gobierno documental propios.
Sin esa frontera, el principal/autor conserva responsabilidad y usa la skill pertinente.
La revision independiente de codigo es un encargo explicito de este contrato,
no una razon para fabricar trabajo concurrente ni un especialista por cada lente.

No encadenar toda la tabla. Mantener esfuerzo dentro de un bloque coherente.
Handoff compacto: solicitud original, actor/objetivo, candidato/ambiente,
referencia visual, fuentes originales focales, decision pendiente, exclusiones y
parada. El auditor puede consultar lo necesario para cuestionar la evidencia;
no heredar por defecto el historial ni repetir una exploracion ya vigente.
Cerrar con la ruta realmente usada, solo si explica una decision o limitacion.
