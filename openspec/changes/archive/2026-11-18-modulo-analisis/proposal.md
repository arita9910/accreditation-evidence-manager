# Proposal

## Why

El módulo de análisis debe consolidar consultas de estado, completitud y comparación sobre datos repartidos entre los módulos de ciclos, estructura normativa, evidencias, cuantitativos, valoraciones y mejora. La propuesta implementa esas consultas sin crear tablas propias y sin calcular categoría o cumplimiento, según el Plan 11 (Módulo de análisis), para completar el incremento 4 de la aplicación.

Las fuentes SEA-CU exigen que la evaluación permita identificar fortalezas y debilidades y ofrecer información para el diseño y seguimiento continuo de planes de mejora ([Resolución No.36-2024 SEA-CU](../../../docs/fuentes/Resolución%20No.36-2024%20SEA-CU.md#L23-L27)); el Manual también vincula el análisis del ciclo con caracterización, seguimiento y atención de aspectos pendientes ([Manual de implementación SEA-CU 2025](../../../docs/fuentes/Manual%20implementación%20SEA-CU%202025.md#L1186-L1194)).

## What Changes

- Incorporar servicios de solo lectura `estado_ciclo(ciclo)`, `completitud(ciclo)` y `comparar(ciclo_a, ciclo_b)` en `sistema/backend/analisis/`.
- Exponer consultas bajo `/api/ciclos/{id}/estado/`, `/api/ciclos/{id}/completitud/` y `/api/comparaciones/?a=&b=`.
- Representar el estado por dimensión, indicador y criterio, incluyendo evidencias, datos cuantitativos, respaldos, valoraciones y acciones asociadas.
- Emitir tipos de aviso de completitud sin bloquear el informe ni calcular cumplimiento.
- Reservar el término "categoría" únicamente para la categoría de acreditación (Calificada/Certificada/Excelencia), que no se calcula ni se devuelve por este módulo.
- Comparar ciclos únicamente dentro de la misma carrera y rechazar carreras distintas con error HTTP 400.
- Aplicar permisos centralizados con `puede(...)` y control de sesión; al ser consultas de solo lectura, `analisis` no invoca `exigir_ciclo_abierto`.
- Registrar con `registrar(...)` solo comparaciones autorizadas; los 403 se auditan en middleware.
- Propuesta provisional de comparación (pendiente de tutor): emparejar cursos por posición relativa dentro del ciclo (`curso_inicial + desplazamiento`) y comparar `ValorCriterio` por criterio.
- Añadir tablero de estado, vista de completitud y comparación con diferencias resaltadas en React.
- Mantener consultas acotadas y sin N+1 mediante carga anticipada y agregaciones.

## Capabilities

### New Capabilities

- `analisis-ciclo`: consultas de estado y completitud de un ciclo y comparación autorizada entre ciclos de una misma carrera.

### Modified Capabilities

- Ninguna. Los requisitos existentes no cambian; el módulo reutiliza sus capacidades de ciclos, cuantitativos, valoración y mejora.

## Impact

- Backend: nueva app Django `analisis` con `servicios.py`, `serializadores.py`, `vistas.py`, `urls.py` y `tests/`; sin `modelos.py` ni nuevas tablas.
- API: tres endpoints REST bajo `/api/` y formato de error estándar del proyecto.
- Reutilización: lectura de estructura normativa, evidencias/clasificaciones, valores cuantitativos y vínculos, valoraciones y acciones de mejora.
- Seguridad: permisos y ámbito según comportamiento real de `puede(...)`; para comparación, documentar discrepancias de la matriz ideal frente a la implementación actual.
- Frontend: pantalla React para árbol de estado, avisos y comparación.
- Dependencias: ninguna nueva.
- Documentación: cierre con avance en `sistema/docs/avance/11-analisis.md` y dudas en `sistema/docs/decisiones/`.

Fuente principal: [Plan 11 — Módulo análisis](../../../docs/origin-plans/11-modulo-analisis.md#L1-L34).
