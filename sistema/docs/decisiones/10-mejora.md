# Decisiones del Plan 10 - Módulo de Mejora

- Origen obligatorio: Cada acción de mejora debe estar estrictamente vinculada a una debilidad registrada en el módulo de Valoraciones del mismo ciclo.
- Un plan por ciclo: Solo puede existir un Plan de Mejora por cada ciclo de autoevaluación.
- Estados del plan: El plan transita por los estados Borrador, Aprobado y Cerrado, controlados por el botón de edición del plan.
- Gestión de acciones: Las acciones pueden ser creadas, editadas y eliminadas siempre y cuando el ciclo esté abierto y el plan no esté cerrado.
- Auditoría: Todas las operaciones de creación, edición y borrado (del plan y de las acciones) quedan registradas mediante registrar(...).
- Verificación: Pruebas ejecutadas en SQLite y Vitest. PostgreSQL queda pendiente según D-14.