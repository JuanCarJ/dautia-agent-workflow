# Principios UX para superficies de conversión

Usar solo las secciones relacionadas con la solicitud. Estas son heurísticas de revisión inicial; no sustituyen investigación, analítica, pruebas de usabilidad ni auditorías especializadas.

## Evidencia antes que preferencia

- Distinguir un defecto funcional de una preferencia estética.
- Evaluar jerarquía, lectura y comportamiento dentro de la marca y el público reales.
- No marcar una fuente, color, layout, radio, alineación o patrón como incorrecto por pertenecer a una lista de tendencias.
- Considerar un patrón genérico solo cuando debilite identidad, comprensión o confianza en el contexto observado.

## Jerarquía y escaneabilidad

- Priorizar el contenido necesario para entender y actuar.
- Usar headings y agrupación que describan el contenido, no solo que decoren.
- Revisar orden visual y orden del DOM.
- No imponer patrón F, alineación izquierda o una estructura única; el idioma, contenido y tipo de interfaz cambian el comportamiento de lectura.

## Responsive y entrada

- Revisar al menos desktop y mobile; añadir viewports según el caso.
- Comprobar reflow, zoom, overflow y contenido oculto.
- Evaluar targets por tamaño, separación, frecuencia y riesgo de error.
- Tratar 44×44 CSS px como objetivo de diseño útil, no como mínimo universal de WCAG AA.
- WCAG 2.2 SC 2.5.8 AA exige 24×24 CSS px o una excepción válida; SC 2.5.5 establece 44×44 CSS px en nivel AAA.
- Elegir navegación superior, inferior o lateral según arquitectura, frecuencia y plataforma; ninguna posición es universalmente superior.

Fuentes:

- https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum
- https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced

## Accesibilidad inicial

Revisar, sin declarar conformidad:

- navegación y operación por teclado;
- foco visible, orden lógico y foco no oculto;
- estructura semántica, nombres accesibles y labels;
- contraste, color como señal y legibilidad;
- errores, instrucciones y estados anunciados;
- zoom, reflow y orientación;
- alternativas a drag y motion no esencial;
- autenticación y consentimiento comprensibles.

Las imágenes informativas necesitan una alternativa que comunique su propósito. Las decorativas deben poder ignorarse, normalmente con `alt=""`; no exigir texto descriptivo para todas.

Una revisión parcial o automatizada no permite afirmar “cumple WCAG”. La conformidad AA requiere evaluar todos los criterios A y AA aplicables en la página completa, incluidas sus variaciones.

Fuentes:

- https://www.w3.org/TR/WCAG22/#conformance-reqs
- https://www.w3.org/WAI/test-evaluate/
- https://www.w3.org/WAI/tutorials/images/decorative/

## Tipografía y color

- Evaluar legibilidad, carga, fallback, licencia, soporte de idioma y coherencia de marca.
- No considerar Inter, Roboto, Arial u otra familia automáticamente genérica.
- Elegir `font-display` según el tradeoff entre contenido inmediato, estabilidad y fidelidad. `swap` muestra fallback y después puede intercambiar la fuente; no evita FOUT ni cambios visuales por definición.
- Evaluar contraste con los valores aplicables de WCAG, incluidos estados hover, focus, disabled y errores.
- No prohibir colores, gradientes o negro puro por estilo; comprobar su función, contraste y coherencia.

Fuente sobre fuentes web:

- https://web.dev/learn/performance/optimize-web-fonts

## Motion y estados

- Usar motion para relación, continuidad o feedback, no como requisito decorativo.
- Respetar `prefers-reduced-motion` cuando el movimiento no sea esencial.
- Comprobar loading, éxito, error, vacío y recuperación solo cuando existan en el flujo.
- No fijar duración, easing o propiedades animadas sin observar el caso y el impacto.

## Rendimiento percibido

- Diferenciar medición de laboratorio y datos de campo.
- Evitar declarar Core Web Vitals con una sola sesión de navegador.
- Umbrales oficiales “good” en p75: LCP ≤2.5 s, INP ≤200 ms y CLS ≤0.1.
- Skeleton, spinner, texto de progreso o contenido inmediato son opciones contextuales; el estado no debe simular progreso inexistente.

Fuente:

- https://web.dev/articles/vitals

## Confianza y patrones engañosos

- Comprobar que precio, renovación, cancelación, privacidad y uso de datos sean comprensibles cuando apliquen.
- No recomendar urgencia falsa, opciones visualmente sesgadas, costos tardíos, consentimiento preseleccionado ni fricción artificial para rechazar.
- Tratar claims, testimonios y prueba social como evidencia que debe ser atribuible y actual.

## Reporte

Para cada hallazgo visual o de usabilidad registrar estado, viewport, evidencia y confianza. Describir la mejora esperada como hipótesis salvo que exista medición que demuestre el impacto.
