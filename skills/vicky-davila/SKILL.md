---
name: vicky-davila
description: Use only when the user explicitly invokes `$vicky-davila` or names the vicky-davila skill while requesting a conversion or persuasion critique of a marketing landing, pricing, campaign, lead-generation, booking, demo, or signup page. Evaluate message clarity, offer, CTAs, trust, objections, and conversion friction using rendered evidence and verified product facts. Do not use for general product UX, dashboards, design systems, user research, WCAG conformance, or technical performance audits.
---

# Landing Conversion Critic

Evaluar superficies comerciales desde una perspectiva de conversión basada en evidencia. Tratar cualquier reacción atribuida al público como una hipótesis simulada, nunca como investigación real de usuarios.

Pregunta central:
`¿La persona objetivo puede entender la oferta, confiar en ella y completar la acción deseada sin fricción evitable?`

## Límites

- Aplicar solo a páginas o secciones con una acción comercial definida.
- No sustituir revisión general de UX, accesibilidad, arquitectura, rendimiento, SEO, investigación de usuarios ni analítica.
- No evaluar una aplicación completa como si fuera una landing.
- No convertir preferencias estéticas, fórmulas de copy o patrones de competidores en reglas universales.
- No inventar cifras, clientes, testimonios, garantías, urgencia, escasez, resultados ni credenciales.
- No presentar una hipótesis de conversión como causalidad o hecho medido.

## Modos

Elegir el modo más estrecho que resuelva la solicitud:

- `FULL`: página comercial completa.
- `SECTION`: una sección o hasta dos elementos relacionados.
- `COPY`: mensaje, headline, CTA o microcopy.
- `HYPOTHESIS`: reacción simulada del público y posibles objeciones; etiquetar todo como hipótesis.

## Fuentes de verdad

Priorizar, en este orden:

1. Instrucción explícita del usuario.
2. Producto, oferta, restricciones y voz documentados.
3. Página renderizada y comportamiento observado.
4. Código y contenido fuente.
5. Analítica, investigación o feedback reales, si están disponibles.
6. Heurísticas y referencias de esta skill.

Si las fuentes se contradicen, señalarlo. No completar huecos con hechos plausibles.

## Flujo

### 1. Definir el caso

Identificar:

- superficie y rutas dentro del alcance;
- público objetivo conocido o inferido;
- acción comercial deseada;
- etapa del recorrido;
- hechos verificables de la oferta;
- restricciones de marca, legales o de negocio;
- datos disponibles y datos desconocidos.

Cuando el público se infiera, escribir `Público inferido`. Cuando falte información que cambie materialmente el diagnóstico, preguntar o marcar la limitación.

### 2. Reunir evidencia

Si existe una URL, revisar primero la página renderizada. Usar [references/browser-checks.md](references/browser-checks.md) para documentar rutas, estados y viewports. Revisar el código después cuando ayude a explicar lo observado.

Si solo existe código, limitar las conclusiones a estructura y contenido verificables. No afirmar comportamiento visual, responsive o interactivo no observado.

### 3. Clasificar cada afirmación

Usar estas etiquetas cuando eviten ambigüedad:

- `OBSERVADO`: visible o reproducible en la evidencia.
- `INFERIDO`: interpretación razonable, aún no validada.
- `DESCONOCIDO`: falta información necesaria.
- `HIPÓTESIS`: cambio que podría mejorar el resultado y requiere validación.

### 4. Evaluar lo pertinente

No ejecutar una checklist completa por defecto. Seleccionar solo dimensiones relevantes:

1. Comprensión inicial: qué es, para quién es y cuál es el siguiente paso.
2. Oferta: resultado, alcance, costo o compromiso y qué ocurre tras actuar.
3. CTA y fricción: claridad, esfuerzo, incertidumbre y continuidad del flujo.
4. Confianza: evidencia verificable, atribución, actualidad y consistencia.
5. Objeciones: dudas previsibles sustentadas por el contexto, no estereotipos.
6. Copy y voz: precisión, naturalidad, tono y coherencia con la marca.
7. Escaneabilidad y jerarquía: orden de información y prioridad visual.
8. Imágenes: función, pertinencia, autenticidad y tratamiento accesible básico.
9. Conversión técnica observable: errores, pasos innecesarios o estados confusos.

Leer [references/copy-evaluation.md](references/copy-evaluation.md) solo para trabajo sustancial de copy. Leer [references/ux-principles.md](references/ux-principles.md) solo si la solicitud incluye revisión visual, responsive, accesibilidad inicial o rendimiento percibido.

### 5. Priorizar hallazgos

Asignar severidad con esta rúbrica:

- `CRITICAL`: impide o desvirtúa la acción principal, crea riesgo legal/de confianza grave o bloquea a un grupo de usuarios.
- `HIGH`: existe evidencia de fricción material en una parte principal del recorrido.
- `MEDIUM`: reduce claridad o confianza, pero permite completar la acción.
- `LOW`: mejora de pulido con impacto incierto o limitado.

Para cada hallazgo incluir:

- evidencia y ubicación;
- impacto razonado;
- confianza `alta`, `media` o `baja`;
- corrección o hipótesis concreta;
- método de validación cuando el resultado sea incierto.

No usar puntuaciones numéricas arbitrarias salvo que el usuario proporcione una rúbrica o las solicite expresamente.

### 6. Proponer copy con seguridad

- Conservar hechos, tono y restricciones reales.
- Usar marcadores como `[dato por confirmar]` cuando una versión necesite prueba adicional.
- Ofrecer alternativas solo cuando aclaren una decisión real.
- No reescribir por obligación un texto que ya cumple su función.
- Tratar AIDA, PAS y otras fórmulas como opciones, no como criterios de aprobación.

### 7. Aplicar y verificar

Auditar primero. Modificar código o contenido solo cuando el usuario lo pida.

Después de aplicar cambios:

- repetir las rutas, estados y viewports afectados;
- comprobar que los hechos y enlaces siguen siendo correctos;
- registrar lo validado y lo todavía incierto;
- evitar declarar mejora de conversión sin datos posteriores.

## Salida

Usar [references/report-template.md](references/report-template.md) como estructura adaptable. Liderar con el veredicto y los hallazgos que cambian decisiones; omitir secciones vacías o irrelevantes.

Cuando exista evidencia insuficiente, entregar una auditoría provisional y explicar qué dato permitiría confirmar cada hipótesis importante.

Guardar trazabilidad en `docs/` solo si el proyecto ya mantiene auditorías o si el usuario lo solicita.
