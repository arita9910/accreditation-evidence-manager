# evidencias Specification

## Purpose

Definir la gestión documental del ciclo de acreditación, con carga de evidencias, control de permisos, registro de huellas, clasificación por criterio y recuperación segura de documentos.

## ADDED Requirements

### Requirement: Carga y versionado de evidencias
El sistema SHALL permitir registrar evidencias asociadas a un ciclo, con metadatos obligatorios y soporte digital o en papel, manteniendo una versión vigente por evidencia y sin sobrescribir el archivo previo cuando se reemplaza una versión.

#### Scenario: Crear una evidencia con archivo digital
- **WHEN** un usuario autorizado carga una evidencia con su ciclo, tipo, curso académico y soporte digital
- **THEN** el sistema crea la evidencia y el primer archivo asociado con versión 1, sin perder versiones anteriores de la misma evidencia

#### Scenario: Reemplazar una evidencia digital
- **WHEN** un fichero vigente se reemplaza por uno nuevo en la misma evidencia
- **THEN** el sistema conserva la versión anterior como historial y marca la nueva como vigente

#### Scenario: Evidencia en papel sin archivo
- **WHEN** una evidencia se registra como de soporte papel
- **THEN** el sistema exige la custodia original y no admite fichero asociado a esa evidencia

### Requirement: Integridad por huella SHA-256
El sistema SHALL calcular la huella SHA-256 de cada archivo guardado, almacenar la huella en el metadato del archivo y permitir verificar la integridad del contenido sin depender del nombre del fichero.

#### Scenario: Guardar un archivo y verificar su huella
- **WHEN** se guarda un fichero válido en el almacenamiento del módulo
- **THEN** la huella calculada coincide con el contenido del archivo y la comprobación de integridad devuelve un estado correcto

#### Scenario: Detectar un archivo alterado
- **WHEN** el contenido guardado cambia después de su almacenamiento
- **THEN** la verificación de huella detecta la alteración y marca el archivo como incorrecto

### Requirement: Clasificación por criterio y permisos por dimensión
El sistema SHALL permitir clasificar una evidencia por uno o varios criterios del ciclo, sin duplicar la clasificación y resguardando la operación con permisos por dimensión y rol.

#### Scenario: Clasificar una evidencia autorizada
- **WHEN** un usuario con permisos adecuados clasifica una evidencia en un criterio válido del ciclo
- **THEN** la clasificación queda registrada y la evidencia queda vinculada a ese criterio sin duplicados

#### Scenario: Negar clasificación no autorizada
- **WHEN** un integrante intenta clasificar una evidencia en una dimensión o criterio sin permiso
- **THEN** la operación queda denegada y se registra el intento como acceso no autorizado

### Requirement: Búsqueda y descarga controlada
El sistema SHALL permitir buscar evidencias por metadatos y criterios, y SHALL restringir la descarga de archivos a usuarios autorizados y a ciclos abiertos, según la normativa del proyecto.

#### Scenario: Buscar evidencias por texto y filtro
- **WHEN** un usuario consulta evidencias por texto libre o filtros de criterio, ciclo, curso o soporte
- **THEN** el sistema devuelve los resultados compatibles con la búsqueda en metadatos y no indexa archivos completos

#### Scenario: Descargar evidencia con permisos
- **WHEN** un usuario autorizado solicita el archivo vigente de una evidencia
- **THEN** el sistema permite la descarga y registra la acción de auditoría y el acceso

#### Scenario: Denegar descarga sin permiso
- **WHEN** un usuario que no tiene acceso a la evidencia o a la dimensión solicitada intenta descargar el archivo
- **THEN** la descarga queda rechazada y el sistema conserva la trazabilidad del intento

### Requirement: API y pantalla del módulo
La API y la interfaz SHALL exponer las operaciones principales del módulo de evidencias con respuestas coherentes con el resto del sistema, incluyendo listado, creación, clasificación, verificación y descarga.

#### Scenario: Consultar la colección de evidencias
- **WHEN** un cliente autenticado consulta `/api/evidencias/` con filtros y búsqueda
- **THEN** recibe la colección paginada y la información necesaria para crear, clasificar o descargar evidencias

#### Scenario: Usar la pantalla de gestión
- **WHEN** un usuario trabaja en la pantalla de evidencias del ciclo
- **THEN** puede filtrar, cargar, revisar el historial de versiones y ver el estado de integridad de cada archivo
