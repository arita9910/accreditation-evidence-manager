# Proposal

## Why

El módulo de cuentas es un requisito de la historia 0.3 del plan 05 y del incremento 1 para cerrar la autenticación de usuarios, los roles con ámbito y una sola función de autorización que sirva para el resto de módulos. La decisión D-06 exige una autorización propia sobre roles con ámbito, mientras que la lógica de ciclos y auditoría ya usa validaciones preliminares que deben sustituirse por la implementación real de este módulo para evitar duplicar reglas. (Fuente: docs/origin-plans/05-modulo-cuentas.md:3-71; docs/decisiones/README.md:52-58)

## What Changes

- Crear la capacidad `cuentas` para autenticar a los usuarios del sistema, gestionar su sesión y exponer la identidad del usuario autenticado a la UI.
- Definir roles con ámbito y vigencia (`AsignacionRol`) para carrera, facultad y ciclo, con una lógica centralizada de permisos por acción y contexto.
- Sustituir el stub `puede(...)` del módulo de ciclos y la comprobación de auditoría por la lógica real del módulo `cuentas`, manteniendo la firma actual del servicio para no romper dependencias existentes.
- Exponer la API de sesión, cambio de contraseña, consulta de identidad y administración de usuarios/roles para el administrador técnico.
- Dejar explícito el alcance de funcionalidad y las decisiones de diseño para los perfiles de director de carrera, decano, rector, administrador técnico y par evaluador con sus regímenes de acceso.

## Capabilities

### New Capabilities
- `cuentas`: autenticación de usuarios, roles con ámbito, permisos efectivos y administración de la cuenta del sistema.

### Modified Capabilities
- `ciclos`: la validación de permisos de negocio pasa a usar la lógica real del módulo `cuentas` sin cambiar la firma del servicio ni la semántica de la operación.
- `auditoria`: consulta y trazabilidad de accesos denegados y acciones de negocio reciben la lógica de permisos del módulo `cuentas` y conservan los requisitos de alcance definido por el plan 05.

## Impact

- `sistema/backend/cuentas/`: modelos, servicios, permisos, serializadores, vistas, URLs, pruebas y lógica de sesión.
- `sistema/backend/ciclos/servicios.py` y `sistema/backend/ciclos/vistas.py`: reemplazo del stub de permisos por `cuente.permisos.puede` y validación del flujo de negocio.
- `sistema/backend/auditoria/vistas.py`: consulta de registros con alcance por perfil, manteniendo la regla de acceso de director y administrador técnico.
- UI y contratos de API bajo `/api/`, con sesión de Django + CSRF y sin JWT, según D-13 y el plan 05.
