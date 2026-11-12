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

### 2) Celdas genéricas por modelo y definición por datos
La estructura del modelo se almacenará como metadatos y definiciones de columnas, y el backend cargará los 11 modelos resumidos a partir de datos en vez de codificar una tabla por modelo. Esto sigue D-04 y evita que el código dependa de una plantilla Excel concreta aún no disponible. Alternativa considerada: una tabla independiente por cada modelo; se descarta porque exige cambiar código al variar la definición de los modelos. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L13-L15), [docs/decisiones/README.md](../../../docs/decisiones/README.md#L18-L30).

### 3) Reutilización de servicios de ciclo, cuentas y auditoría
Las escrituras del módulo cuantitativo deben invocar `exigir_ciclo_abierto(...)`, `puede(...)` y `registrar(...)` en vez de duplicar validaciones locales. Esto refuerza la consistencia con los otros módulos y evita divergencias de negocio. Alternativa considerada: validar dentro del servicio de cuantitativos sin depender del resto del sistema; se descarta porque rompe la arquitectura de autorización y trazabilidad del proyecto. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L7-L27), [docs/origin-plans/07-modulo-evidencias.md](../../../docs/origin-plans/07-modulo-evidencias.md#L1-L42).

### 4) Enfoque de API y UI por flujos de negocio
La API ofrecerá un conjunto de endpoints de lectura/escritura centrados en valores por modelo, valores por criterio, vínculos y consulta de sin respaldo, mientras que la pantalla React se apoyará en una tabla editable por modelo y una vista de evidencia con selector de vínculos. La lógica se mantiene en servicios, con vistas y componentes delgados. Alternativa considerada: hacer toda la lógica en vistas; se descarta porque el plan 09 insiste en que la lógica esté en servicios y en que el frontend sea compatible con la capa REST del proyecto. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L27-L47).

## Risks / Trade-offs

- [Riesgo: los 11 modelos resumen y la correspondencia criterio–modelo pueden cambiar en validación comisionada] → Mitigación: dejar la estructura de celdas como datos y mantener una capa de mapeo configurable; la decisión de código se aplaza a la validación normativa y no a la implementación del módulo.
- [Riesgo: la base Excel del CTE-CU no está disponible] → Mitigación: diseñar la persistencia con metadatos y cálculo a partir del Manual, evitando suposiciones de formato concreto.
- [Riesgo: la validación de tipos y porcentajes puede complicar la edición de tablas] → Mitigación: centralizar reglas de validación y tests en servicio y UI para que la entrada se rechace de forma consistente en backend y frontend.

## Migration Plan

1. Crear la migración para la base de datos del módulo cuantitativo con `ValorModelo`, `ValorCriterio` y `VinculoDato`.
2. Añadir las restricciones y el CHECK que impide ligar dos tipos distintos al mismo registro de vínculo.
3. Implementar servicios para guardar valores, consultar sin respaldo y gestionar vínculos con evidencia.
4. Exponer la capa API y la pantalla React asociada con validación de UI y pruebas de integración.
5. Ejecutar pruebas en SQLite y validar la compatibilidad con PostgreSQL mediante la misma lógica de negocio y migraciones portables.

## Open Questions

- La correspondencia exacta entre los 38 criterios cuantitativos y los 18 criterios con modelo debe validarse con la comisión, porque el plan 09 la considera una propuesta pendiente. Esto no bloquea la estructura general del módulo, pero sí condiciona el catálogo definitivo de mapeos y la carga inicial de metadatos. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L13-L16).
