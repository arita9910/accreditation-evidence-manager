# Proposal

## Why

El Plan 10 define un módulo de mejora para convertir las debilidades o hallazgos de la valoración y la autoevaluación en acciones de mejora con responsable, plazo y seguimiento, manteniendo un historial de cumplimiento acreditable. El proyecto ya dispone de patrones sólidos para permisos (`puede(...)`), auditoría (`registrar(...)`) y bloqueo de escritura cuando el ciclo está cerrado (`exigir_ciclo_abierto`), pero aún no tiene una capacidad explícita para gestionar el plan de mejora por ciclo ni su relación con el plan del ciclo anterior. La falta de esta capacidad impide cerrar el flujo de evaluación con trazabilidad, evidencia y responsabilidad sobre la corrección de las deficiencias detectadas.

## What Changes

- Se introduce una nueva capacidad de negocio llamada `mejora` para gestionar el plan de mejora del ciclo y su seguimiento.
- Se crean las entidades y reglas de negocio del módulo: `PlanMejora`, `AccionMejora`, `SeguimientoAccion` y `AccionEvidencia`, con origen obligatorio en una debilidad o hallazgo de valoración.
- Se añade la lógica de validación de estados, responsables y plazos para las acciones de mejora, incluyendo cálculo de acciones vencidas y visualización del plan del ciclo anterior.
- Se integra la escritura en el módulo con la validación centralizada del ciclo abierto, la auditoría y los permisos del sistema, sin introducir nuevas dependencias externas.
- Se habilita la API y la capa de presentación requerida para consultar, proponer, aprobar, registrar seguimiento y vincular evidencias a acciones de mejora.

## Capabilities

### New Capabilities

- `mejora`: gestión del plan de mejora del ciclo, la trazabilidad de las acciones y su relación con debilidades, evidencias y plan anterior.

### Modified Capabilities

- Ninguna. El cambio crea una capacidad nueva para cubrir el Plan 10 sin alterar los requisitos de otros módulos ya definidos.

## Impact

- Código y servicios del nuevo módulo `sistema/backend/mejora/` (modelos, servicios, serializadores, vistas, URLs y pruebas).
- Integración con el patrón centralizado de validación del ciclo: `exigir_ciclo_abierto` en `sistema/backend/ciclos/servicios.py`.
- Integración con la auditoría transaccional: `registrar(...)` en `sistema/backend/auditoria/servicios.py`.
- Integración con permisos por carrera y rol: `puede(...)` en `sistema/backend/cuentas/permisos.py`.
- Dependencias del negocio: valoración/autoevaluación, evidencias y la referencia al ciclo anterior.
- API REST bajo `/api/` y vista React asociada para la gestión del plan y del seguimiento.

## Fuentes consultadas

- [docs/origin-plans/10-modulo-mejora.md](../../../docs/origin-plans/10-modulo-mejora.md#L1-L44)
- [sistema/docs/decisiones/04-05-06-decisiones.md](../../../sistema/docs/decisiones/04-05-06-decisiones.md#L1-L18)
- [sistema/backend/ciclos/servicios.py](../../../sistema/backend/ciclos/servicios.py#L52-L60)
- [sistema/backend/auditoria/servicios.py](../../../sistema/backend/auditoria/servicios.py#L22-L41)
- [sistema/backend/cuentas/permisos.py](../../../sistema/backend/cuentas/permisos.py#L204-L260)

## Preguntas abiertas

- ¿Se desea que el módulo de mejora permita también una aprobación automática de la acción por el director cuando se propone desde una debilidad ya validada en la autoevaluación, o debe requerirse siempre una supervisión manual posterior?
- ¿La visualización del plan del ciclo anterior debe limitarse solo a la consulta o debe incluir también comparación con el plan actual en la misma pantalla?

## Resumen (movido desde spec)

La capacidad `mejora` cubre la gestión del plan de mejora del ciclo y su seguimiento hasta la acreditación o la corrección de las deficiencias detectadas por la valoración y la autoevaluación. La intención es que cada acción de mejora nazca de una debilidad identificada, se asigne a un responsable con plazo definido, se registre en la auditoría, se acompañe de evidencias y pueda compararse con el plan del ciclo anterior.

## Fuentes de referencia (movido desde spec)

- [docs/origin-plans/10-modulo-mejora.md](../../../docs/origin-plans/10-modulo-mejora.md#L1-L44)
- [sistema/docs/decisiones/04-05-06-decisiones.md](../../../sistema/docs/decisiones/04-05-06-decisiones.md#L1-L18)
- [sistema/backend/ciclos/servicios.py](../../../sistema/backend/ciclos/servicios.py#L52-L60)
- [sistema/backend/auditoria/servicios.py](../../../sistema/backend/auditoria/servicios.py#L22-L41)
- [sistema/backend/cuentas/permisos.py](../../../sistema/backend/cuentas/permisos.py#L204-L260)

## Preguntas abiertas (movido desde spec)

- ¿Se incorpora el cálculo de acciones vencidas como una simple indicación visual o debe bloquear también la aprobación de nuevas actualizaciones cuando una acción excede el plazo?
- ¿Se considera necesario que el usuario director pueda comparar el plan anterior y el actual en la misma pantalla, o basta con una consulta independiente del plan anterior?
