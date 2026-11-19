# Design

## Context

El módulo de análisis consulta ciclos, catálogo, evidencias, cuantitativos, valoraciones y mejora sin crear entidades propias. El Plan 11 exige tres servicios de consulta (`estado_ciclo`, `completitud`, `comparar`) y tres endpoints REST ([Plan 11](../../../docs/origin-plans/11-modulo-analisis.md#L17-L26)).

El módulo es solo de lectura: no crea ni modifica datos del ciclo, por lo que no invoca `exigir_ciclo_abierto`.

## Goals / Non-Goals

**Goals:**
- Ofrecer resultados deterministas por dimensión, indicador y criterio.
- Mantener consultas con número acotado de SQL.
- Reutilizar permisos (`puede(...)`) y auditoría (`registrar(...)`) existentes.
- Entregar completitud como información (tipos de aviso), sin bloqueo.

**Non-Goals:**
- Crear modelos o migraciones para `analisis`.
- Calcular cumplimiento o categoría de acreditación.
- Escribir datos de ciclo desde endpoints de análisis.

## Decisions

### 1. App sin modelos propios
- **Decisión:** `sistema/backend/analisis/` no define `modelos.py` de dominio ni migraciones.
- **Rationale:** el plan declara explícitamente que no tiene tablas propias ([Plan 11](../../../docs/origin-plans/11-modulo-analisis.md#L3-L4)).

### 2. Tipos de aviso de completitud (no categorías)
- **Decisión:** usar `tipos_aviso` y reservar "categoría" para la acreditación (Calificada/Certificada/Excelencia), que no se calcula ni se devuelve.
- **Rationale:** evita ambigüedad terminológica con la categoría de acreditación.

Tabla base de tipos de aviso (Plan 11 L20-L21):

| Tipo de aviso (funcional) | Clave JSON propuesta | Origen (tabla/modelo) | Fuente |
| --- | --- | --- | --- |
| criterios sin evidencia | `criterios_sin_evidencia` | `estructura.Criterio` + clasificaciones de `evidencias` | [Plan 11 L21](../../../docs/origin-plans/11-modulo-analisis.md#L21) |
| criterios cuantitativos sin dato | `criterios_cuantitativos_sin_dato` | `estructura.Criterio` + `cuantitativos.ValorModelo` / `cuantitativos.ValorCriterio` | [Plan 11 L21](../../../docs/origin-plans/11-modulo-analisis.md#L21) |
| datos sin respaldo | `datos_sin_respaldo` | Reusar `datos_sin_respaldo(ciclo)` de cuantitativos | [Plan 09 L29](../../../docs/origin-plans/09-modulo-cuantitativos.md#L29), [Plan 11 L21](../../../docs/origin-plans/11-modulo-analisis.md#L21) |
| modelos incompletos | `modelos_incompletos` | `cuantitativos.ValorModelo` + definición de celdas por `estructura.ModeloCampo` | [Plan 11 L21](../../../docs/origin-plans/11-modulo-analisis.md#L21) |
| dimensiones sin valoración | `dimensiones_sin_valoracion` | `valoracion.Valoracion` agrupada por dimensión | [Plan 11 L21](../../../docs/origin-plans/11-modulo-analisis.md#L21) |
| debilidades sin acción | `debilidades_sin_accion` | `valoracion.Valoracion` (`tipo=debilidad`) sin `mejora.AccionMejora` | [Plan 11 L21](../../../docs/origin-plans/11-modulo-analisis.md#L21) |

### 3. Permisos y sesión según implementación real
- **Decisión:** documentar y probar permisos con lo que hoy hace `puede(...)`.
- **Estado actual verificado:**
  - Sin sesión (`actor is None`) → denegado (`False`) ([permisos.py L210](../../../sistema/backend/cuentas/permisos.py#L210)).
  - Si la acción no existe en `_PERMISOS_POR_ACCION`, `puede(...)` devuelve `True` para usuarios autenticados ([permisos.py L22](../../../sistema/backend/cuentas/permisos.py#L22), [permisos.py L223](../../../sistema/backend/cuentas/permisos.py#L223)).
  - `administrador_tecnico` siempre autoriza acciones tipificadas ([permisos.py L227](../../../sistema/backend/cuentas/permisos.py#L227)).
  - `director_carrera` queda acotado por carrera cuando se pasa objeto contextual ([permisos.py L194](../../../sistema/backend/cuentas/permisos.py#L194)).
- **Discrepancia anotada:** la matriz del Plan 05 indica que administrador técnico no compara ciclos, pero la acción de comparación no está tipificada hoy, por lo que `puede(...)` no materializa esa restricción ([Plan 05](../../../docs/origin-plans/05-modulo-cuentas.md#L59)).

### 4. `exigir_ciclo_abierto` fuera del módulo análisis
- **Decisión:** `estado`, `completitud` y `comparar` no invocan `exigir_ciclo_abierto`.
- **Rationale:** son operaciones de solo lectura y la comparación debe funcionar también con ciclos cerrados.

### 5. Auditoría: comparar autorizado sí, 403 por middleware
- **Decisión:** registrar con `registrar(...)` solo comparaciones autorizadas.
- **Rationale:** los rechazos 403 ya se registran de forma centralizada por middleware ([middleware.py L13](../../../sistema/backend/auditoria/middleware.py#L13), [middleware.py L17](../../../sistema/backend/auditoria/middleware.py#L17), [middleware.py L41](../../../sistema/backend/auditoria/middleware.py#L41)); `registrar(...)` recibe `resultado` para distinguir eventos ([servicios.py L22](../../../sistema/backend/auditoria/servicios.py#L22), [servicios.py L25](../../../sistema/backend/auditoria/servicios.py#L25)).

### 6. Comparación entre ciclos: emparejamiento provisional
- **Decisión (provisional, pendiente de tutor):**
  - Valores de modelo: emparejar por `(campo_id, posicion_relativa_curso)`, donde `posicion_relativa_curso = curso - ciclo.curso_inicial`.
  - Valores de criterio: comparar por `criterio_id` (sin curso), porque `ValorCriterio` es único por `(ciclo, criterio)` y el `curso` es opcional ([models.py L91](../../../sistema/backend/cuantitativos/models.py#L91), [models.py L115](../../../sistema/backend/cuantitativos/models.py#L115)).
  - Acciones de mejora: comparar por estado normalizado de `AccionMejora.Estado` (`propuesta`, `aprobada`, `en_curso`, `cumplida`, `no_cumplida`) ([modelos.py L64](../../../sistema/backend/mejora/modelos.py#L64)).
- **Nota de reutilización Plan 10:** en frontend existe visualización de estado y plan anterior en [Mejora.jsx](../../../sistema/frontend/src/paginas/Mejora.jsx), pero no una utilidad genérica de comparación de acciones; se reutiliza nomenclatura de estados, no lógica de diff.

### 7. Payloads provisionales para cerrar preguntas previas
- **Estado (`estado_ciclo`)**: devolver identificadores y estado resumido (`id`, `codigo`, `nombre`, contadores booleanos) en lugar de objetos completos de valoración/acción.
- **Diferencias (`comparar`)**: lista tipada por bloque:
  - `diferencias_modelos[] = {campo_id, posicion_relativa, curso_a, curso_b, valor_a, valor_b, numerador_a, numerador_b, denominador_a, denominador_b}`
  - `diferencias_criterios[] = {criterio_id, valor_a, valor_b, numerador_a, numerador_b, denominador_a, denominador_b, unidad_a, unidad_b}`
  - `diferencias_acciones[] = {debilidad_id, estado_a, estado_b, total_a, total_b}`

## Risks / Trade-offs

- [Permisos reales vs matriz ideal] → documentar discrepancia y no inventar roles no implementados.
- [Comparación de cursos no alineables por número absoluto] → usar posición relativa al `curso_inicial` (provisional).
- [Ambigüedad de "sin valoración"] → mantener pregunta abierta hasta validación de tutor.

## Migration Plan

No aplica migración de datos: no hay tablas nuevas en `analisis`.

## Preguntas abiertas (con propuesta provisional)

1. **¿"Sin valoración" se mide por dimensión o por criterio?**  
   - Evidencia: Plan 11 usa "dimensiones sin valoración" ([Plan 11 L21](../../../docs/origin-plans/11-modulo-analisis.md#L21)); CU-14 habla de fortalezas/debilidades por dimensión con criterios ([Plan 12 L14](../../../docs/origin-plans/12-modulo-informes.md#L14)).  
   - **Propuesta provisional:** mantener `dimensiones_sin_valoracion` hasta confirmación del tutor.

2. **¿Qué define exactamente "modelo incompleto"?**  
   - Evidencia: el plan lo exige pero no define umbral/regla ([Plan 11 L21](../../../docs/origin-plans/11-modulo-analisis.md#L21)).  
   - **Propuesta provisional:** incompleto si falta al menos una celda esperada en un modelo/curso.

3. **¿Cómo contar "sin dato" para criterios que reciben datos desde modelo?**  
   - Evidencia: 18 criterios dependen de modelo y 20 usan `ValorCriterio` ([Plan 09 L13](../../../docs/origin-plans/09-modulo-cuantitativos.md#L13)).  
   - **Propuesta provisional:** un criterio con modelo está "sin dato" si no existe valor en ninguna celda requerida del modelo asociado para su posición relativa.

4. **¿Se habilitarán decano, rector, miembro y par evaluador en análisis?**  
   - Evidencia: matriz objetivo del Plan 05 vs implementación actual de `puede(...)` ([Plan 05](../../../docs/origin-plans/05-modulo-cuentas.md#L59), [permisos.py L223](../../../sistema/backend/cuentas/permisos.py#L223)).  
   - **Propuesta provisional:** cubrir explícitamente director por carrera, administrador técnico según implementación actual y sin sesión denegada; dejar los demás roles como pendiente funcional.

5. **¿Se confirma el emparejamiento por posición relativa de curso?**  
   - Evidencia: cada ciclo cubre 5 cursos (`curso_final = curso_inicial + 4`) ([modelos.py L94](../../../sistema/backend/ciclos/modelos.py#L94)).  
   - **Propuesta provisional:** usar posición relativa y validar con tutor antes de cerrar implementación.
