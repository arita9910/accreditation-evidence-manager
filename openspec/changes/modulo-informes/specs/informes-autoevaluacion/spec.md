# Spec Delta

## Purpose

Define la composición, generación, versionado y descarga autorizada del informe de autoevaluación como documento editable basado en el expediente del ciclo.

## ADDED Requirements

### Requirement: Editar textos cualitativos del informe
El sistema SHALL permitir guardar textos cualitativos por sección a usuarios autorizados y SHALL rechazar la edición de ciclos cerrados.

#### Scenario: Director guarda caracterización con ciclo abierto
- **WHEN** el director de carrera o miembro autorizado envía contenido para una sección válida
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

Fuentes: Plan 12, objetivo, requisitos y tareas T2-T5 en `docs/origin-plans/12-modulo-informes.md:3-18` y `docs/origin-plans/12-modulo-informes.md:28-42`; Manual 2025 en `docs/fuentes/Manual implementación SEA-CU 2025.md:176-205` y lineas sobre cuantificación en `docs/fuentes/Manual implementación SEA-CU 2025.md:1145-1145`; Resolución No.36/2024 SEA-CU en `docs/fuentes/Resolución No.36-2024 SEA-CU.md:22-27` y `docs/fuentes/Resolución No.36-2024 SEA-CU.md:68-107`.
