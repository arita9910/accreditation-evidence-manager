# informes-autoevaluacion Specification

## Purpose

Define la composición, generación, versionado y descarga autorizada del informe de autoevaluación como documento editable basado en el expediente del ciclo.

## Requirements

### Requirement: Editar textos cualitativos del informe
El sistema SHALL permitir guardar textos cualitativos por sección a usuarios autorizados y SHALL rechazar la edición de ciclos cerrados.

#### Scenario: Director guarda caracterización con ciclo abierto
- **WHEN** un usuario con rol implementado y autorizado envía contenido para una sección válida
- **THEN** el sistema exige que el ciclo esté abierto y persiste el texto asociado al usuario editor

#### Scenario: Se intenta editar un ciclo cerrado
- **WHEN** una operación de edición recibe un ciclo que no está abierto
- **THEN** el sistema rechaza la operación y no modifica el contenido

### Requirement: Componer el informe obligatorio
El sistema SHALL componer el informe con portada y datos del ciclo, caracterización, fortalezas y debilidades por dimensión, plan de mejora, sostenibilidad del claustro y los modelos anexos con datos del ciclo.

#### Scenario: Generar informe completo
- **WHEN** se genera el informe de un ciclo con datos disponibles
- **THEN** el documento incluye las secciones obligatorias y datos referenciados a criterios y evidencias

#### Scenario: Reacreditación con ciclo anterior
- **WHEN** existe un plan valorado del ciclo anterior
- **THEN** el informe incluye las mejoras alcanzadas respecto a ese proceso anterior

### Requirement: Exportar un DOCX editable conforme al formato
El sistema SHALL exportar el informe como archivo DOCX editable con Arial 12, interlineado sencillo y porcentajes acompañados de su relación de origen.

#### Scenario: Documento generado con formato base
- **WHEN** se inspecciona el cuerpo del DOCX generado
- **THEN** el texto usa Arial 12 e interlineado sencillo y las tablas permanecen legibles

#### Scenario: Porcentaje cuantitativo
- **WHEN** el informe incluye un porcentaje
- **THEN** se muestra su relación de origen reutilizando el formato común de valoraciones

### Requirement: Crear versiones trazables del informe
El sistema SHALL crear versiones numeradas sin bloquear por advertencias de completitud, SHALL registrar el archivo y su huella SHA-256 y SHALL declarar el método de conteo de páginas.

#### Scenario: Primera generación en ciclo sin LibreOffice
- **WHEN** el usuario genera una versión y LibreOffice no está disponible
- **THEN** el sistema usa estimación por caracteres, declara `metodo_conteo=estimado` y conserva la versión

#### Scenario: Informe que supera 50 páginas sin anexos
- **WHEN** el conteo determina más de 50 páginas sin anexos
- **THEN** el sistema conserva el documento y añade una advertencia visible sin bloquear la generación

### Requirement: Descargar versiones según el rol autorizado
El sistema SHALL autorizar la descarga de versiones con una decisión centralizada de permisos y SHALL mostrar versiones a los perfiles definidos por el plan.

#### Scenario: Director genera y descarga
- **WHEN** un director autorizado solicita generar o descargar una versión de su ciclo
- **THEN** el sistema autoriza la operación sobre el ciclo correspondiente

#### Scenario: Usuario no autorizado intenta descargar
- **WHEN** un usuario sin rol o ámbito autorizado solicita una versión
- **THEN** el sistema deniega la operación y registra el intento

#### Scenario: Regla provisional de versión final para par evaluador
- **WHEN** el sistema evalúa qué versión puede descargar el par evaluador
- **THEN** considera provisionalmente como final la versión con mayor `numero` del ciclo hasta que exista una marca explícita

### Requirement: Presentar avisos de completitud en lista simple
La interfaz SHALL mostrar los avisos en formato clave-valor directo y SHALL listar los elementos de cada arreglo separados por comas o por saltos de línea, sin badges ni textos de truncamiento como "... y X más".

#### Scenario: Generación con muchos avisos
- **WHEN** la pantalla de generación recibe listas extensas de avisos
- **THEN** muestra la lista completa en formato simple por clave, sin ocultar elementos ni resumir cantidades

#### Scenario: Consulta de completitud
- **WHEN** la pantalla de análisis muestra avisos de completitud
- **THEN** aplica el mismo formato de lista simple por clave y conserva el contenido completo de cada arreglo

#### Scenario: Exclusión de modelos incompletos
- **WHEN** la respuesta de completitud contiene `modelos_incompletos`
- **THEN** las pantallas de generación y análisis no renderizan esa clave ni su lista
