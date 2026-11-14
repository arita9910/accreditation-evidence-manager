# Avance 09 — Módulo cuantitativo

## Estado

La planificación del cambio `cuantitativos` se ha revisado para mantener coherencia entre la propuesta, el diseño y la ejecución. En este bloque se implementó la carga de `ModeloCampo` desde `sistema/datos/modelos_resumen.json` con 11 modelos, se volvió repetible por claves naturales (`modelo`, `fila`, `columna`) y se añadieron pruebas de idempotencia e integridad en SQLite.

## Criterios revisados

- Catálogo de `ModeloCampo` cargado desde los 11 modelos del Manual y con orden repetible por claves naturales, sin introducir dependencias nuevas.
- Revisión de permisos y auditoría: `puede(...)` en lecturas y escrituras; `registrar(...)` solo en escrituras relevantes.
- `VinculoDato` apunta a `Evidencia`; exige mismo ciclo; impide duplicar par dato–evidencia; `desvincular` exige ciclo abierto.
- Pregunta abierta documentada para contrastar los 38 criterios cuantitativos con el catálogo cargado (20 criterios con 22 asociaciones `CriterioModelo`).
- Preguntas abiertas por celdas dudosas registradas sin conjeturas en `modelos_resumen.json` y en la decisión D-09.05.

## Verificación final ejecutada

- La validación del backend se ejecutó sobre SQLite con la suite completa de Django: `python manage.py test` en `sistema/backend` y pasó.
- La validación del frontend se ejecutó con la suite de Vitest en `sistema/frontend` y pasó.
- La comprobación de lint y build del frontend también pasó (`npm run lint` y `npm run build`).
- La verificación en PostgreSQL queda pendiente y documentada conforme a D-14; no se marca como realizada. La validación del cierre se realiza en SQLite y no se hace afirmación de PostgreSQL.

## Pendiente documental

- Completar la verificación funcional en navegador antes de archivar el cambio y registrar el resultado en la evidencia final del cierre.
