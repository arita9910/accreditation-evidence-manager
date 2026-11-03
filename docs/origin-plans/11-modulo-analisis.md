# Plan 11 — Módulo análisis (incremento 4)

## Objetivo
Ofrecer consultas que leen de varios módulos: estado y completitud del ciclo por dimensión y criterio, y comparación entre dos ciclos de la misma carrera. **No tiene tablas propias.**

## Convenciones comunes
- Django 5.2 + DRF; React 18 + Vite (JS); SQLite en desarrollo y PostgreSQL en producción; consultas sin SQL propio de un gestor.
- Nombres en español. App `sistema/backend/analisis/` con `servicios.py`, `serializadores.py`, `vistas.py`, `urls.py`, `tests/` (sin `modelos.py` de dominio). Lógica en servicios; vistas delgadas.
- API bajo `/api/`, JSON, sesión + CSRF. Permisos con `cuentas.permisos.puede(...)`.
- Indicador = 2.º nivel; criterio = 3.er nivel. Ambigüedad → `docs/decisiones/`.

## Contexto
CU-06 (estado del ciclo), CU-17 (comparar resultados entre ciclos). Depende de planes 07 a 10 y 04. Las consultas deben evitar el problema N+1 (usar `select_related`/`prefetch_related`/agregaciones). **El módulo informa, no evalúa:** no calcula categoría ni cumplimiento.

## Tareas

### T1 — Estado del ciclo
`estado_ciclo(ciclo)` → por dimensión, indicador y criterio: número de evidencias clasificadas, si tiene valor cuantitativo (cuando aplica), si ese dato tiene respaldo, valoraciones registradas (fortalezas/debilidades) y acciones de mejora asociadas. `GET /api/ciclos/{id}/estado/`.

### T2 — Completitud
`completitud(ciclo)` → listas de avisos: criterios sin evidencia, criterios cuantitativos sin dato, datos sin respaldo, modelos incompletos, dimensiones sin valoración, debilidades sin acción. Estos avisos **no bloquean**; los consume el informe (plan 12). `GET /api/ciclos/{id}/completitud/`.

### T3 — Comparación
`comparar(ciclo_a, ciclo_b)` (misma carrera): diferencias en valores de modelos (por campo y curso), en valores de criterio y en el estado de las acciones de mejora. Rechaza ciclos de carreras distintas. `GET /api/comparaciones/?a=&b=`.

- **Aceptación (pruebas):** con un conjunto de datos de prueba conocido, los totales, avisos y diferencias coinciden con los calculados a mano; comparar ciclos de carreras distintas devuelve 400 con el formato de error; permisos: director de su carrera, decano de su facultad, rector todas; miembro, administrador técnico y par evaluador no comparan; consultas con número acotado de queries (prueba con `assertNumQueries`).

### T4 — Pantallas React
Tablero de estado del ciclo (árbol dimensión → indicador → criterio con indicadores visuales y filtro «solo con avisos»); vista de completitud; comparación entre dos ciclos con diferencias resaltadas. **Aceptación (Vitest):** el filtro de avisos y el resaltado de diferencias.

## Fuera de alcance
Gráficos avanzados, exportación, predicciones, cálculo de categoría.

## Definición de terminado
Pruebas en verde; tablero y comparación funcionando; avance en `docs/avance/11-analisis.md`.
