# Spec Delta

## MODIFIED Requirements

### Requirement: Consulta de auditoría por permisos
La auditoría SHALL seguir usando un registro central en tabla propia y SHALL aplicar la autorización del módulo `cuentas` al consultar registros, restringiendo los resultados cuando el actor es un director de carrera o un perfil con ámbito inferior al total del sistema.

#### Scenario: Director consultando registros de su carrera
- **WHEN** un director consulta la auditoría asociada a la carrera que supervisa
- **THEN** puede ver los registros autorizados de esa área y no los de otras carreras

#### Scenario: Administrador técnico consultando todo el historial
- **WHEN** un administrador técnico accede a la auditoría
- **THEN** el sistema le permite consultar todas las acciones registradas que estén dentro del alcance administrativo

#### Scenario: Director de carrera consulta la auditoría de su ámbito
- **WHEN** un director de carrera solicita la auditoría de las acciones relacionadas con la carrera que supervisa
- **THEN** el sistema le devuelve únicamente los registros que correspondan a ese ámbito y deniega el acceso a registros ajenos

#### Scenario: Acceso denegado se registra con el actor y la acción
- **WHEN** un usuario intenta ejecutar una acción que no tiene autorizada
- **THEN** el evento de auditoría conserva la identidad del usuario, la acción denegada y la entidad sin exponer contenido sensible

#### Scenario: Administrador técnico consulta todo el alcance permitido
- **WHEN** el usuario tiene el rol de administrador técnico
- **THEN** la auditoría le da acceso al conjunto administrativo y mantiene el mismo patrón de trazabilidad que para el resto de acciones del sistema
