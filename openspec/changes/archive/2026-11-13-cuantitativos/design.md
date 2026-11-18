# Design

## Context

La propuesta y la especificación del cambio se basan en el plan 09 y en las decisiones del repositorio: la funcionalidad debe cubrir los 11 modelos resumen del Manual, tratar solo modelos resumen y `ValorCriterio`, y mantener la relación bidireccional con evidencias de respaldo. El diseño sigue la arquitectura general del proyecto: Django 5.2 + DRF, React 18 + Vite, SQLite en desarrollo y PostgreSQL en producción, con lógica de negocio en servicios y vistas delgadas. Ver [proposal.md](./proposal.md), [specs/cuantitativos/spec.md](./specs/cuantitativos/spec.md), [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L1-L47) y [docs/decisiones/README.md](../../../docs/decisiones/README.md#L27-L45).

## Goals / Non-Goals

**Goals:**
- Registrar y validar los valores de los 11 modelos resumen del Manual por ciclo y curso.
- Permitir el valor propio de criterios cuantitativos sin modelo y mantener la integridad del dato.
- Vincular cada dato cuantitativo con evidencias y listar los datos sin respaldo.
- Reutilizar la validación central de ciclo abierto, permisos `puede(...)` y auditoría `registrar(...)` del resto del sistema.

**Non-Goals:**
- No se implementarán registros nominales ni modelos por profesor o publicación.
- No se importará la base Excel del CTE-CU en este incremento.
- No se calculará automáticamente cumplimiento o categoría a partir de los datos cuantitativos.

## Decisions

### 1) Modelo de datos con tres entidades centrales
Se crearán `ValorModelo`, `ValorCriterio` y `VinculoDato` como entidades del módulo, con consistencia por `(ciclo, campo, curso)` para `ValorModelo` y `(ciclo, criterio)` para `ValorCriterio`, y `VinculoDato` con una sola referencia activa entre dato y evidencia. Esta decisión mantiene la estructura requerida por el plan 09 y evita el modelo nominal que descartó D-05. Alternativa considerada: construir cada dato como registro nominal, que se descarta porque contradice D-05 y la intención de mantener solo resúmenes. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L13-L19), [docs/decisiones/README.md](../../../docs/decisiones/README.md#L31-L45).

### 2) Carga del catálogo de `ModeloCampo` desde los 11 modelos del Manual
El cargador de `ModeloCampo` se construirá desde un fichero de datos en `sistema/datos/` y una orden repetible por claves naturales, siguiendo el mismo patrón del Plan 03 para `cargar_catalogo` y sin introducir nuevas dependencias. La fuente primaria será el Manual de implementación SEA-CU 2025; si una celda no tiene un valor verificable, se dejará como pregunta abierta y no se conjeturará. Fuente: [docs/fuentes/Manual implementación SEA-CU 2025.md](../../../docs/fuentes/Manual%20implementaci%C3%B3n%20SEA-CU%202025.md#L1234-L1409), [docs/origin-plans/03-modulo-estructura.md](../../../docs/origin-plans/03-modulo-estructura.md#L18-L28), [docs/origin-plans/01-modelo-de-datos.md](../../../docs/origin-plans/01-modelo-de-datos.md#L41-L43).

### 3) Reutilización de servicios de ciclo, cuentas y auditoría
Las lecturas y escrituras del módulo cuantitativo deben invocar `puede(...)` en todas las comprobaciones de acceso, mientras que `registrar(...)` solo se ejecutará en operaciones de escritura relevantes: guardar, vincular y desvincular. La validación del ciclo abierto se reutiliza a través de `exigir_ciclo_abierto(...)`, sin duplicar reglas y sin cambiar los requisitos de ciclos, cuentas ni auditoría. Alternativa considerada: validar dentro del servicio de cuantitativos sin depender del resto del sistema; se descarta porque rompe la arquitectura de autorización y trazabilidad del proyecto. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L7-L27), [docs/origin-plans/07-modulo-evidencias.md](../../../docs/origin-plans/07-modulo-evidencias.md#L1-L42), [docs/decisiones/README.md](../../../docs/decisiones/README.md#L73-L96).

### 4) VinculoDato vinculado a Evidencia con ciclo y unicidad estricta
`VinculoDato` apuntará a `Evidencia` (no a `FicheroEvidencia`, D-11), exigirá que el dato y la evidencia compartan el mismo ciclo, impedirá duplicar el par dato–evidencia y forzará que `desvincular` también requiera ciclo abierto. La validación debe hacerse en servicio y en el modelo para evitar cruces entre ciclos y enlaces repetidos. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L13-L19), [docs/origin-plans/01-modelo-de-datos.md](../../../docs/origin-plans/01-modelo-de-datos.md#L41-L61), [docs/decisiones/README.md](../../../docs/decisiones/README.md#L101-L120).

### 5) Enfoque de API y UI por flujos de negocio
La API ofrecerá un conjunto de endpoints de lectura/escritura centrados en valores por modelo, valores por criterio, vínculos y consulta de sin respaldo, mientras que la pantalla React se apoyará en una tabla editable por modelo y una vista de evidencia con selector de vínculos. La lógica se mantiene en servicios, con vistas y componentes delgados. Alternativa considerada: hacer toda la lógica en vistas; se descarta porque el plan 09 insiste en que la lógica esté en servicios y en que el frontend sea compatible con la capa REST del proyecto. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L27-L47).

## Risks / Trade-offs

- [Riesgo: la correspondencia entre los 38 criterios cuantitativos y los modelos del Manual no está cerrada] → Mitigación: resolver la diferencia con el catálogo cargado y la fuente del Manual, sin introducir una capa de mapeo configurable ni suposiciones en código.
- [Riesgo: la base Excel del CTE-CU no está disponible] → Mitigación: diseñar la persistencia con metadatos y cálculo a partir del Manual, evitando suposiciones de formato concreto.
- [Riesgo: la validación de tipos y porcentajes puede complicar la edición de tablas] → Mitigación: centralizar reglas de validación y tests en servicio y UI para que la entrada se rechace de forma consistente en backend y frontend.

## Migration Plan

1. Crear la migración para la base de datos del módulo cuantitativo con `ValorModelo`, `ValorCriterio` y `VinculoDato`.
2. Añadir las restricciones y el CHECK que impide ligar dos tipos distintos al mismo registro de vínculo.
3. Implementar servicios para guardar valores, consultar sin respaldo y gestionar vínculos con evidencia.
4. Exponer la capa API y la pantalla React asociada con validación de UI y pruebas de integración.
5. Ejecutar pruebas solo en SQLite; verificación en PostgreSQL pendiente y documentada (D-14).

## Open Questions

- ¿Cuáles de los 38 criterios cuantitativos no tienen modelo asociado? Debe contrastarse con el catálogo cargado de `ModeloCampo`/`CriterioModelo` (20 criterios con 22 asociaciones) y con la fuente del Manual; no se conjeturan relaciones. Fuente: [docs/fuentes/Manual implementación SEA-CU 2025.md](../../../docs/fuentes/Manual%20implementaci%C3%B3n%20SEA-CU%202025.md#L1234-L1409), [docs/origin-plans/03-modulo-estructura.md](../../../docs/origin-plans/03-modulo-estructura.md#L18-L28), [docs/origin-plans/01-modelo-de-datos.md](../../../docs/origin-plans/01-modelo-de-datos.md#L41-L43).
