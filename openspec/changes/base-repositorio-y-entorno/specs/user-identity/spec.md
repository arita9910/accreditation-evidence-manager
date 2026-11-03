# Spec Delta

## Purpose

Proporciona una identidad de usuario propia para el sistema, lista desde la primera migración y sin incorporar todavía los flujos de autenticación ni la gestión de permisos.

## ADDED Requirements

### Requirement: Identidad de usuario propia
El sistema SHALL disponer de un modelo propio de usuario con los campos `username`, `nombre`, `apellidos`, `email` y `activo`, y SHALL almacenar las contraseñas mediante mecanismos seguros.

#### Scenario: Crear una cuenta administrativa inicial
- **WHEN** se crea el superusuario inicial con el comando de administración de Django
- **THEN** el registro usa el modelo propio del sistema y la contraseña no se almacena en texto claro

### Requirement: Modelo de usuario en la migración inicial
La primera migración de la base de datos SHALL incluir el modelo propio configurado como modelo de usuario del sistema.

#### Scenario: Inicializar la base de datos desde cero
- **WHEN** se generan las migraciones iniciales en una instalación limpia
- **THEN** el modelo propio de usuario forma parte de la migración inicial y está disponible antes de migrar las demás apps
