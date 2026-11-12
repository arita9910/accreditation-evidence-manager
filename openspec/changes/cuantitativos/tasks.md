# Tasks

## 1. Modelo y migración

- [ ] 1.1 Definir la migración de `ValorModelo`, `ValorCriterio` y `VinculoDato` con unicidad por ciclo/curso/campo y validaciones de integridad; verificar que la migración se aplica correctamente en SQLite y no introduce columnas nominales.
- [ ] 1.2 Añadir la restricción `CHECK` de `VinculoDato` para asegurar que exactamente uno de los dos datos esté presente y verificar la prueba que reproduzca la violación del CHECK.
- [ ] 1.3 Preparar pruebas de modelo para tipos, no negativos, porcentajes y la copia de `acreditacion_anterior`; verificar que los casos esperados pasan en SQLite.

## 2. Servicios

- [ ] 2.1 Implementar `guardar_valores_modelo(ciclo, modelo, curso, celdas, usuario)` con validación por tipo de campo, coherencia de porcentajes y total, y llamada a `exigir_ciclo_abierto(...)`; verificar casos positivos y negativos del cálculo.
- [ ] 2.2 Implementar `guardar_valor_criterio(ciclo, criterio, ...)` para criterios cuantitativos sin modelo y rechazar el valor cuando el criterio tenga modelo o sea cualitativo; verificar las pruebas de rechazo.
- [ ] 2.3 Implementar `rellenar_acreditacion_anterior(ciclo)`, `datos_sin_respaldo(ciclo)` y `datos_de_evidencia(evidencia)` con recorrido bidireccional de dato–evidencia; verificar que un dato sin respaldo aparece y desaparece tras vincularlo.
- [ ] 2.4 Implementar `vincular(dato, evidencias, usuario)` y `desvincular`, integrando `puede(...)` y `registrar(...)` en la operación; verificar permisos y trazabilidad de auditoría.

## 3. API

- [ ] 3.1 Crear `GET/PUT /api/ciclos/{id}/modelos/{n}/valores/?curso=` para consulta y escritura de valores por modelo; verificar respuesta JSON y permisos positivos/negativos.
- [ ] 3.2 Crear `GET/PUT /api/ciclos/{id}/criterios/{codigo}/valor/`, `POST/DELETE /api/vinculos/` y `GET /api/evidencias/{id}/datos/` con `GET /api/datos/{tipo}/{id}/evidencias/`; verificar vínculos en ambos sentidos.
- [ ] 3.3 Crear `GET /api/ciclos/{id}/datos/sin-respaldo/` y pruebas de API para volver a consultar los casos de datos sin evidencia y los accesos denegados.

## 4. Pantalla

- [ ] 4.1 Construir la tabla editable de datos por modelo con validación de números no negativos, cálculos de porcentaje y totales; verificar con Vitest la validación de entrada.
- [ ] 4.2 Construir la edición del valor por criterio con referencia textual a la Guía como dato de apoyo, sin que el sistema lo evalúe como cumplimiento; verificar la visualización y la validación de la pantalla.
- [ ] 4.3 Construir el selector de evidencias para vincular datos y la lista de datos sin respaldo en la ficha de evidencia; verificar que la interfaz muestra los datos respaldados y los pendientes.
