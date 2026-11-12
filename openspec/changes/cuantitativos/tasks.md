# Tasks

## 0. Catálogo de modelos y `ModeloCampo`

- [x] 0.1 Crear el fichero de datos `sistema/datos/` con los 11 modelos del Manual y el cargador repetible por claves naturales, verificando que el total de modelos y campos quede alineado con el catálogo cargado; documentar celdas dudosas como preguntas abiertas sin conjeturas.
- [x] 0.2 Implementar la carga de `ModeloCampo` y pruebas de idempotencia para el catálogo, verificando que la cuenta de 11 modelos y sus campos coincida con la fuente del Manual y que no se dupliquen registros al recargar.
- [x] 0.3 Añadir pruebas de integridad para `CriterioModelo` y `ModeloCampo` con total de modelos y campos, verificando que el catálogo cargado no produzca asociaciones extrañas ni campos faltantes.

## 1. Modelo y migración

- [x] 1.1 Definir la migración de `ValorModelo`, `ValorCriterio` y `VinculoDato` con unicidad por ciclo/curso/campo y validaciones de integridad; verificar que la migración se aplica correctamente en SQLite y no introduce columnas nominales.
- [x] 1.2 Añadir la restricción `CHECK` de `VinculoDato` para asegurar que exactamente uno de los dos datos esté presente y verificar la prueba que reproduzca la violación del CHECK.
- [x] 1.3 Preparar pruebas de modelo para tipos, no negativos, porcentajes y la copia de `acreditacion_anterior`; verificar que los casos esperados pasan en SQLite.

## 2. Servicios

- [ ] 2.1 Implementar `guardar_valores_modelo(ciclo, modelo, curso, celdas, usuario)` con validación por tipo de campo, coherencia de porcentajes y total, y llamada a `exigir_ciclo_abierto(...)`; verificar casos positivos y negativos del cálculo.
- [ ] 2.2 Implementar `guardar_valor_criterio(ciclo, criterio, ...)` para criterios cuantitativos sin modelo y rechazar el valor cuando el criterio tenga modelo o sea cualitativo; verificar las pruebas de rechazo.
- [ ] 2.3 Implementar `rellenar_acreditacion_anterior(ciclo)`, `datos_sin_respaldo(ciclo)` y `datos_de_evidencia(evidencia)` con recorrido bidireccional de dato–evidencia; verificar que un dato sin respaldo aparece y desaparece tras vincularlo.
- [ ] 2.4 Implementar `vincular(dato, evidencias, usuario)` y `desvincular`, integrando `puede(...)` y `registrar(...)` en la operación; verificar permisos y trazabilidad de auditoría.

## 3. API

- [ ] 3.1 Crear `GET/PUT /api/ciclos/{id}/modelos/{n}/valores/?curso=` para consulta y escritura de valores por modelo; verificar respuesta JSON y permisos positivos/negativos.
- [ ] 3.2 Crear `GET/PUT /api/ciclos/{id}/criterios/{codigo}/valor/` para consulta y escritura de valores por criterio; verificar respuesta JSON, validaciones y permisos.
- [ ] 3.3 Crear `POST/DELETE /api/vinculos/`, `GET /api/evidencias/{id}/datos/` y `GET /api/datos/{tipo}/{id}/evidencias/`; verificar vínculos en ambos sentidos y la restricción de complejidad del par dato–evidencia.
- [ ] 3.4 Crear `GET /api/ciclos/{id}/datos/sin-respaldo/` y pruebas de API para volver a consultar los casos de datos sin evidencia y los accesos denegados.

## 4. Pantalla

- [ ] 4.1 Construir la tabla editable de datos por modelo con validación de números no negativos, cálculos de porcentaje y totales; verificar con Vitest la validación de entrada.
- [ ] 4.2 Construir la edición del valor por criterio con referencia textual a la Guía como dato de apoyo, sin que el sistema lo evalúe como cumplimiento; verificar la visualización y la validación de la pantalla.
- [ ] 4.3 Construir el selector de evidencias para vincular datos y la lista de datos sin respaldo en la ficha de evidencia; verificar que la interfaz muestra los datos respaldados y los pendientes.

## 5. Verificación final

- [ ] 5.1 Ejecutar la suite backend y la suite de Vitest por separado; no correr la verificación de Django y la verificación frontend en paralelo con la misma tarea de cierre.
- [ ] 5.2 Ejecutar lint y build de frontend, confirmar que pasan y registrar el resultado antes de archivar el cambio.
- [ ] 5.3 Verificar la funcionalidad en navegador antes de archivar y documentar el avance en `system/docs/avance/09-cuantitativos.md` con la decisión de diseño en `system/docs/decisiones/09-cuantitativos.md`.
- [ ] 5.4 Confirmar que los artefactos finales reflejan el criterio de `pruebas solo en SQLite; verificación en PostgreSQL pendiente y documentada (D-14)` y no se marca la validación de PostgreSQL como hecha.
