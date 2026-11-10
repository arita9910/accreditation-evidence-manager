# Spec Delta

## MODIFIED Requirements

### Requirement: Apertura y cierre de ciclos de evaluación
La lógica del módulo de ciclos SHALL mantener las reglas de apertura y cierre ya establecidas y SHALL registrar cada operación relevante a través del servicio de auditoría sin cambiar la firma ni la semántica del flujo de negocio existente.

#### Scenario: Abrir un ciclo válido
- **WHEN** se abre un ciclo con una carrera válida, cinco cursos consecutivos y un ciclo anterior cerrado de la misma carrera
- **THEN** el ciclo queda en estado abierto con la información de fecha de apertura y la referencia a la versión normativa y carrera correspondientes

#### Scenario: Registrar auditoría de negocio en operaciones del ciclo
- **WHEN** un usuario ejecuta `abrir_ciclo`, `cerrar_ciclo` o `asignar_dimension` con la firma actual del servicio
- **THEN** el módulo de auditoría recibe la acción de negocio, el actor, la entidad y el detalle del cambio sin requerir cambios en la interfaz pública del flujo de ciclos

#### Scenario: Rechazar apertura cuando ya existe otro ciclo abierto
- **WHEN** una carrera ya tiene un ciclo abierto
- **THEN** la apertura de otro ciclo para la misma carrera falla y no crea un segundo ciclo abierto simultáneamente
