# runtime-configuration Specification

## Purpose

Establece el comportamiento de configuración que permite ejecutar el sistema en desarrollo y producción con sus bases de datos y límites de almacenamiento correspondientes.

## Requirements

### Requirement: Selección de configuración por entorno
El backend SHALL ofrecer configuraciones de desarrollo y producción seleccionables mediante `DJANGO_SETTINGS_MODULE`, usando SQLite en desarrollo y PostgreSQL en producción.

#### Scenario: Selección de base de datos
- **WHEN** se selecciona la configuración de desarrollo o producción
- **THEN** el backend utiliza SQLite o PostgreSQL, respectivamente

### Requirement: Secretos y modo de depuración de producción
La configuración de producción SHALL obtener `SECRET_KEY` y los datos de conexión a PostgreSQL de variables de entorno y SHALL mantener `DEBUG=False`.

#### Scenario: Ejecución con configuración de producción
- **WHEN** el backend arranca con los ajustes de producción y las variables de entorno configuradas
- **THEN** utiliza esos valores para la clave y la conexión a la base de datos sin habilitar el modo de depuración

### Requirement: Registro rotativo de errores
El backend SHALL registrar errores en archivos con rotación dentro de una ubicación de logs que no se versiona.

#### Scenario: Rotación de archivos de log
- **WHEN** se registran errores hasta alcanzar el límite configurado para un archivo
- **THEN** el registro continúa en un archivo nuevo y los archivos permanecen fuera del control de versiones

### Requirement: Almacenamiento privado de evidencias
La ubicación de almacenamiento de evidencias SHALL ser configurable y estar fuera del contenido servido públicamente.

#### Scenario: Acceso a evidencia almacenada
- **WHEN** una evidencia se guarda en la ubicación configurada
- **THEN** su archivo no queda expuesto como contenido público estático del sitio
