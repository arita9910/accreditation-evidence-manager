# Tasks

## 1. Modelo y migración

- [x] 1.1 Definir el modelo de auditoría de solo inserción con campos de usuario, fecha, acción, entidad, detalle, resultado e IP, y verificar que la migración sqlite queda lista para la app `auditoria`.
- [x] 1.2 Reforzar `save()` y `delete()` para impedir edición y borrado en la entidad de auditoría, y verificar que una actualización sobre una fila existente falla con la prueba del módulo.
- [x] 1.3 Rechazar `QuerySet.update()`/`delete()` y el borrado masivo del modelo de auditoría, y comprobar la prueba de integridad del bloque.
- [x] 1.4 Documentar el contrato de la tabla y la estrategia de inmutabilidad, y comprobar que la documentación del bloque queda alineada con D-07 y el plan 06.

## 2. Servicio registrar y reemplazo del stub

- [x] 2.1 Implementar `registrar(accion, *, usuario=None, entidad=None, detalle=None, contexto=None, **kwargs)` con la firma actual y la serialización del detalle, y verificar que la prueba del servicio crea el evento con la forma esperada.
- [x] 2.2 Sustituir el stub in-memory por la implementación real de persistencia en la base de datos, conservando la misma firma y el comportamiento de los módulos consumidoras, y verificar que los eventos se guardan con la estructura existente.
- [x] 2.3 Reemplazar las llamadas del stub en `ciclos/servicios.py` para `abrir_ciclo`, `cerrar_ciclo` y `asignar_dimension`, y comprobar que las pruebas del módulo de ciclos siguen pasando sin cambios funcionales.
- [x] 2.4 Definir la política de transacción para la operación principal y el registro, y verificar la prueba de coherencia para asegurar que no haya éxito sin rastro.

## 3. API de consulta

- [x] 3.1 Crear la API de consulta `GET /api/auditoria/` con filtros por usuario, acción, entidad, fecha y resultado, y verificar el caso de filtros correctos sobre un conjunto de registros.
- [x] 3.2 Aplicar el alcance de permisos del director y del administrador técnico, y verificar que un director no vea registros ajenos a su carrera.
- [x] 3.3 Añadir ordenación por fecha descendente y paginación, y verificar que la API responde con JSON consistente y mensajes en español.

## 4. Middleware y accesos denegados

- [x] 4.1 Registrar cada respuesta 403 de acceso en auditoría sin guardar contenidos sensibles, y verificar la prueba del middleware con un usuario no autorizado.
- [x] 4.2 Asegurar que el evento de `acceso.denegado` conserva el usuario, la acción y la entidad objetivo, y verificar el caso de la negación con `PermisoSistema`.

## 5. Pantalla de consulta

- [ ] 5.1 Diseñar la pantalla de auditoría con filtros de usuario, acción, fechas y resultado, y comprobar que el formulario envía los argumentos esperados a la API.
- [ ] 5.2 Añadir la paginación visual y la presentación del listado, y verificar con Vitest que el flujo del filtro y la carga de datos sigue funcionando.

## 6. Verificación final y integración

- [ ] 6.1 Ejecutar las pruebas del módulo de auditoría y del módulo de ciclos, y verificar que la regresión de la firma `registrar(...)` no rompe el comportamiento existente.
- [ ] 6.2 Revisar el alcance de la documentación y de los artefactos del cambio, y verificar que la especificación, el diseño y la implementación quedan alineados con el plan 06 y las decisiones D-07, D-11 y D-17.
