# Design

## Context

La propuesta de cambio se apoya en el plan del ciclo de mejora descrito en [docs/origin-plans/10-modulo-mejora.md](../../../docs/origin-plans/10-modulo-mejora.md#L1-L44), donde se establece que el módulo debe gestionar un plan de mejora basado en debilidades, con responsable, plazo, seguimiento, acciones vencidas y comparación con el plan del ciclo anterior. El diseño debe respetar la arquitectura ya definida por el proyecto: servicios con lógica centralizada, vistas delgadas, permisos a través de `puede(...)`, auditoría centralizada con `registrar(...)`, y validación de ciclo abierto con `exigir_ciclo_abierto`.

Los fundamentos de esa integración ya se documentan en [sistema/docs/decisiones/04-05-06-decisiones.md](../../../sistema/docs/decisiones/04-05-06-decisiones.md#L1-L18) y se ejecutan en [sistema/backend/ciclos/servicios.py](../../../sistema/backend/ciclos/servicios.py#L52-L60), [sistema/backend/auditoria/servicios.py](../../../sistema/backend/auditoria/servicios.py#L22-L41) y [sistema/backend/cuentas/permisos.py](../../../sistema/backend/cuentas/permisos.py#L204-L260).

## Goals / Non-Goals

**Goals:**
- Unificar la gestión del plan de mejora dentro del ciclo actual.
- Forzar la relación obligatoria entre una acción y una debilidad/ hallazgo de valoración.
- Registrar el historial de seguimiento, la aprobación, la evidencia y la ventana de cumplimiento.
- Exponer la consulta del plan anterior para cerrar el ciclo de mejora y la explicación de resultados.

**Non-Goals:**
- No se incluirán notificaciones por correo ni automatizaciones externas de seguimiento.
- No se desarrollará una planificación de Gantt ni un cálculo de impacto económico o académico de cada acción.
- No se añadirá ninguna dependencia nueva ni se redefinirá la capa de permisos o de auditoría; se reutilizarán los servicios ya existentes.

## Decisions

### 1. Reusar servicios centrales en lugar de duplicar lógica

La decisión principal es mantener el módulo de mejora acoplado a la validación centralizada del proyecto: `exigir_ciclo_abierto` definirá la regla de negocio para escribir sobre ciclos cerrados; `puede(...)` decidirá permisos; y `registrar(...)` registrará las operaciones relevantes. Esto evita duplicar reglas y mantiene la coherencia con los módulos ya implementados en ciclos, valoración y auditoría.

**Alternativa considerada:** duplicar validaciones en `mejora/servicios.py`.
**Por qué no:** esto rompería la convención del proyecto y dificultaría el mantenimiento en futuros módulos; además, la decisión ya está establecida por los planes 04, 05 y 06.

### 2. Modelo de origen de la acción: debilidad obligatoria

Cada `AccionMejora` tendrá una referencia explícita a una `debilidad` o hallazgo de valoración. Esta restricción se incluirá en el modelo y en la capa de servicios para evitar acciones genéricas o no trazables.

**Alternativa considerada:** un estado de acción libre sin origen.
**Por qué no:** contradice el objetivo del plan y la directriz del plan 10: las mejoras deben vincularse a hallazgos y no a acciones aisladas.

### 3. Separación entre plan, acción, seguimiento y evidencia

Se estructurará la información en cuatro entidades acopladas por relaciones de negocio: `PlanMejora`, `AccionMejora`, `SeguimientoAccion` y `AccionEvidencia`. La separación permite conservar la trazabilidad del estado de cada acción y la evidencia acumulada sin mezclar responsabilidades.

**Alternativa considerada:** guardar todo en una sola entidad o en un JSON de contenido libre.
**Por qué no:** reduce la trazabilidad y complica la consulta por progreso, responsable y cumplimiento.

### 4. Consulta del plan anterior como una vista complementaria

La API y la pantalla deberán exponer un endpoint o vista para consultar el `plan_ciclo_anterior` junto con el plan actual. La comparación podrá realizarse como lectura separada o en una visión combinada, sin que ello implique cambios en el modelo del ciclo.

**Alternativa considerada:** ocultar completamente el plan anterior.
**Por qué no:** el plan 10 explícitamente requiere valorar la resolución del plan del ciclo anterior para cerrar el ciclo actual con contexto histórico.

## Risks / Trade-offs

- [Riesgo de acoplamiento a la lógica de permisos] → Mitigación: reutilizar `puede(...)` y no crear permisos ad hoc; documentar los permisos por acción en la capa de servicios y las vistas.
- [Riesgo de inconsistencias entre estados y transiciones] → Mitigación: centralizar la validación de estados en servicios y reforzar pruebas de transición no permitida.
- [Riesgo de falta de evidencias] → Mitigación: obligar la vinculación de evidencias a la acción y validar que el usuario responsable o el director pueda registrar evidencia antes de cerrar la acción como cumplida.
- [Riesgo de carga de la vista de comparación de planes] → Mitigación: mantener el plan anterior como lectura optimizada y separada; evitar lógica de negocio pesada en la capa de presentación.

## Migration Plan

1. Crear el módulo `sistema/backend/mejora/` con modelos y servicios base, manteniendo la estructura por capas del proyecto.
2. Alinear las entidades con la lógica centralizada de ciclo abierto, permisos y auditoría ya existente.
3. Añadir las pruebas de negocio para validación de origen, transiciones e integración con auditoría.
4. Exponer la API REST y el flujo de pantalla para crear, aprobar y registrar seguimiento.
5. Validar la consulta del plan del ciclo anterior junto con el plan actual y dejar la documentación de avance en `docs/avance/10-mejora.md`.

## Open Questions

- ¿El cierre de una acción como `cumplida` debe requerir siempre evidencia asociada, o se acepta la finalización sin evidencia cuando el responsable deja constancia del resultado en el seguimiento?
- ¿La comparación del plan anterior y el actual debe ser una vista única o dos consultas separadas que luego se combinan en la interfaz?

## Fuentes consultadas

- [docs/origin-plans/10-modulo-mejora.md](../../../docs/origin-plans/10-modulo-mejora.md#L1-L44)
- [sistema/docs/decisiones/04-05-06-decisiones.md](../../../sistema/docs/decisiones/04-05-06-decisiones.md#L1-L18)
- [sistema/backend/ciclos/servicios.py](../../../sistema/backend/ciclos/servicios.py#L52-L60)
- [sistema/backend/auditoria/servicios.py](../../../sistema/backend/auditoria/servicios.py#L22-L41)
- [sistema/backend/cuentas/permisos.py](../../../sistema/backend/cuentas/permisos.py#L204-L260)
