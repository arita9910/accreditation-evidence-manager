# Design

## Context

El cambio sigue el plan 06 de auditoría y la decisión D-07: auditoría en tabla propia de solo inserción llamada por un servicio, no por historial automático. La intención del módulo es registrar quién hizo qué, cuándo y sobre qué objeto, con permiso de consulta por perfil y con una capa de negocio que no rompa la operación principal. La fuente del plan establece además que la funcionalidad se construye antes de cuentas, en el incremento 1, para que otros módulos puedan registrar desde el principio y que el servicio `registrar(...)` debe conservar el trazado de operaciones de negocio, no solo cambios de filas. (Fuente: docs/origin-plans/06-modulo-auditoria.md:12-29; docs/decisiones/README.md:61-69)

En el código actual, el stub ya existe como `registrar(accion, *, usuario=None, entidad=None, detalle=None, contexto=None, **kwargs)` en `sistema/backend/auditoria/servicios.py` y los servicios del módulo de ciclos lo consumen desde `abrir_ciclo`, `cerrar_ciclo` y `asignar_dimension` con la firma actual y con llamadas del tipo `registrar("abrir_ciclo", usuario=usuario, entidad="Ciclo", detalle={...})`. Eso permite un reemplazo seguro sin alterar la API pública que ya usa el resto del sistema. (Fuente: sistema/backend/auditoria/servicios.py:11-35; sistema/backend/ciclos/servicios.py:4,23-40,57-165)

## Goals / Non-Goals

**Goals:**
- Sustituir el stub de auditoría por la implementación real, conservando la firma pública del servicio `registrar(...)`.
- Registrar las acciones de negocio del módulo de ciclos sin cambiar la lógica de validación ni el comportamiento ya probado por las pruebas actuales.
- Exponer la consulta y el filtrado de auditoría con alcance por permisos, sin introducir dependencias nuevas ni romper la estrategia del repositorio.

**Non-Goals:**
- No se incluye exportación masiva ni alertas; el plan 06 los deja fuera de alcance.
- No se reforma la lógica de negocio de ciclos ni se cambia la firma pública de `abrir_ciclo`, `cerrar_ciclo` o `asignar_dimension`.
- No se añaden dependencias externas ni cambios de arquitectura por fuera de la app `auditoria` y la integración con ciclos.

## Decisions

### 1. Mantener un modelo de auditoría propio, no un historial automático
La solución usará una tabla propia de solo inserción para el registro de actividad. Esto cumple el requisito de seguridad y evita que un módulo externo reescriba el historial sin control. El plan 06 deja claro que la auditoría debe ser una tabla dedicada y el servicio `registrar` debe llamarla; la decisión se alinea además con la estrategia de la aplicación y con la regla de no depender de librerías de historial automatizadas. (Fuente: docs/origin-plans/06-modulo-auditoria.md:12-29; docs/decisiones/README.md:61-69)

### 2. Conservar la firma del stub `registrar(...)` para la integración con ciclos
La forma actual del stub en `auditoria.servicios.registrar` ya se usa desde `ciclos/servicios.py` y debe mantenerse durante la migración a la implementación real. Eso implica conservar el nombre del servicio, los argumentos opcionales y el comportamiento de aceptación del actor, la entidad y el detalle, para que `abrir_ciclo`, `cerrar_ciclo` y `asignar_dimension` no necesiten cambios de firma ni de llamadas desde las pruebas del plan 04. (Fuente: sistema/backend/auditoria/servicios.py:11-35; sistema/backend/ciclos/servicios.py:57-170)

### 3. El servicio será el punto de integración y no un cambio directo en los modelos de ciclos
La auditoría debe registrarse en la capa de servicios, no en los modelos, para evitar acoplar el modelo del dominio con la trazabilidad de negocio y para mantener una sola ruta centralizada de escritura. Esta opción reduce acoplamiento y coincide con la directriz del plan 06: "los demás módulos llaman a este servicio; registra acciones de negocio, no solo cambios de filas". (Fuente: docs/origin-plans/06-modulo-auditoria.md:24-27)

### 4. La consulta se hará por permisos y alcance, no por acceso global
El plan 06 limita la consulta para que el director vea la auditoría de su carrera y el administrador técnico vea todo. Este criterio se mantiene en la API de consulta y, si se desarrolla la pantalla, en el frontend para no exponer información ajena a la organización. (Fuente: docs/origin-plans/06-modulo-auditoria.md:31-35)

### 5. No introducir dependencias ni ampliaciones ajenas al alcance
El repositorio mantiene un único repositorio con rama por incremento y el cambio no añade paquetes ni dependencias nuevas. La versión de reemplazo de archivos también queda bajo una estrategia de control de versiones y se evita cualquier dependencia extra para no diluir el alcance del módulo. (Fuente: docs/decisiones/README.md:97-116; docs/decisiones/README.md:151-167)

## Risks / Trade-offs

- [Riesgo] Reemplazar el stub sin conservar la firma de la API podría romper las llamadas de ciclos y forzar cambios de pruebas. → Mitigación: mantener la firma `registrar(accion, *, usuario=None, entidad=None, detalle=None, contexto=None, **kwargs)` intacta y validar la compatibilidad con las llamadas actuales de `ciclos/servicios.py`.
- [Riesgo] Si la auditoría se registra en una transacción distinta de la operación principal, puede quedar trazabilidad inconsistente. → Mitigación: diseñar la escritura en la misma transacción del flujo principal o documentar explícitamente el consenso del equipo para un comportamiento no transaccional.
- [Riesgo] La consulta de auditoría puede filtrar demasiado o insuficiente si no se modela el alcance por carrera. → Mitigación: aplicar los permisos del director y administrador técnico en la capa de servicio y en la API de consulta.

## Migration Plan

1. Crear el modelo y la migración de la app `auditoria`, manteniendo la inmutabilidad y la restricción de borrado y actualización de registros.
2. Implementar `registrar(...)` como la única infraestructura de escritura, con campos de usuario, entidad, detalle, resultado y contexto, y mantener su firma pública.
3. Reemplazar el stub en `ciclos/servicios.py` por el servicio real, manteniendo las llamadas actuales en `abrir_ciclo`, `cerrar_ciclo` y `asignar_dimension`.
4. Añadir la API de consulta con filtros y permisos, y si el plan lo exige, la pantalla de consulta con paginación y filtros.
5. Ejecutar pruebas del módulo de ciclos y de auditoría para comprobar que el comportamiento existente sigue intacto.

## Open Questions

- ¿Debe la operación de negocio y el registro de auditoría estar en la misma transacción para garantizar que no haya “éxito sin rastro”? El plan 06 la sugiere como propuesta, pero la decisión final debe confirmarse antes de cerrar la implementación. (Fuente: docs/origin-plans/06-modulo-auditoria.md:24-27)
- ¿Se usará una vista de consulta por carrera para director o la validación de permisos se realizará directamente en la capa de servicio y en la API? La respuesta afecta a la forma de testear los accesos y puede dejar la decisión del alcance a la implementación final. (Fuente: docs/origin-plans/06-modulo-auditoria.md:31-35)
