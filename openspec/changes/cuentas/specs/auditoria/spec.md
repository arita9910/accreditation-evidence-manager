# Spec Delta

## MODIFIED Requirements

### Requirement: Consulta y registro de auditoría con alcance real de permisos
La auditoría SHALL seguir usando un registro central en tabla propia y SHALL aplicar la autorización del módulo `cuentas` al consultar registros, restringiendo los resultados cuando el actor es un director de carrera o un perfil con ámbito inferior al total del sistema.

#### Scenario: Director consultando la auditoría de su carrera
- **WHEN** un director de carrera solicita la auditoría de las acciones relacionadas con la carrera que supervisa
- **THEN** el sistema le devuelve únicamente los registros que correspondan a ese ámbito y deniega el acceso a registros ajenos

#### Scenario: Acceso denegado se registra con el actor y la acción
- **WHEN** un usuario intenta ejecutar una acción que no tiene autorizada
- **THEN** el evento de auditoría conserva la identidad del usuario, la acción denegada y la entidad sin exponer contenido sensible

#### Scenario: Administrador técnico consulta todo el alcance permitido
- **WHEN** el usuario tiene el rol de administrador técnico
- **THEN** la auditoría le da acceso al conjunto administrativo y mantiene el mismo patrón de trazabilidad que para el resto de acciones del sistema
