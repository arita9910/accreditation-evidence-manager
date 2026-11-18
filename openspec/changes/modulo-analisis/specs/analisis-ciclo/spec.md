# Spec Delta

## Purpose

Definir consultas de estado, completitud y comparación de ciclos como capacidades de solo lectura. El módulo informa y no evalúa: no calcula cumplimiento ni devuelve categoría de acreditación. Fuente: [Plan 11](../../../../../docs/origin-plans/11-modulo-analisis.md#L3-L4).

## ADDED Requirements

### Requirement: Consultar el estado agregado de un ciclo
El sistema SHALL presentar el estado de un ciclo organizado por dimensión, indicador y criterio, incluyendo cantidad de evidencias clasificadas, datos cuantitativos aplicables y su respaldo, valoraciones y acciones de mejora asociadas. Fuente: [Plan 11](../../../../../docs/origin-plans/11-modulo-analisis.md#L17-L18).

#### Scenario: Consultar estado de un ciclo autorizado
- **WHEN** un usuario autorizado solicita el estado de un ciclo de su ámbito
- **THEN** la API devuelve el árbol dimensión-indicador-criterio con identificadores y estados resumidos

#### Scenario: Consultar un ciclo cerrado
- **WHEN** un usuario autorizado consulta estado o completitud de un ciclo cerrado
- **THEN** la API responde correctamente (solo lectura) sin exigir ciclo abierto

### Requirement: Informar completitud sin bloquear operaciones
El sistema SHALL devolver seis tipos de aviso: `criterios_sin_evidencia`, `criterios_cuantitativos_sin_dato`, `datos_sin_respaldo`, `modelos_incompletos`, `dimensiones_sin_valoracion`, `debilidades_sin_accion`, sin impedir que el ciclo continúe ni calcular cumplimiento. Fuente: [Plan 11](../../../../../docs/origin-plans/11-modulo-analisis.md#L21).

#### Scenario: Obtener tipos de aviso conocidos
- **WHEN** un ciclo contiene pendientes definidos por completitud
- **THEN** la API devuelve las listas por tipo de aviso y mantiene una respuesta informativa

#### Scenario: Completitud sin datos mínimos
- **WHEN** el ciclo no tiene evidencias, datos cuantitativos o valoraciones
- **THEN** el sistema devuelve tipos de aviso estructurados en lugar de bloquear

### Requirement: Comparar ciclos de la misma carrera
El sistema SHALL comparar diferencias en valores de modelos, valores de criterio y estados de acciones de mejora únicamente entre ciclos de la misma carrera. Fuente: [Plan 11](../../../../../docs/origin-plans/11-modulo-analisis.md#L23-L26).

#### Scenario: Comparar ciclos válidos
- **WHEN** un usuario autorizado solicita comparar dos ciclos de la misma carrera
- **THEN** la API devuelve diferencias en modelos, criterios y acciones
- **AND** (propuesta provisional) empareja cursos por posición relativa dentro de cada ciclo (`curso - curso_inicial`) y compara `ValorCriterio` por `criterio_id`

#### Scenario: Rechazar ciclos de carreras distintas
- **WHEN** los ciclos pertenecen a carreras diferentes
- **THEN** el sistema devuelve HTTP 400 con formato estándar de error

#### Scenario: Rechazar comparación con parámetros incompletos
- **WHEN** falta `a` o falta `b` en `/api/comparaciones/`
- **THEN** el sistema devuelve HTTP 400 con formato estándar de error
- **AND** (propuesta provisional) usa `codigo="parametros_invalidos"` y mensaje en español

#### Scenario: Rechazar comparación del mismo ciclo
- **WHEN** `a` y `b` son iguales
- **THEN** el sistema devuelve HTTP 400 con formato estándar de error
- **AND** (propuesta provisional) usa `codigo="comparacion_invalida"`

#### Scenario: Rechazar ciclo inexistente
- **WHEN** `a` o `b` no corresponde a un ciclo existente
- **THEN** el sistema devuelve HTTP 404 con formato estándar de error
- **AND** (propuesta provisional) usa `codigo="ciclo_no_encontrado"`

### Requirement: Aplicar permisos reales y control de sesión
El sistema SHALL exigir sesión para consultar análisis y SHALL aplicar autorización mediante `puede(...)` según implementación vigente.

#### Scenario: Sesión ausente
- **WHEN** una solicitud llega sin sesión autenticada
- **THEN** el sistema rechaza la operación con código de autenticación del proyecto y formato estándar de error
- **AND** (propuesta provisional) devuelve HTTP 403 con `codigo="autenticacion_requerida"`

#### Scenario: Permisos vigentes para comparación
- **WHEN** se solicita comparación autenticada
- **THEN** se aplica `puede(...)` con el ciclo/carrera de contexto
- **AND** se documenta discrepancia con la matriz objetivo del Plan 05 cuando la acción no esté tipificada en `_PERMISOS_POR_ACCION`

#### Scenario: Roles aún no cerrados funcionalmente
- **WHEN** la matriz funcional exige decano, rector, miembro y par evaluador en análisis
- **THEN** el cambio deja esos roles como pregunta abierta con propuesta provisional y sin inventar reglas no implementadas

### Requirement: Auditar comparaciones autorizadas y denegaciones 403
El sistema SHALL registrar con `registrar(...)` las comparaciones autorizadas. Las denegaciones 403 SHALL quedar registradas por el middleware de auditoría existente.

#### Scenario: Registrar una comparación autorizada
- **WHEN** una comparación se ejecuta con permiso
- **THEN** el sistema crea un evento de auditoría con acción y contexto

#### Scenario: Registrar una denegación por middleware
- **WHEN** la capa API responde 403
- **THEN** el middleware registra el acceso denegado sin duplicar registro manual en la vista de análisis

### Requirement: Mantener consultas acotadas y UI con resaltado
El sistema SHALL limitar consultas SQL mediante carga anticipada/agregaciones y SHALL permitir filtrar tipos de aviso y resaltar diferencias en interfaz React. Fuente: [Plan 11](../../../../../docs/origin-plans/11-modulo-analisis.md#L28-L29).

#### Scenario: Consultar sin crecimiento lineal de queries
- **WHEN** se solicita estado de un ciclo con su jerarquía completa
- **THEN** el número de consultas se mantiene acotado y validado con `assertNumQueries`

#### Scenario: Filtrar avisos y resaltar diferencias
- **WHEN** el usuario activa filtros o revisa comparación
- **THEN** la interfaz muestra solo elementos con avisos y destaca diferencias
