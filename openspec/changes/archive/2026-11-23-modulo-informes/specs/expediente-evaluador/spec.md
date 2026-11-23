# Spec Delta

## Purpose

Permite al par evaluador externo consultar en modo solo lectura el expediente asignado y auditar las consultas y descargas dentro de su vigencia.

## ADDED Requirements

### Requirement: Conceder acceso temporal de par evaluador por ciclo
El sistema SHALL requerir una asignación explícita del par evaluador al ciclo con `vigente_desde` y `vigente_hasta`, y SHALL usar ese intervalo para autorizar consultas y descargas del expediente.

#### Scenario: Asignación vigente
- **WHEN** existe una asignación activa para el par en el ciclo solicitado
- **THEN** el sistema habilita el acceso de lectura y descarga dentro del alcance de ese ciclo

#### Scenario: Asignación fuera de vigencia
- **WHEN** no existe asignación o el acceso ocurre fuera del intervalo vigente
- **THEN** el sistema rechaza el acceso y conserva trazabilidad del rechazo por la política de auditoría de denegados

### Requirement: Consultar el expediente del ciclo asignado
El sistema SHALL entregar al par evaluador el árbol del ciclo con evidencias clasificadas, datos y vínculos únicamente para el ciclo con asignación vigente.

#### Scenario: Par evaluador consulta su ciclo vigente
- **WHEN** un par evaluador con asignación vigente solicita el expediente de su ciclo
- **THEN** el sistema devuelve el árbol del ciclo, evidencias, datos y vínculos en modo de lectura

#### Scenario: Par evaluador intenta consultar otro ciclo
- **WHEN** el par solicita un ciclo distinto al asignado
- **THEN** el sistema rechaza el acceso y registra el intento denegado

### Requirement: Descargar ficheros con alcance vigente
El sistema SHALL permitir la descarga de ficheros del expediente solo al par evaluador asignado mientras la asignación no haya caducado.

#### Scenario: Descarga vigente
- **WHEN** la asignación está vigente y la descarga corresponde al ciclo asignado
- **THEN** el sistema entrega el fichero y registra la consulta

#### Scenario: Asignación caducada
- **WHEN** `vigente_hasta` ya pasó y el par intenta consultar o descargar
- **THEN** el sistema rechaza el acceso y registra el rechazo

#### Scenario: Descarga por endpoint dedicado
- **WHEN** el par evaluador descarga un fichero del expediente desde el endpoint de descarga
- **THEN** el sistema valida vigencia y ámbito del ciclo antes de entregar el archivo

### Requirement: Mantener el expediente como solo lectura
El sistema SHALL impedir cualquier operación de escritura del par evaluador y SHALL no ofrecer acciones de modificación en la interfaz de expediente.

#### Scenario: Par evaluador intenta escribir
- **WHEN** el par evalúa un endpoint de creación, actualización o eliminación
- **THEN** el sistema devuelve 403 y registra el intento según la política de auditoría

#### Scenario: Visualización en React
- **WHEN** el par evaluador abre el expediente
- **THEN** la pantalla reutiliza la vista de lectura y no muestra acciones de escritura

### Requirement: Auditar consultas y descargas del expediente
El sistema SHALL registrar las consultas y descargas realizadas por el par evaluador, incluyendo resultado y ciclo objetivo.

#### Scenario: Consulta exitosa
- **WHEN** el par evaluador obtiene el expediente vigente
- **THEN** se registra la consulta con el usuario, entidad y contexto del ciclo

#### Scenario: Consulta o descarga rechazada
- **WHEN** el acceso falla por asignación inexistente, caducidad o alcance incorrecto
- **THEN** el rechazo queda registrado por el mecanismo central de denegación sin exponer contenido sensible

Fuentes: Plan 12, CU-19 y aceptaciones en `docs/origin-plans/12-modulo-informes.md:13-18` y `docs/origin-plans/12-modulo-informes.md:42-47`; Manual 2025 sobre función y confidencialidad de los pares evaluadores en `docs/fuentes/Manual implementación SEA-CU 2025.md:107-118`.
