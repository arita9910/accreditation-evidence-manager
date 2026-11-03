# Plan 08 — Módulo valoración (incremento 2)

## Objetivo
Registrar la valoración cualitativa de la comisión por dimensión: fortalezas y debilidades, con los criterios y evidencias que las respaldan.

## Convenciones comunes
- Django 5.2 + DRF; React 18 + Vite (JS); SQLite en desarrollo y PostgreSQL en producción.
- Nombres en español. App `sistema/backend/valoracion/` con `modelos.py`, `servicios.py`, `serializadores.py`, `vistas.py`, `urls.py`, `tests/`. Lógica en servicios; vistas delgadas.
- API bajo `/api/`, JSON, sesión + CSRF. Permisos con `cuentas.permisos.puede(...)`; auditoría con `registrar(...)`; escrituras exigen ciclo abierto.
- Indicador = 2.º nivel; criterio = 3.er nivel. Ambigüedad → `docs/decisiones/`.

## Contexto
CU-13. Depende de planes 07, 04, 05. Los textos de fortalezas y debilidades siguen las indicaciones del Anexo 5 del Manual; los porcentajes se escriben con la relación que los origina, por ejemplo 86,2 % (19/23). **La valoración no calcula categorías ni juicios automáticos.**

## Entidades (plan 01, oleada C)
- **Valoracion:** ciclo (FK), dimension (FK), tipo (fortaleza/debilidad), texto, redactada_por. Una fila por fortaleza o debilidad.
- **ValoracionCriterio:** valoracion (FK), criterio (FK). **ValoracionEvidencia:** valoracion (FK), evidencia (FK). Tablas de unión N:M.

## Tareas

### T1 — Modelos y migraciones con pruebas.

### T2 — Servicios
- `crear_valoracion(ciclo, dimension, tipo, texto, criterios, evidencias, usuario)`: solo el miembro asignado a esa dimensión o el director; ciclo abierto; los criterios deben pertenecer a la dimensión; las evidencias, al ciclo.
- `editar_valoracion`, `eliminar_valoracion` (solo si ninguna acción de mejora depende de ella; si depende, error claro).
- Utilidad `formatear_porcentaje(numerador, denominador) -> "86,2 % (19/23)"` con coma decimal y una cifra decimal (redondeo documentado), reutilizable por el plan 12.
- **Aceptación (pruebas):** permiso por dimensión (miembro sin asignación rechazado; decano rechazado); criterio de otra dimensión rechazado; porcentaje bien formateado, incluido denominador cero (error claro); eliminar una debilidad con acciones asociadas rechazado.

### T3 — API
`GET/POST /api/ciclos/{id}/valoraciones/` (filtros por dimensión y tipo), `GET/PATCH/DELETE /api/valoraciones/{id}/`. **Aceptación:** pruebas de API con permisos positivos y negativos.

### T4 — Pantallas React
Editor de fortalezas y debilidades por dimensión: lista por tipo, selector de criterios de la dimensión, selector de evidencias del ciclo (de las ya clasificadas), asistente para insertar porcentajes con su relación de origen, y recordatorio de las indicaciones del Anexo 5. **Aceptación (Vitest):** el asistente inserta «86,2 % (19/23)» con coma decimal.

## Fuera de alcance
Redacción de otros textos del informe (plan 12), acciones de mejora (plan 10).

## Definición de terminado
Pruebas en verde; el flujo miembro → valoración → debilidad disponible para el plan 10 funcionando; avance en `docs/avance/08-valoracion.md`.
