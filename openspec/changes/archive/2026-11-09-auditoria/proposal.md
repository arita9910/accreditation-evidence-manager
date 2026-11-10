# Proposal

## Why

El proyecto necesita un registro de auditoría de negocio con trazabilidad de quién hizo qué, cuándo y sobre qué entidad, sin depender de librerías automáticas ni de una estructura ad hoc por módulo. El plan 06 define un módulo dedicado con modelo de solo inserción y servicio centralizado, y la integración con ciclos exige sustituir el stub temporal por una implementación real que conserve la firma del servicio ya existente.

## What Changes

- Crear la capacidad de auditoría para registrar acciones de negocio y accesos denegados con trazabilidad de usuario, entidad, fecha, detalle y resultado.
- Implementar la capa de persistencia y servicio centralizado `registrar(...)` con contrato estable para el resto del sistema.
- Reemplazar el stub in-memory del módulo de auditoría por la implementación real sin cambiar la firma que consumen los servicios de ciclos.
- Integrar la auditoría en las operaciones de negocio de `abrir_ciclo`, `cerrar_ciclo` y `asignar_dimension`, manteniendo la lógica del módulo y evitando cambios de comportamiento en sus pruebas.
- Exponer la consulta y el filtrado de registros según permisos del director y del administrador técnico, y reservar la pantalla de consulta cuando el plan lo requiera.

## Capabilities

### New Capabilities
- auditoria: registro, consulta y trazabilidad de acciones de negocio y accesos denegados con permisos y persistencia centralizados.

### Modified Capabilities
- ciclos: la integración con la auditoría real en sus operaciones de apertura, cierre y asignación de dimensiones, sin alterar la firma ni la semántica del flujo de negocio ya probado.

## Impact

- `sistema/backend/auditoria/` para modelo, servicios, serializadores, vistas y pruebas.
- `sistema/backend/ciclos/servicios.py` para la sustitución del stub `registrar(...)` por llamadas reales con la misma firma.
- APIs REST y pantalla de consulta si el plan lo exige para la auditoría de permisos.
- Repositorio y ramas: se mantiene la estrategia de un único repositorio y rama por incremento según D-17, sin introducir dependencias externas nuevas.
