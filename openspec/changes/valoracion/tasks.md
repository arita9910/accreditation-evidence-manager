# Tasks

## 1. Modelo y migración

- [ ] 1.1 Definir los modelos `Valoracion`, `ValoracionCriterio` y `ValoracionEvidencia`, con restricciones de unicidad y claves foráneas, y verificar la migración en SQLite. Fuente: [docs/origin-plans/08-modulo-valoracion.md](../../docs/origin-plans/08-modulo-valoracion.md#L15-L18).
- [ ] 1.2 Añadir pruebas del modelo para validar el tipo de valoración, la dimensión y la asociación a criterios/evidencias del mismo ciclo, y verificar los casos de rechazo. Fuente: [docs/origin-plans/08-modulo-valoracion.md](../../docs/origin-plans/08-modulo-valoracion.md#L21-L27).
- [ ] 1.3 Verificar que la migración y la validación de integridad siguen la convención de catálogo y de datos versionados de los planes 01 y 07. Fuente: [docs/decisiones/README.md](../../docs/decisiones/README.md#L25-L43), [docs/origin-plans/07-modulo-evidencias.md](../../docs/origin-plans/07-modulo-evidencias.md#L15-L57).

## 2. Servicios de valoración

- [ ] 2.1 Implementar `crear_valoracion(...)` con validación de ciclo abierto, permisos por dimensión y vinculación segura a criterios/evidencias del mismo ciclo. Verificación: prueba unitaria de caso correcto y caso rechazado.
- [ ] 2.2 Implementar `editar_valoracion(...)` y `eliminar_valoracion(...)` con validación de dependencias y mensajes claros cuando una debilidad tiene acciones asociadas. Verificación: prueba de edición y prueba de bloqueo por dependencia.
- [ ] 2.3 Implementar `formatear_porcentaje(...)` con coma decimal y una cifra decimal, reutilizable por el resto del sistema y compatible con `86,2 % (19/23)`. Verificación: prueba de caso normal y caso denominador cero.
- [ ] 2.4 Reforzar la auditoría y la trazabilidad con `registrar(...)` y asegurar que cada escritura del servicio queda registrada antes del cierre del bloque. Verificación: prueba de registro en alta y edición.

## 3. API

- [ ] 3.1 Exponer `GET/POST /api/ciclos/{id}/valoraciones/` y filtros por dimensión y tipo, con validación de permisos, ciclo abierto y contexto de carrera. Verificación: prueba de API alternativa positiva y negativa.
- [ ] 3.2 Exponer `GET/PATCH/DELETE /api/valoraciones/{id}/` con restricciones por usuario y dimensión; rechazar eliminaciones con dependencias. Verificación: pruebas de API con casos autorizados y denegados.
- [ ] 3.3 Documentar el contrato OpenAPI del módulo y verificar que la respuesta de error y los códigos de estado son coherentes con el resto de la API del proyecto. Verificación: pruebas de serialización y respuestas HTTP.

## 4. Pantalla React

- [ ] 4.1 Crear el editor por dimensión para fortalezas y debilidades con selector de criterios del mismo ciclo y control visual del tipo de valoración. Verificación: componente con renderización y estados iniciales.
- [ ] 4.2 Añadir selector de evidencias del ciclo que ya estén clasificadas y asistente para insertar porcentajes con el formato `86,2 % (19/23)`. Verificación: prueba Vitest del asistente con valor exacto.
- [ ] 4.3 Añadir recordatorio de las indicaciones del Anexo 5 del Manual y validación de la UI para evitar guardar valoraciones sin contenido, criterios o evidencias válidas. Verificación: prueba de validación del formulario.

## 5. Verificación y cierre

- [ ] 5.1 Ejecutar la batería de pruebas del módulo (modelo, servicio, API y UI), comprobar que la validación de ciclo, permisos y auditoría siguen funcionando y dejar evidencia de la ejecución en el bloque final. Verificación: suite del módulo en verde y registro del resultado.

## Workflow follow-up

- Revisar y cerrar la propuesta con el equipo antes de implementar la capa del plan 10.
- Archivar el cambio una vez se cumplan las revisiones del proyecto y queden verificados los resultados de las pruebas del módulo.
