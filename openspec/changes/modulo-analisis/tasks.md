# Tasks

## 1. Modelos

- [ ] 1.1 Confirmar que `analisis` no introduce tablas ni migraciones y reutiliza los modelos existentes; verificar con `python manage.py makemigrations --check --dry-run` y que `analisis` esté registrado en `INSTALLED_APPS`
- [ ] 1.2 Definir estructuras en memoria para estado, completitud y comparación, sin calcular ni devolver categoría de acreditación; verificar con pruebas unitarias de payload

## 2. Servicios

- [ ] 2.1 Implementar `estado_ciclo(ciclo)` con carga anticipada de dimensiones, indicadores, criterios, clasificaciones, valores, vínculos, valoraciones y acciones; construir aquí mismo los límites de `assertNumQueries` para recorrer árbol completo sin N+1
- [ ] 2.2 Implementar `completitud(ciclo)` para seis **tipos de aviso** (`criterios_sin_evidencia`, `criterios_cuantitativos_sin_dato`, `datos_sin_respaldo`, `modelos_incompletos`, `dimensiones_sin_valoracion`, `debilidades_sin_accion`) reusando la consulta `datos_sin_respaldo(ciclo)` del módulo cuantitativos
- [ ] 2.3 Implementar `comparar(ciclo_a, ciclo_b)` con validación de misma carrera y diferencias de modelos, criterios y estados de acciones; incluir propuesta provisional de emparejamiento por posición relativa del curso y `ValorCriterio` por criterio
- [ ] 2.4 Integrar `puede(...)` y `registrar(...)` en autorización y auditoría de comparación autorizada; **no** invocar `exigir_ciclo_abierto` en endpoints de análisis por ser de solo lectura
- [ ] 2.5 Documentar y probar discrepancias entre matriz objetivo y comportamiento real de `puede(...)` para comparación, incluyendo caso sin sesión

## 3. API

- [ ] 3.1 Crear serializadores de estado, completitud y comparación con formato de error estándar (`codigo`, `mensaje`, `detalle`); verificar serialización de datos completos y vacíos
- [ ] 3.2 Implementar `GET /api/ciclos/{id}/estado/` y `GET /api/ciclos/{id}/completitud/`; verificar autenticación, ámbito y consulta de ciclo cerrado
- [ ] 3.3 Implementar `GET /api/comparaciones/?a=&b=`; verificar casos: válido, carrera distinta (400), `a`/`b` ausentes (400), `a==b` (400), ciclo inexistente (404), sin sesión y permisos de director (su carrera) + administrador técnico según comportamiento real de `puede(...)`; dejar decano, rector, miembro y par evaluador como pregunta abierta
- [ ] 3.4 Registrar en rutas `/api/` y probar CSRF/sesión según patrón existente; verificar que los 403 queden auditados por middleware sin duplicación

## 4. Pantallas

- [ ] 4.1 Crear tablero React del estado del ciclo con árbol dimensión-indicador-criterio e indicadores visuales; verificar renderizado con Vitest
- [ ] 4.2 Crear vista React de completitud y filtro "solo con avisos"; verificar en Vitest que oculta elementos sin avisos
- [ ] 4.3 Crear vista React de comparación entre dos ciclos con diferencias resaltadas; verificar en Vitest el resaltado
- [ ] 4.4 Conectar pantallas a endpoints y añadir entrada de menú por rol/permiso disponible; verificar flujos positivos y negativos en componentes

## 5. Verificación

- [ ] 5.1 Ejecutar pruebas backend existentes y nuevas de `analisis` solo con SQLite; verificar paso sin dependencias nuevas
- [ ] 5.2 Ejecutar pruebas Vitest del filtro y de diferencias
- [ ] 5.3 Ejecutar `openspec validate modulo-analisis`
- [ ] 5.4 Registrar resultado verificable y pendientes en `sistema/docs/avance/11-analisis.md`
- [ ] 5.5 Realizar prueba en navegador de las tres pantallas (estado, completitud y comparación) antes de archivar; documentar evidencia y pendientes en `sistema/docs/avance/11-analisis.md`

## Workflow follow-up

- Registrar dudas no resueltas con fuente y línea en `sistema/docs/decisiones/`.
- Tras resolver preguntas abiertas y aprobar tareas, ejecutar `/opsx-apply` para implementación.
- Mantener PostgreSQL como pendiente documentado (D-14), sin declararlo como validado.
