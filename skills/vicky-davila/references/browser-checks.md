# Evidencia de navegador

Usar esta referencia cuando exista una URL o una aplicación ejecutable. Preferir la herramienta Browser de Codex para exploración interactiva y Playwright para flujos repetibles o versionados.

## Preparar el alcance

Registrar antes de concluir:

- URL y ruta;
- estado revisado: inicial, formulario, éxito, error, autenticado, vacío u otro relevante;
- viewport y dispositivo aproximado;
- fecha de observación;
- limitaciones de acceso, datos o autenticación.

Como mínimo, revisar un viewport desktop y uno mobile. Agregar tamaños intermedios solo cuando la composición o el tráfico esperado lo justifiquen; ningún tamaño único representa todos los dispositivos.

## Orden de revisión

1. Observar el primer viewport sin inspeccionar el código.
2. Recorrer la acción comercial principal.
3. Revisar jerarquía, CTA, confianza y continuidad entre pasos.
4. Comprobar los estados relevantes que realmente existan.
5. Usar DOM o código para explicar lo observado, no para reemplazarlo.
6. Capturar evidencia cuando un hallazgo dependa de ubicación o estado visual.

## Evidencia mínima por hallazgo

- ruta, estado y viewport;
- elemento o texto exacto;
- comportamiento observado;
- captura o selector cuando aporte reproducibilidad;
- diferencia entre lo observado y lo esperado;
- nivel de confianza.

## Checks iniciales, no de conformidad

- navegación por teclado del recorrido principal;
- foco visible y no oculto;
- etiquetas y mensajes de error comprensibles;
- contraste potencialmente problemático;
- targets táctiles y separación;
- overflow, zoom y reflow básicos;
- imágenes informativas frente a decorativas;
- motion que interfiera o ignore preferencias del usuario.

Estos checks no permiten afirmar conformidad WCAG. Remitir una auditoría de conformidad a una metodología especializada con revisión manual.

## Después de cambios

Repetir las mismas rutas, estados y viewports. Comparar evidencia antes/después y comprobar que la acción principal sigue funcionando. Si no existe medición de negocio, describir el resultado como reducción de fricción observada, no como aumento demostrado de conversión.
