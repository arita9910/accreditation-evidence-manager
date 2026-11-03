# Plan 06 — Módulo auditoría (incremento 1)

## Objetivo
Registrar quién hizo qué, cuándo y sobre qué objeto, en una tabla de **solo inserción**, y permitir su consulta según permisos.

## Convenciones comunes
- Django 5.2 + DRF; React 18 + Vite (JS); SQLite en desarrollo y PostgreSQL en producción.
- Nombres en español. App `sistema/backend/auditoria/` con `modelos.py`, `servicios.py`, `serializadores.py`, `vistas.py`, `urls.py`, `tests/`. Lógica en servicios; vistas delgadas.
- API bajo `/api/`, JSON, sesión + CSRF. Permisos con `cuentas.permisos.puede(...)`.
- Ambigüedad → `docs/decisiones/`.

## Contexto
CU-18 (consultar el registro de auditoría). Requisito de seguridad: RM 160/2023, art. 28.2 a). D-07: tabla propia de solo inserción llamada por un servicio, no librería de historial automático. Depende de: plan 02. Se construye **antes de cuentas** dentro del incremento 1 para que cuentas y ciclos puedan registrar desde el principio (hasta que cuentas exista, `usuario` puede ser nulo).

## Entidad (plan 01, oleada B)
**RegistroAuditoria:** usuario (FK nulo), fecha_hora, accion, objeto_tipo, objeto_id, detalle (JSON/Text), ip, resultado (correcto/denegado). Sin edición ni borrado.

## Tareas

### T1 — Modelo de solo inserción
- Sobrescribir `save()` (solo si `pk is None`), `delete()` (lanza error) y el `QuerySet` (`update`, `delete`, `bulk_update` lanzan error). Opcional: restringir permisos del rol de base de datos en producción (documentar, no implementar SQL propio de un gestor).
- **Aceptación (pruebas):** crear funciona; modificar una fila existente falla; borrar falla; `queryset.update()` y `.delete()` fallan.

### T2 — Servicio `registrar`
`auditoria.servicios.registrar(usuario, accion, objeto=None, detalle=None, resultado='correcto', peticion=None)`: rellena `fecha_hora` e `ip` (de la petición), `objeto_tipo`/`objeto_id` a partir del objeto. Catálogo de acciones como constantes (p. ej. `sesion.entrar`, `sesion.fallida`, `usuario.crear`, `rol.asignar`, `ciclo.abrir`, `ciclo.cerrar`, `evidencia.cargar`, `evidencia.descargar`, `acceso.denegado`…). Los demás módulos llaman a este servicio; **registra acciones de negocio, no solo cambios de filas**. No debe romper la operación principal si falla el registro: decidir y documentar (propuesta: la operación de negocio y el registro van en la misma transacción para que no haya operaciones sin rastro).
- **Aceptación:** pruebas del servicio; transacción coherente (si la operación falla, no queda registro de éxito).

### T3 — Middleware/ayuda de accesos denegados
Registrar en auditoría cada respuesta 403 producida por `PermisoSistema` (acción, usuario, objeto), sin guardar contenidos sensibles.

### T4 — API de consulta
`GET /api/auditoria/` con filtros `usuario`, `accion`, `objeto_tipo`, `desde`, `hasta`, `resultado`; paginada y ordenada por fecha descendente. Alcance: el director ve la de su carrera; el administrador técnico ve todo; los demás roles no acceden (matriz del plan 05).
- **Aceptación:** pruebas de filtros y de permisos (director de otra carrera no ve registros ajenos).

### T5 — Pantalla
Tabla con filtros (usuario, acción, fechas, resultado) y paginación. **Aceptación (Vitest):** los filtros se envían a la API.

### T6 — Cobertura
Verificar con una prueba que las operaciones de cuentas y ciclos del incremento 1 dejan su registro y que los accesos denegados también.

## Fuera de alcance
Exportación de la auditoría, alertas, retención/archivado.

## Definición de terminado
Modelo inmutable probado, servicio usado por cuentas y ciclos, API y pantalla probadas, avance en `docs/avance/06-auditoria.md`.
