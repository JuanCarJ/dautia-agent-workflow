# Plantilla adaptable de auditoría

Omitir cualquier sección que no ayude a decidir. No generar puntuaciones ni completar casillas por obligación.

## Resumen

- **Modo:** FULL / SECTION / COPY / HYPOTHESIS
- **Superficie y alcance:** rutas, secciones y estados revisados
- **Público:** confirmado / inferido
- **Acción deseada:** acción exacta
- **Evidencia:** browser, código, analítica, investigación o documentación
- **Limitaciones:** datos o estados no disponibles

### Veredicto

Explicar en dos o tres frases si la oferta se entiende, inspira confianza suficiente y permite actuar. Distinguir lo observado de lo inferido.

## Hallazgos prioritarios

| Sev. | Tipo | Evidencia y ubicación | Impacto | Confianza | Corrección o hipótesis | Validación |
|---|---|---|---|---|---|---|
| HIGH | OBSERVADO | `/pricing`, mobile, CTA | El destino no es previsible | Alta | Cambiar etiqueta y microcopy | Repetir flujo y medir clic→inicio |

Usar `CRITICAL`, `HIGH`, `MEDIUM` o `LOW`. Usar `OBSERVADO`, `INFERIDO`, `DESCONOCIDO` o `HIPÓTESIS` para el tipo.

## Reescrituras

Incluir solo textos que necesiten una decisión:

| Ubicación | Original | Propuesta | Hechos usados | Tradeoff |
|---|---|---|---|---|

Usar `[dato por confirmar]` si una propuesta depende de información no verificada.

## Señales iniciales de accesibilidad o rendimiento

Enumerar únicamente problemas observados y el alcance de la revisión. No declarar conformidad WCAG ni aumento de rendimiento/conversión sin evaluación o medición adecuada.

## Datos que cambiarían el diagnóstico

- analítica o paso del funnel relevante;
- distribución de dispositivos o canales;
- investigación o feedback de usuarios;
- restricciones legales, de marca o de operación;
- evidencia para claims y prueba social.

## Próximas decisiones

Ordenar acciones por dependencia y valor esperado. Separar:

1. correcciones sustentadas por evidencia;
2. hipótesis que conviene experimentar;
3. preguntas que bloquean una recomendación segura.

## Validación posterior

Registrar rutas, estados y viewports repetidos, resultado funcional, evidencia antes/después y métricas disponibles. Si no existen datos posteriores, describir lo corregido sin afirmar que la conversión aumentó.

## Trazabilidad opcional

Si el proyecto mantiene auditorías, guardar un documento breve en `docs/audits/` o la ruta documentada por el repo:

```markdown
# Auditoría de landing y conversión

Fecha:
Alcance:
Evidencia:
Limitaciones:

## Hallazgos
| ID | Severidad | Tipo | Evidencia | Decisión | Estado |
|---|---|---|---|---|---|

## Cambios aplicados
| ID | Antes | Después | Validación |
|---|---|---|---|

## Hipótesis pendientes
| ID | Hipótesis | Métrica o prueba | Estado |
|---|---|---|---|
```

No crear trazabilidad si el usuario pidió solo una opinión breve o el proyecto no conserva este tipo de artefactos.
