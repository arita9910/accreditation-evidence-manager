# Spec Delta

## Purpose

La capacidad de cuentas define la autenticación, los roles con ámbito y la autorización centralizada del sistema para que cada acción se valide con una sola función de permisos y no con reglas duplicadas por módulo.

## ADDED Requirements

### Requirement: Autenticación con sesión y gestión de la cuenta
El sistema SHALL autenticar a los usuarios mediante nombre de usuario y contraseña con sesión de Django, SHALL permitir cerrar sesión y SHALL validar el cambio de contraseña con los validadores de Django.

#### Scenario: Inicio de sesión correcto
- **WHEN** un usuario introduce un nombre de usuario y una contraseña válida
- **THEN** la API crea la sesión del usuario y devuelve el estado autenticado sin requerir JWT

#### Scenario: Credenciales incorrectas
- **WHEN** un usuario falla la autenticación repetidamente
- **THEN** el sistema aplica el límite de intentos configurado y registra el acceso denegado en auditoría

#### Scenario: Cierre de sesión y cambio de clave
- **WHEN** el usuario cierra la sesión o solicita cambiar la contraseña
- **THEN** la aplicación invalidará la sesión actual o actualizará la contraseña con validación del backend

### Requirement: Modelo de usuario con rol único y carrera asignada
El sistema SHALL mantener `cuentas.Usuario` con `AbstractBaseUser` + `PermissionsMixin` y SHALL registrar el rol activo y la carrera asociada del usuario sin heredar de `ModeloBase`. La trazabilidad SHALL realizarse por medio del servicio `registrar(...)` de auditoría para conservar usuario, acción y ámbito sin duplicar reglas de dominio en la identidad.

#### Scenario: Usuario con rol de administrador técnico
- **WHEN** un usuario tiene el rol `Administrador Técnico`
- **THEN** el sistema le concede acceso global para todas las carreras y operaciones del sistema

#### Scenario: Usuario con rol de director de carrera
- **WHEN** un usuario tiene el rol `Director de Carrera` y una carrera asignada
- **THEN** el sistema restringe sus permisos a esa carrera concreta y no a otras carreras del sistema

#### Scenario: Un único rol activo por usuario
- **WHEN** un usuario tiene un solo rol activo definido en su modelo
- **THEN** la autorización de cuentas y la auditoría usan ese rol como fuente de verdad y no permiten un conflicto de permisos por rol simultáneo

### Requirement: Roles con ámbito y acceso restringido por carrera
El sistema SHALL modelar el acceso con un único rol activo por usuario, usando `Administrador Técnico` para el alcance global y `Director de Carrera` para el alcance restringido a la carrera designada por una `ForeignKey`, y SHALL impedir que la evaluación de permisos ignore ese alcance.

#### Scenario: Director de carrera consultando auditoría
- **WHEN** un director de carrera solicita registros de auditoría relacionados con la carrera que supervisa
- **THEN** el sistema devuelve únicamente los registros de ese ámbito y deniega el acceso a registros ajenos

#### Scenario: Administrador técnico consultando toda la auditoría
- **WHEN** un usuario tiene el rol de administrador técnico
- **THEN** la auditoría le da acceso a la vista global del sistema y mantiene la trazabilidad de todas las acciones

#### Scenario: Módulo de ciclos respetando el alcance del director
- **WHEN** un director de carrera intenta operar sobre una carrera distinta a la que tiene asignada
- **THEN** la operación queda denegada y el bloqueo se registra con usuario, acción y entidad sin contenido sensible

### Requirement: Autorización centralizada por acción y contexto
La aplicación SHALL evaluar cada permiso mediante una única función `puede(usuario, accion, objeto=None)` y SHALL aplicar la decisión en la capa de permisos de DRF para las acciones del sistema, con la matriz de roles y los requisitos de acceso por carrera, facultad, ciclo y administrador técnico.

#### Scenario: Director de carrera abre un ciclo
- **WHEN** un director de carrera activa la acción de abrir ciclo sobre su carrera
- **THEN** el sistema autoriza la acción y la operación se ejecuta con el ámbito correcto

#### Scenario: Miembro sin permiso intenta editar un ciclo
- **WHEN** un miembro sin permisos de organización intenta ejecutar una acción de apertura o cierre
- **THEN** la solicitud queda denegada y el intento se registra en auditoría

#### Scenario: Administrador técnico gestiona usuarios y roles
- **WHEN** un administrador técnico accede a la gestión de usuarios y roles
- **THEN** el sistema le permite realizar la administración sin alterar el alcance del resto de perfiles
