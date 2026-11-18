# Mejora Specification

## Purpose

TBD - Update Purpose after archive

## Requirements

### Requirement: Plan de mejora por ciclo

El sistema SHALL gestionar un único plan de mejora por ciclo en el que se registren las acciones de corrección asociadas a debilidades detectadas y se conserve el estado del plan hasta su cierre o revisión posterior.

#### Scenario: Registro de plan de mejora válido

- **GIVEN** un ciclo con actividad de evaluación habilitada
- **WHEN** se registra un plan de mejora para ese ciclo
- **THEN** el sistema crea el plan asociado al ciclo y conserva su estado de aprobación y ejecución

#### Scenario: Rechazo de plan sin ciclo válido

- **GIVEN** una solicitud de creación sin un ciclo válido
- **WHEN** se intenta registrar el plan de mejora
- **THEN** la operación falla por validación de negocio y no persiste un registro inconsistente

### Requirement: Acciones de mejora vinculadas a debilidades

El sistema SHALL exigir que toda acción de mejora esté vinculada a una debilidad de origen identificada dentro de la valoración o la autoevaluación, y no SHALL permitir la creación de acciones sin ese origen.

#### Scenario: Propuesta con debilidad válida

- **GIVEN** una debilidad válida del ciclo activo
- **WHEN** un usuario propone una acción de mejora vinculada a esa debilidad
- **THEN** el sistema registra la acción y conserva la referencia al origen

#### Scenario: Rechazo de acción sin origen válido

- **GIVEN** una propuesta sin debilidad o con una debilidad inexistente o fuera del ciclo
- **WHEN** se intenta crear la acción
- **THEN** la operación queda rechazada con error de negocio y se registra la trazabilidad del rechazo

### Requirement: Estados, fechas y responsabilidades

El sistema SHALL controlar la transición de estados de cada acción de mejora, garantizar responsable y fecha límite, y registrar el histórico del seguimiento con la persona que ejecuta la actualización.

#### Scenario: Transición de estado permitida

- **GIVEN** una acción con estado actual válido
- **WHEN** el responsable o el director solicita una transición definida por el negocio
- **THEN** el sistema actualiza el estado y registra el usuario y la marca temporal del cambio

#### Scenario: Detección de acción vencida

- **GIVEN** una acción sin estado final y con fecha límite superada
- **WHEN** se consulta el seguimiento del plan
- **THEN** la funcionalidad de vencidas la identifica como pendiente y la muestra de forma destacada

### Requirement: Integración con permisos, auditoría y ciclo abierto

El sistema SHALL integrar la creación, actualización y cierre de acciones de mejora con los servicios de permisos y auditoría ya existentes, y SHALL requerir que la operación se ejecute solo si el ciclo asociado está abierto.

#### Scenario: Bloqueo por ciclo cerrado

- **GIVEN** una operación de escritura sobre una acción de mejora
- **WHEN** el ciclo asociado está cerrado
- **THEN** se invoca `exigir_ciclo_abierto` y la operación falla antes de guardar cambios

#### Scenario: Denegación por permisos insuficientes

- **GIVEN** un usuario sin permisos suficientes para crear o aprobar acciones
- **WHEN** intenta ejecutar la operación
- **THEN** el sistema la deniega mediante `puede(...)` y registra el intento en auditoría

### Requirement: Seguimiento y evidencias del cumplimiento

El sistema SHALL permitir añadir seguimientos y evidencias a cada acción de mejora, y SHALL mantener la relación del plan del ciclo anterior para valorar cómo se resolvieron las deficiencias previas.

#### Scenario: Registro de avance con evidencia

- **GIVEN** una acción de mejora existente
- **WHEN** se registra un avance con notas y evidencias asociadas
- **THEN** el sistema conserva la relación entre acción, seguimiento y evidencias para trazabilidad del cumplimiento

#### Scenario: Consulta del plan del ciclo anterior

- **GIVEN** un ciclo actual con referencia a ciclo anterior
- **WHEN** se consulta el plan de mejora del ciclo anterior
- **THEN** la API devuelve el estado final de las acciones previas para compararlo con el plan actual
