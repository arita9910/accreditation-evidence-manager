# Tasks

## 1. Definición del módulo y contratos base

- [x] 1.1 Crear la estructura `sistema/backend/mejora/` con modelos, servicios, serializadores, vistas, URLs y pruebas del plan 10, y verificar que los archivos esperados queden presentes.
- [x] 1.2 Definir las entidades `PlanMejora`, `AccionMejora`, `SeguimientoAccion` y `AccionEvidencia` con la relación obligatoria a una debilidad o hallazgo de valoración, y verificar la regla de negocio con pruebas unitarias.
- [x] 1.3 Integrar la validación del ciclo abierto y la trazabilidad con `exigir_ciclo_abierto`, `puede(...)` y `registrar(...)`, y verificar que las pruebas de permisos y auditoría pasen.

## 2. Lógica de negocio y validación de estados

- [ ] 2.1 Implementar `proponer_accion`, `aprobar_accion`, `registrar_seguimiento`, `vincular_evidencia`, `acciones_vencidas` y `plan_ciclo_anterior`, y verificar que el servicio expone el comportamiento esperado por el plan.
- [ ] 2.2 Rechazar transiciones de estado no válidas y validar que cada acción de mejora debe tener origen en una debilidad, y verificar los casos de prueba negativos.
- [ ] 2.3 Registrar en el historial del seguimiento los cambios de estado y los usuarios implicados, y verificar la trazabilidad con auditoría en pruebas específicas.

## 3. API y consumo de datos

- [ ] 3.1 Exponer endpoints REST para `GET/POST /api/ciclos/{id}/plan/`, `GET/POST /api/planes/{id}/acciones/`, `PATCH /api/acciones/{id}/`, `GET/POST /api/acciones/{id}/seguimientos/` y `POST /api/acciones/{id}/evidencias/`, y verificar la respuesta HTTP con permisos positivos y negativos.
- [ ] 3.2 Añadir la consulta del plan del ciclo anterior en la API `GET /api/ciclos/{id}/plan-anterior/` y verificar la comparación de estado con el plan actual.
- [ ] 3.3 Documentar los contratos y validaciones mínimos de la API y verificar que las pruebas de serialización y permisos pasan.

## 4. Pantalla y experiencia de usuario

- [ ] 4.1 Implementar la vista del plan del ciclo con acciones y vencidas resaltadas, y verificar la renderización de la UI con pruebas Vitest.
- [ ] 4.2 Permitir proponer una acción desde una debilidad seleccionada, y verificar que la UI evita crear una acción sin elegir debilidad.
- [ ] 4.3 Añadir el historial de seguimiento y la vista del plan anterior junto al nuevo, y verificar la interacción con el usuario y la comparación de planes.

## 5. Integración final y verificación

- [ ] 5.1 Ejecutar la batería de pruebas del módulo de mejora y verificar que el flujo debilidad → acción → seguimiento → cumplimiento quede en verde.
- [ ] 5.2 Actualizar la documentación de avance en `docs/avance/10-mejora.md` y verificar que el documento refleja el estado real del módulo.

## Workflow follow-up

- Revisar el resultado del cambio y archive el plan una vez validado por el equipo.
- Verificar que la documentación final del cambio quede alineada con los requisitos del plan 10.
