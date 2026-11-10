# Spec Delta

## MODIFIED Requirements

### Requirement: Permisos de negocio del módulo de ciclos
La lógica del módulo de ciclos SHALL aplicar la autorización centralizada del módulo `cuentas` para cada operación de negocio y SHALL mantener la firma pública del servicio actual, incluso cuando el permiso real deje de estar embebido en un stub local.

#### Scenario: Director de carrera puede abrir un ciclo
- **WHEN** el actor tiene una asignación vigente como director de carrera sobre la carrera objetivo
- **THEN** el módulo de ciclos autoriza la apertura del ciclo y conserva la trazabilidad de la operación en auditoría

#### Scenario: Miembro sin permiso no puede abrir un ciclo
- **WHEN** un miembro no autorizado intenta abrir o cerrar un ciclo
- **THEN** la operación queda denegada con el error de negocio estándar y el intento se registra como acceso denegado

#### Scenario: Integración con la función real de permisos
- **WHEN** un servicio del módulo de ciclos llama a la función centralizada de permisos del sistema
- **THEN** la decisión de acceso se toma con la misma matriz y el mismo contexto del módulo `cuentas`, sin duplicar la lógica en el servicio de ciclos
