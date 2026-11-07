# Tasks

## 1. T1 — Modelos y migraciones (oleada B parcial)

- [x] 1.1 Definir y documentar `Facultad`, `Carrera`, `Ciclo` y `AsignacionDimension` con sus campos y relaciones.
- [x] 1.2 Añadir migraciones y restricciones de integridad: FK, unicidad por `(ciclo, usuario, dimension)` y validaciones de negocio básicas.
- [x] 1.3 Garantizar la regla de un solo ciclo abierto por carrera y la cadena de `ciclo_anterior` por carrera.
- [x] 1.4 Incluir pruebas para apertura, cierre, cierre de solo lectura, vigencia y asignación duplicada.

## 2. T2 — Servicios

- [x] 2.1 Implementar `crear_facultad` y `crear_carrera` con validaciones de dominio.
- [x] 2.2 Implementar `abrir_ciclo(carrera, tipo, anio_base, curso_inicial, version_normativa, ciclo_anterior=None)` con la validación de no duplicados, mismo ciclo anterior y regla de cinco cursos.
- [x] 2.3 Implementar `cerrar_ciclo(ciclo, categoria_obtenida=None, vigencia_anios=None)` con cierre de fecha y validación de 5/7/9/nulo.
- [x] 2.4 Implementar `asignar_dimension(ciclo, usuario, dimension)` y `quitar_asignacion` con validación de ciclo abierto y usuario miembro de la carrera.
- [x] 2.5 Definir `exigir_ciclo_abierto(ciclo)` como helper reutilizable para otros módulos.
- [x] 2.6 Verificar que las pruebas de aceptación cubran: dos ciclos abiertos, ciclo anterior incorrecto, cierre con fechas, ciclo cerrado no editable, vigencia válida y asignación duplicada rechazada.

## 3. T3 — API

- [ ] 3.1 Exponer `GET/POST /api/facultades/` y `GET/POST/PATCH /api/carreras/` con el patrón estándar del proyecto.
- [ ] 3.2 Exponer `GET /api/ciclos/` con filtros por carrera y estado, `POST /api/ciclos/` para apertura, `GET /api/ciclos/{id}/` y `POST /api/ciclos/{id}/cerrar/`.
- [ ] 3.3 Exponer `GET/POST/DELETE /api/ciclos/{id}/asignaciones/` para gestionar la comisión y las dimensiones.
- [ ] 3.4 Aplicar paginación y forma estándar de errores en español.
- [ ] 3.5 Añadir pruebas de la API con validación de códigos de error y la respuesta esperada.

## 4. T4 — Pantallas React

- [ ] 4.1 Crear la lista de carreras y sus ciclos con estado visible.
- [ ] 4.2 Implementar el formulario de apertura con validación de los campos y aviso de cinco cursos.
- [ ] 4.3 Implementar la acción de cierre con categoría y vigencia opcionales.
- [ ] 4.4 Diseñar la tabla dimensión × usuario para la asignación de miembros a la comisión.
- [ ] 4.5 Verificar los tests de Vitest para validación del formulario y render del tablero de asignación.

## 5. T5 — Conexión con cuentas y auditoría

- [ ] 5.1 Cuando estén disponibles los planes 05 y 06, aplicar `puede(...)` a todas las vistas y servicios del módulo.
- [ ] 5.2 Restringir apertura/cierre/asignación al director de su carrera y la creación de facultad/carrera al administrador técnico.
- [ ] 5.3 Invocar `registrar(...)` en cada operación relevante del módulo.
- [ ] 5.4 Añadir pruebas negativas de permisos y auditoría según la matriz de permisos correspondiente.

## Workflow follow-up

- Revisar que cada tarea del módulo quede alineada con el plan 04 y con la pregunta abierta sobre la relación categoría-vigencia.
- No iniciar la implementación del cambio hasta que la propuesta y el diseño hayan sido revisados por el equipo y la normativa del tutor confirme la regla exacta.
