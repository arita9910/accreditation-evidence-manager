# Proposal

## Why

El módulo cuantitativo de la acreditación necesita registrar los 11 modelos resumen del Manual y los valores propios de los criterios cuantitativos sin modelo, además de vincular cada dato con sus evidencias de respaldo en ambos sentidos. El plan 09 y las decisiones D-04 y D-05 establecen que la estructura debe mantenerse como celdas genéricas por modelo y que los datos cuantitativos solo se registran en modelos resumen o en `ValorCriterio`, sin registros nominales. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L1-L47), [docs/decisiones/README.md](../../../docs/decisiones/README.md#L33-L45).

## What Changes

- Se introduce el módulo de datos cuantitativos para persistir `ValorModelo`, `ValorCriterio` y `VinculoDato` con validación de integridad y restricciones de negocio.
- Se define la lógica de escritura para modelos resumen y criterios cuantitativos sin modelo, con validación por tipo de campo, no negativos, porcentajes y copia de acreditación anterior cuando aplica.
- Se añade la consulta y el análisis de registros sin respaldo, así como la relación bidireccional dato–evidencia para cumplir la trazabilidad de evidencias.
- Se integra la autorización y la auditoría del sistema en cada operación de escritura y consulta, incluyendo la regla de exigir ciclo abierto y la comprobación de permisos por `puede(...)` y `registrar(...)`.
- Se prepara la capa API y la pantalla React para registrar, consultar y visualizar los datos cuantitativos y los enlaces a evidencias.

## Capabilities

### New Capabilities
- `cuantitativos`: gestión de datos cuantitativos del ciclo, vinculación con evidencias, validación por modelo y consulta de elementos sin respaldo.

### Modified Capabilities
- `ciclos`: se reutiliza la validación centralizada `exigir_ciclo_abierto(...)` como requisito previo a las escrituras del módulo cuantitativo. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L7-L27), [docs/origin-plans/04-modulo-ciclos.md](../../../docs/origin-plans/04-modulo-ciclos.md#L1-L80).
- `cuentas`: se ajusta la autorización de operaciones del módulo cuantitativo a la política centralizada `puede(...)` para miembros y directores. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L7-L27).
- `auditoria`: cada operación relevante del módulo cuantitativo debe registrarse con `registrar(...)` para conservar trazabilidad de negocio. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L7-L27), [docs/decisiones/README.md](../../../docs/decisiones/README.md#L73-L96).

## Impact

- Backend: nuevo submódulo `sistema/backend/cuantitativos/` con modelos, servicios, serializadores, vistas y URLs para datos cuantitativos.
- Base de datos: migraciones para `ValorModelo`, `ValorCriterio`, `VinculoDato` y validaciones de integridad según el plan 09 y los modelos resumen del Manual.
- API: endpoints `GET/PUT` de valores por modelo y criterio, vínculos entre datos y evidencias, y listado de datos sin respaldo.
- Frontend: pantallas React para captura de tablas por modelo, edición de valores por criterio y visualización de evidencias enlazadas.
- Dependencias cercanas: ciclos abiertos, permisos de cuentas, auditoría y evidencias, sin introducir nuevas dependencias externas ni registros nominales.
