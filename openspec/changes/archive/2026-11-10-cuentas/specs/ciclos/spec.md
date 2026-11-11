# Spec Delta

## MODIFIED Requirements

### Requirement: Apertura y cierre de ciclos de evaluación
La lógica del módulo de ciclos SHALL aplicar la autorización centralizada del módulo `cuentas` para cada operación de negocio y SHALL mantener la firma pública del servicio actual, incluso cuando el permiso real deje de estar embebido en un stub local.

#### Scenario: Abrir un ciclo válido
- **WHEN** se abre un ciclo con una carrera válida, cinco cursos consecutivos y un ciclo anterior cerrado de la misma carrera
- **THEN** el ciclo queda en estado abierto con la información de fecha de apertura y la referencia a la versión normativa y carrera correspondientes

#### Scenario: Registrar auditoría de negocio en operaciones del ciclo
- **WHEN** un usuario ejecuta `abrir_ciclo`, `cerrar_ciclo` o `asignar_dimension` con la firma actual del servicio
- **THEN** el módulo de auditoría recibe la acción de negocio, el actor, la entidad y el detalle del cambio sin requerir cambios en la interfaz pública del flujo de ciclos

#### Scenario: Rechazar apertura cuando ya existe otro ciclo abierto
- **WHEN** una carrera ya tiene un ciclo abierto
- **THEN** la apertura de otro ciclo para la misma carrera falla y no crea un segundo ciclo abierto simultáneamente

#### Scenario: Director de carrera puede abrir un ciclo
- **WHEN** el actor tiene una asignación vigente como director de carrera sobre la carrera objetivo
- **THEN** el módulo de ciclos autoriza la apertura del ciclo y conserva la trazabilidad de la operación en auditoría

#### Scenario: Miembro sin permiso no puede abrir un ciclo
- **WHEN** un miembro no autorizado intenta abrir o cerrar un ciclo
- **THEN** la operación queda denegada con el error de negocio estándar y el intento se registra como acceso denegado

#### Scenario: Integración con la función real de permisos
- **WHEN** un servicio del módulo de ciclos llama a la función centralizada de permisos del sistema
- **THEN** la decisión de acceso se toma con la misma matriz y el mismo contexto del módulo `cuentas`, sin duplicar la lógica en el servicio de ciclos
