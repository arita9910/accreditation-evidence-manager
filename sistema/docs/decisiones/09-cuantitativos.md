# Decisiones 09 — Módulo cuantitativo

## D-09.01 — Catalogar `ModeloCampo` desde el Manual

La carga de `ModeloCampo` debe basarse en un fichero de datos del proyecto y un cargador repetible por claves naturales, siguiendo la misma convención del Plan 03. La estructura del Manual se usa como fuente primaria; si una celda no tiene valor verificable, queda como pregunta abierta por no conjeturar. Fuente: [docs/fuentes/Manual implementación SEA-CU 2025.md](../../../docs/fuentes/Manual%20implementaci%C3%B3n%20SEA-CU%202025.md#L1234-L1409), [docs/origin-plans/03-modulo-estructura.md](../../../docs/origin-plans/03-modulo-estructura.md#L18-L28), [docs/origin-plans/01-modelo-de-datos.md](../../../docs/origin-plans/01-modelo-de-datos.md#L41-L43).

## D-09.02 — Permisos y auditoría por servicio

`puede(...)` se usa en lecturas y escrituras; `registrar(...)` solo en escrituras relevantes (guardar, vincular, desvincular). La validación de ciclo abierto sigue centralizada en el servicio de ciclos y no se duplica en el módulo cuantitativo. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L7-L27), [docs/decisiones/README.md](../../../docs/decisiones/README.md#L73-L96).

## D-09.03 — `VinculoDato` con vínculo a evidencia y ciclo

`VinculoDato` apunta a `Evidencia` y no a `FicheroEvidencia` (D-11); exige mismo ciclo entre dato y evidencia, impide duplicar el par dato–evidencia y exige ciclo abierto también al desvincular. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L13-L19), [docs/origin-plans/01-modelo-de-datos.md](../../../docs/origin-plans/01-modelo-de-datos.md#L41-L61).

## D-09.04 — Pregunta abierta sobre criterios sin modelo

La decisión pendiente es determinar qué criterios de los 38 cuantitativos no tienen modelo asociado y contrastarlo con el catálogo cargado (`20 criterios con 22 asociaciones CriterioModelo`). La resolución debe basarse en la fuente y en la línea del Manual y no en suposiciones de implementación. Fuente: [docs/fuentes/Manual implementación SEA-CU 2025.md](../../../docs/fuentes/Manual%20implementaci%C3%B3n%20SEA-CU%202025.md#L1234-L1409), [docs/origin-plans/03-modulo-estructura.md](../../../docs/origin-plans/03-modulo-estructura.md#L18-L28), [docs/origin-plans/01-modelo-de-datos.md](../../../docs/origin-plans/01-modelo-de-datos.md#L41-L43).

## D-09.05 — Preguntas abiertas de celdas dudosas en ModeloCampo

El archivo `sistema/datos/modelos_resumen.json` incorpora la estructura base de celdas para los 11 modelos y mantiene preguntas abiertas por modelo cuando la fuente no permite fijar inequívocamente tipo o desagregación de algunas celdas. Estas dudas quedan explícitas como `preguntas_abiertas` por modelo y no se resuelven con conjeturas en código. Fuente: [docs/fuentes/Manual implementación SEA-CU 2025.md](../../../docs/fuentes/Manual%20implementaci%C3%B3n%20SEA-CU%202025.md#L1234-L1409), [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L13-L19).

## D-09.06 — Verificación en SQLite y PostgreSQL pendiente documentada

La verificación final de este cambio se ejecuta en SQLite, conforme a la política de desarrollo del proyecto (`D-14`). La validación en PostgreSQL queda pendiente y se documenta explícitamente como no realizada en este cierre; no se registra como prueba superada ni se marca como hecha en la bitácora del cambio. Esta restricción evita afirmar que la verificación de producción se ha ejecutado cuando solo se ha validado el entorno de desarrollo. Fuente: [docs/decisiones/README.md](../../../docs/decisiones/README.md#L124-L130), [sistema/README.md](../../../sistema/README.md#L59-L80).
