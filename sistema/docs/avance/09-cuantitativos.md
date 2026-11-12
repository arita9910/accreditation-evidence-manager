# Avance 09 — Módulo cuantitativo

## Estado

La planificación del cambio `cuantitativos` se ha revisado para mantener coherencia entre la propuesta, el diseño y la ejecución. La carga del catálogo de modelos, la restricción de `VinculoDato` y la verificación de SQLite quedan como base del incremento.

## Criterios revisados

- Catálogo de `ModeloCampo` cargado desde los 11 modelos del Manual y con orden repetible por claves naturales, sin introducir dependencias nuevas.
- Revisión de permisos y auditoría: `puede(...)` en lecturas y escrituras; `registrar(...)` solo en escrituras relevantes.
- `VinculoDato` apunta a `Evidencia`; exige mismo ciclo; impide duplicar par dato–evidencia; `desvincular` exige ciclo abierto.
- Pregunta abierta documentada para contrastar los 38 criterios cuantitativos con el catálogo cargado (20 criterios con 22 asociaciones `CriterioModelo`).

## Pendiente documental

- Confirmar la verificación en PostgreSQL solo como pendiente y documentada, siguiendo D-14.
- Completar la ejecución del plan de pruebas y verificación final en navegador antes de archivar el cambio.
