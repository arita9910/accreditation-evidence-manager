# Proposal

## Why

El módulo de valoración debe capturar la opinión cualitativa de la comisión por dimensión, asociando fortalezas y debilidades a criterios y evidencias del ciclo, sin duplicar la lógica de permisos, auditoría o control del ciclo que ya existe en el proyecto. El plan 08 define esta necesidad y la integra con el módulo de evidencias y con el catálogo de criterios del sistema; la implementación debe respetar esa base, no crear otra forma paralela de autorización ni de trazabilidad. Fuente: [docs/origin-plans/08-modulo-valoracion.md](../../docs/origin-plans/08-modulo-valoracion.md#L1-L38), [docs/origin-plans/07-modulo-evidencias.md](../../docs/origin-plans/07-modulo-evidencias.md#L1-L57), [docs/decisiones/README.md](../../docs/decisiones/README.md#L16-L20).

## What Changes

- Añadir la capacidad de registrar valoraciones cualitativas por dimensión con tipo fortaleza/debilidad, texto, criterios y evidencias vinculadas.
- Reforzar la validación de negocio para que cada valoración solo use criterios de su dimensión y evidencias del ciclo abierto.
- Integrar el control de permisos y de auditoría con las utilidades del sistema ya implementadas en `puede(...)` y `registrar(...)`.
- Exponer la API y la pantalla de gestión para crear, listar, editar y eliminar valoraciones según los permisos del plan.
- Mantener la salida de porcentajes con formato estable para que el módulo de informes pueda reutilizar la misma convención.

## Capabilities

### New Capabilities
- valoracion: gestión de valoraciones cualitativas del ciclo, con control por dimensión, criterios y evidencias, y formato de porcentajes reutilizable.

### Modified Capabilities
- No hay capacidades existentes cuya especificación requiera modificación en esta propuesta; el cambio introduce una nueva capacidad del sistema. Fuente: [docs/origin-plans/08-modulo-valoracion.md](../../docs/origin-plans/08-modulo-valoracion.md#L15-L38).

## Impact

- Módulos afectados: `sistema/backend/valoracion/` (nueva app), `sistema/backend/ciclos/servicios.py`, `sistema/backend/cuentas/permisos.py` y `sistema/backend/auditoria/servicios.py`.
- API: endpoints bajo `/api/` para listar, crear y modificar valoraciones y su relación con criterios/evidencias del ciclo.
- UI: editor de fortalezas y debilidades por dimensión en React con selector de criterios y evidencias, según el plan 08.
- Dependencias: debe reutilizar la estructura del catálogo de criterios y de evidencia ya definida en los planes 07 y 01; no se introducen dependencias nuevas. Fuente: [docs/origin-plans/08-modulo-valoracion.md](../../docs/origin-plans/08-modulo-valoracion.md#L15-L38), [sistema/backend/ciclos/servicios.py](../../../sistema/backend/ciclos/servicios.py#L52-L58), [sistema/backend/cuentas/permisos.py](../../../sistema/backend/cuentas/permisos.py#L201-L230), [sistema/backend/auditoria/servicios.py](../../../sistema/backend/auditoria/servicios.py#L22-L45).
