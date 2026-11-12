# Avance 09 — Módulo cuantitativo

## Estado

La planificación del cambio `cuantitativos` se ha revisado para mantener coherencia entre la propuesta, el diseño y la ejecución. En este bloque se implementó la carga de `ModeloCampo` desde `sistema/datos/modelos_resumen.json` con 11 modelos, se volvió repetible por claves naturales (`modelo`, `fila`, `columna`) y se añadieron pruebas de idempotencia e integridad en SQLite.

## Criterios revisados

- Catálogo de `ModeloCampo` cargado desde los 11 modelos del Manual y con orden repetible por claves naturales, sin introducir dependencias nuevas.
- Revisión de permisos y auditoría: `puede(...)` en lecturas y escrituras; `registrar(...)` solo en escrituras relevantes.
- `VinculoDato` apunta a `Evidencia`; exige mismo ciclo; impide duplicar par dato–evidencia; `desvincular` exige ciclo abierto.
- Pregunta abierta documentada para contrastar los 38 criterios cuantitativos con el catálogo cargado (20 criterios con 22 asociaciones `CriterioModelo`).
- Preguntas abiertas por celdas dudosas registradas sin conjeturas en `modelos_resumen.json` y en la decisión D-09.05.

## Pendiente documental

- Confirmar la verificación en PostgreSQL solo como pendiente y documentada, siguiendo D-14.
- Completar la ejecución del plan de pruebas y verificación final en navegador antes de archivar el cambio.
