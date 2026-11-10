# auditoria Specification

## Purpose

Permitir registrar de forma consistente las acciones de negocio y los accesos denegados en una trazabilidad centralizada, con persistencia inmutable y consulta por permisos para los perfiles que deben supervisar la actividad del sistema.

## Requirements

### Requirement: Registro centralizado de acciones de negocio
El sistema SHALL registrar cada acción de negocio con el usuario responsable, la acción ejecutada, la entidad afectada, el detalle del cambio y el resultado del intento, sin bloquear ni alterar la operación principal cuando la auditoría falle.

#### Scenario: Registrar una operación de negocio correcta
- **WHEN** un servicio del sistema ejecuta una operación relevante, como abrir un ciclo, cerrar un ciclo o asignar una dimensión
- **THEN** el módulo de auditoría crea un registro con la acción, el actor, la entidad, el detalle y la marca temporal correspondientes

#### Scenario: Registrar una operación de negocio con fallo
- **WHEN** la operación principal falla antes de confirmar el resultado final
- **THEN** la auditoría no debe ocultar el error del flujo de negocio ni dejar un registro que afirme un éxito no realizado

### Requirement: Registro de accesos denegados
El sistema SHALL registrar cada respuesta 403 generada por la capa de permisos, conservando la identidad del usuario, la acción denegada y la entidad objetivo sin guardar contenidos sensibles de la petición.

#### Scenario: Denegación por permiso
- **WHEN** un usuario intenta ejecutar una acción que no está autorizada
- **THEN** se guarda un evento de auditoría con el resultado `denegado`, el usuario, la acción y la entidad relacionada

### Requirement: Consulta de auditoría por permisos
El sistema SHALL permitir consultar los registros de auditoría con filtros por usuario, acción, entidad, fecha y resultado, y SHALL restringir el acceso según la norma de negocio del plan 06.

#### Scenario: Director consultando registros de su carrera
- **WHEN** un director consulta la auditoría asociada a la carrera que supervisa
- **THEN** puede ver los registros autorizados de esa área y no los de otras carreras

#### Scenario: Administrador técnico consultando todo el historial
- **WHEN** un administrador técnico accede a la auditoría
- **THEN** el sistema le permite consultar todas las acciones registradas que estén dentro del alcance administrativo
