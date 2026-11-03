# Plan 09 — Módulo cuantitativos (incremento 3)

## Objetivo
Capturar los datos cuantitativos de los 11 modelos resumen y el valor propio de los criterios cuantitativos sin modelo, y vincular cada dato con las evidencias que lo respaldan, en ambos sentidos.

## Convenciones comunes
- Django 5.2 + DRF; React 18 + Vite (JS); SQLite en desarrollo y PostgreSQL en producción.
- Nombres en español. App `sistema/backend/cuantitativos/` con `modelos.py`, `servicios.py`, `serializadores.py`, `vistas.py`, `urls.py`, `tests/`. Lógica en servicios; vistas delgadas.
- API bajo `/api/`, JSON, sesión + CSRF. Permisos con `cuentas.permisos.puede(...)`; auditoría con `registrar(...)`; escrituras exigen ciclo abierto.
- Indicador = 2.º nivel; criterio = 3.er nivel. Ambigüedad → `docs/decisiones/`.

## Contexto
CU-10 (registrar datos), CU-11 (vincular dato con evidencias), CU-12 (consultar datos sin respaldo). Decisiones: **D-05** (solo los 11 modelos resumen, no registros nominales) y **D-04** (los modelos como celdas genéricas con definición por modelo; si la plantilla real de la base de datos Excel del CTE-CU difiere, se cambian datos y no código). Depende de planes 07, 04, 03. De los 38 criterios cuantitativos, 18 reciben datos de un modelo; los otros 20 usan `ValorCriterio`. La correspondencia criterio–modelo es una propuesta a validar con la comisión. **La plantilla vacía de la base de datos Excel aún no está disponible**: construir sobre la definición de los modelos del Manual (Anexo 6) y dejar la estructura de celdas como datos.

## Entidades (plan 01, oleada D)
- **ValorModelo:** ciclo (FK), campo (FK a ModeloCampo), curso, valor, numerador, denominador; único (ciclo, campo, curso).
- **ValorCriterio:** ciclo (FK), criterio (FK), curso (nulo), valor, numerador, denominador, unidad, observacion.
- **VinculoDato:** evidencia (FK), valor_modelo (FK nulo), valor_criterio (FK nulo); **CHECK: exactamente uno** de los dos datos.
Ya existen (plan 03): ModeloDefinicion, ModeloCampo, CriterioModelo. Los datos se registran **por curso** dentro del ciclo (cinco cursos); el claustro sobre el último curso concluido (año base).

## Tareas

### T1 — Modelos, migraciones, CHECK de VinculoDato y pruebas (incluida la violación del CHECK).

### T2 — Servicios
- `guardar_valores_modelo(ciclo, modelo, curso, celdas, usuario)`: valida tipo por campo (entero, decimal, porcentaje, texto), no negativos, coherencia de totales donde el modelo lo defina; porcentajes calculados desde numerador/denominador cuando ambos existan.
- `guardar_valor_criterio(ciclo, criterio, ...)`: solo para criterios cuantitativos sin modelo (rechaza los demás).
- `rellenar_acreditacion_anterior(ciclo)`: copia la columna «acreditación anterior» desde el ciclo previo cuando existe.
- `vincular(dato, evidencias, usuario)` / `desvincular`; `datos_sin_respaldo(ciclo)`: datos sin ningún vínculo; `datos_de_evidencia(evidencia)`.
- Permiso: miembro solo en dimensiones asignadas; director siempre; ciclo abierto.
- **Aceptación (pruebas):** cada cálculo de índice y porcentaje de los modelos con casos conocidos; valor de criterio rechazado si el criterio tiene modelo o es cualitativo; un dato sin evidencia aparece en `sin_respaldo` y deja de aparecer al vincularlo; el vínculo se recorre en ambos sentidos; el CHECK impide vincular dos datos a la vez; administrador técnico sin acceso.

### T3 — API
- `GET/PUT /api/ciclos/{id}/modelos/{n}/valores/?curso=`.
- `GET/PUT /api/ciclos/{id}/criterios/{codigo}/valor/`.
- `POST/DELETE /api/vinculos/`; `GET /api/evidencias/{id}/datos/`; `GET /api/datos/{tipo}/{id}/evidencias/`.
- `GET /api/ciclos/{id}/datos/sin-respaldo/`.
- **Aceptación:** pruebas de API con permisos positivos y negativos.

### T4 — Pantallas React
Captura por modelo en forma de tabla con validaciones y totales; valor del criterio mostrando el requisito de la Guía junto al dato **solo como referencia** («El sistema no evalúa el cumplimiento»); selector de evidencias para vincular; lista de datos sin respaldo; en la ficha de evidencia, los datos que respalda. **Aceptación (Vitest):** la tabla valida no negativos y calcula porcentajes.

## Fuera de alcance
Registros nominales (cada profesor, cada publicación), importación de la base de datos Excel del CTE-CU (futuro), cálculo automático de categoría o de cumplimiento.

## Definición de terminado
Pruebas en verde en SQLite y PostgreSQL; vínculo dato–evidencia bidireccional funcionando; avance en `docs/avance/09-cuantitativos.md`.
