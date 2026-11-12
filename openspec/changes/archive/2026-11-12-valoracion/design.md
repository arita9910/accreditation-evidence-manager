# Design

## Context

La propuesta se apoya directamente en el plan 08 del módulo de valoración y en la lógica ya existente del proyecto para ciclos, evidencias y auditoría. El módulo no debe crear una capa nueva de permisos ni de validación; debe reutilizar `exigir_ciclo_abierto(...)`, `puede(...)` y `registrar(...)` como puntos de control de negocio. Fuente: [docs/origin-plans/08-modulo-valoracion.md](../../docs/origin-plans/08-modulo-valoracion.md#L3-L38), [docs/origin-plans/07-modulo-evidencias.md](../../docs/origin-plans/07-modulo-evidencias.md#L3-L57), [sistema/backend/ciclos/servicios.py](../../../sistema/backend/ciclos/servicios.py#L52-L58), [sistema/backend/cuentas/permisos.py](../../../sistema/backend/cuentas/permisos.py#L201-L230), [sistema/backend/auditoria/servicios.py](../../../sistema/backend/auditoria/servicios.py#L22-L45).

## Goals / Non-Goals

**Goals:**
- Crear la entidad y la lógica de servicio para gestionar valoraciones cualitativas del ciclo.
- Vincular cada valoración con criterios y evidencias del mismo ciclo, respetando la dimensión de origen.
- Reutilizar la seguridad y auditoría ya implantadas en el sistema.
- Exponer la API y la interfaz mínima necesaria para que el flujo miembro → valoración → debilidad quede operativo.

**Non-Goals:**
- Redacción de textos de informe externos al módulo de valoración.
- Cálculo automático de categorías o juicios finales del informe.
- Modificar la lógica de acciones de mejora o del plan 10; la validación de eliminación solo evita la incoherencia con dependencias existentes.

## Decisions

### D1. Reutilizar la validación central de ciclo abierto
Se aplicará `exigir_ciclo_abierto(ciclo)` en cada creación, edición y eliminación de valoraciones. Esa decisión sigue la convención del resto de módulos del backend y evita que la valoración cree rutas de escritura independientes que ignoren el estado del ciclo. Fuente: [sistema/backend/ciclos/servicios.py](../../../sistema/backend/ciclos/servicios.py#L52-L58).

### D2. No introducir permisos ad hoc
Los permisos se evaluarán con `puede(...)` y con el contexto de carrera/dimensión del objeto. Esto mantiene la misma semántica de roles, alcance y acceso que ya usan los módulos de cuentas, evidencias y auditoría. Fuente: [sistema/backend/cuentas/permisos.py](../../../sistema/backend/cuentas/permisos.py#L181-L230).

### D3. Registrar cada alta y cambio en auditoría
Cada escritura relevante del módulo se registrará con `registrar(...)`, con usuario, entidad y detalle del cambio. El proyecto ya usa esta convención para mantener trazabilidad sin introducir una segunda tabla o sistema de auditoría paralelo. Fuente: [sistema/backend/auditoria/servicios.py](../../../sistema/backend/auditoria/servicios.py#L22-L45), [docs/decisiones/README.md](../../docs/decisiones/README.md#L61-L68).

### D4. Vincular valoración a criterios y evidencias del catálogo / ciclo
La valoración se registrará únicamente con criterios que pertenezcan a la dimensión y con evidencias ya asociadas al mismo ciclo. Esa decisión está alineada con plan 08 y con la responsabilidad del plan 07 sobre la clasificación y la verificación de evidencias. Fuente: [docs/origin-plans/08-modulo-valoracion.md](../../docs/origin-plans/08-modulo-valoracion.md#L15-L38), [docs/origin-plans/07-modulo-evidencias.md](../../docs/origin-plans/07-modulo-evidencias.md#L15-L57).

### D5. Mantener el formateo de porcentaje como utilidad reutilizable
La salida `86,2 % (19/23)` se define como utilidad de servicio para que otros módulos, por ejemplo el plan 12, puedan reutilizar la misma convención. La decisión no añade lógica de cálculo ni categorías automáticas; solo formaliza el texto que se presenta. Fuente: [docs/origin-plans/08-modulo-valoracion.md](../../docs/origin-plans/08-modulo-valoracion.md#L23-L27).

## Risks / Trade-offs

- [Riesgo] La validación cruzada entre criterio, dimensión y ciclo puede producir errores de integración si el catálogo de criterios cambió en tiempo de ejecución → Mitigación: validar en servicio y en API antes de persistir, con pruebas de frontera para criterios fuera de dimensión y evidencia de otro ciclo.
- [Riesgo] El formateo de porcentajes puede divergir entre módulos si se repite una regla distinta → Mitigación: centralizar la utilidad `formatear_porcentaje(...)` y reutilizarla desde la API y la pantalla.
- [Riesgo] El módulo puede depender implícitamente de la semántica del plan 07 si la clasificación de evidencias no está bien alimentada → Mitigación: aceptar solo evidencias ya clasificadas dentro del ciclo y documentar la dependencia explícita en el contrato del servicio.

## Migration Plan

1. Crear modelo de valoraciones y tablas de unión para criterios y evidencias.
2. Añadir servicio de validación y formateo con pruebas unitarias.
3. Exponer API con permisos, auditoría y restricciones de ciclo.
4. Añadir la pantalla React para la edición por dimensión.
5. Ejecutar pruebas del flujo completo en SQLite; documentar cualquier caso pendiente para PostgreSQL como parte del despliegue de producción.

## Open Questions

- [Pregunta abierta] Si el catálogo de criterios o de evidencias se actualiza durante el ciclo, ¿la valoración debe vincularse siempre a la versión viva del catálogo del ciclo o a una instantánea fijada al abrir el ciclo? Esta decisión no cambia la especificación del módulo, pero sí la política de validación funcional que debe aplicarse en la capa de servicio.

Fuentes de referencia: [docs/origin-plans/08-modulo-valoracion.md](../../docs/origin-plans/08-modulo-valoracion.md#L3-L38), [docs/decisiones/README.md](../../docs/decisiones/README.md#L16-L20), [docs/decisiones/README.md](../../docs/decisiones/README.md#L25-L43).
