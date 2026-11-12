# Design

## Context

El diseño se apoya en el plan 07 del módulo de evidencias y en las decisiones del repositorio: búsqueda en metadatos, versionado por reemplazo, entrega protegida de ficheros y uso de la arquitectura Django/React con depósito documental separado del almacenamiento público. El módulo debe integrarse con los servicios ya existentes de ciclos, cuentas y auditoría, y respetar la regla de que los archivos nunca se sobrescriben. Véase la motivación en [proposal.md](proposal.md) y los requisitos de la especificación [specs/evidencias/spec.md](specs/evidencias/spec.md).

## Goals / Non-Goals

**Goals:**
- Gestionar el ciclo documental con evidencias digitales y en papel.
- Asegurar integridad con SHA-256 y versionado por reemplazo.
- Proteger descargas y escrituras con permisos por rol y dimensión.
- Exponer API y pantalla para listado, carga, descarga y verificación.

**Non-Goals:**
- No se busca OCR ni búsqueda en el contenido de los archivos.
- No se implementa vista previa ni firma electrónica de documentos.
- No se añade un modelo de `TipoEvidencia` definitivo sin validación de entrevistas; esta parte quedará como decisión abierta.

## Decisions

### 1. Versionado sin sobrescritura de ficheros
La decisión clave es que cada reemplazo de un archivo cree una nueva versión y conserve la anterior activa como historial. Esto se alinea con D-11: “Reemplazar un fichero crea versión nueva” y con la propia definición del plan 07, que exige que `FicheroEvidencia` sea versionado y que el archivo nunca se sobrescriba. Fuente: [docs/decisiones/README.md](docs/decisiones/README.md):97-104 y [docs/origin-plans/07-modulo-evidencias.md](docs/origin-plans/07-modulo-evidencias.md):15-18, 24-31.

### 2. Búsqueda solo en metadatos y no en contenido
La búsqueda se hará sobre metadatos y no sobre el contenido del archivo. La decisión formal está en D-08, que restringe la búsqueda a metadatos con dos implementaciones de servicio: PostgreSQL con texto completo y SQLite con coincidencia por texto. Fuente: [docs/decisiones/README.md](docs/decisiones/README.md):70-77 y [docs/origin-plans/07-modulo-evidencias.md](docs/origin-plans/07-modulo-evidencias.md):33-35.

### 3. Entrega protegida de archivo según entorno
La descarga alimentará la política de D-09: la API comprueba permisos y el entorno decide la entrega. En desarrollo, Django sirve el archivo; en producción, Nginx recibe la entrega por X-Accel-Redirect. Fuente: [docs/decisiones/README.md](docs/decisiones/README.md):79-86 y [docs/origin-plans/07-modulo-evidencias.md](docs/origin-plans/07-modulo-evidencias.md):24-31.

### 4. Integración con módulos existentes
La evidencia no reemplaza la lógica central existente: se reutiliza la firma actual de los servicios ya presentes en el proyecto.

- `exigir_ciclo_abierto(ciclo)` en [sistema/backend/ciclos/servicios.py](../sistema/backend/ciclos/servicios.py#L52-L57): valida que el ciclo esté abierto antes de operar sobre datos dependientes del ciclo.
- `registrar(accion, *, usuario=None, entidad=None, detalle=None, contexto=None, **kwargs)` en [sistema/backend/auditoria/servicios.py](../sistema/backend/auditoria/servicios.py#L22-L37): registra eventos de negocio con detalle serializado.
- `puede(actor, accion, objeto=None, *, recurso=None, contexto=None)` en [sistema/backend/cuentas/permisos.py](../sistema/backend/cuentas/permisos.py#L193-L208): resuelve permisos por rol y contexto, y se usa para autorizar operaciones por dimensión y carrera.

### 5. TipoEvidencia queda abierto a la validación de entrevistas
El modelo de `TipoEvidencia` requiere una definición de naturaleza y soporte que aún no está confirmada por las entrevistas A6. Por tanto, este diseño no inventa un catálogo definitivo ni presupone un soporte concreto más allá de los requisitos propuestos. La intención del plan es dejarlo abierto con la propuesta y con validación posterior. Fuente: [docs/origin-plans/07-modulo-evidencias.md](docs/origin-plans/07-modulo-evidencias.md#L12-L18).

## Risks / Trade-offs

- [Riesgo] La validación de tipos y soportes puede cambiar con las entrevistas → Mitigación: mantener un modelo flexible y un catálogo configurable en la capa de servicio o de datos sin cerrar la API antes de la validación.
- [Riesgo] La huella SHA-256 exige almacenamiento seguro y limpieza de archivos no válidos → Mitigación: diseñar el servicio con rutas internas protegidas y verificación de integridad en la capa de almacenamiento.
- [Riesgo] La gestión de permisos por dimensión requiere contexto de cada criterio → Mitigación: centralizar la decisión en `puede(...)` y mantener el contexto del ciclo y la carrera en cada operación de carga o clasificación.

## Migration Plan

1. Añadir modelos y migración del módulo de evidencias con relaciones por ciclo, criterio y fichero.
2. Implementar la capa de almacenamiento y la verificación de huella con rutas internas protegidas.
3. Añadir servicios de carga, reemplazo, verificación, clasificación y descarga con auditoría.
4. Exponer los endpoints REST y mantener los permisos de la API con sesión y CSRF.
5. Añadir la pantalla principal de lista, filtros, detalle y formulario de carga; completar pruebas del módulo con SQLite y validación previa de PostgreSQL cuando haya entorno disponible.

## Open Questions

- TipoEvidencia: naturaleza, soporte y catálogo exacto pendientes de las entrevistas A6.
- Límite de tamaño y extensiones permitidas para cada tipo de fichero: se propondrán valores iniciales, pero se validarán antes de la implementación real.
- La política exacta de acceso para miembros por dimensión y carrera, si se requiere más granularidad que la aprobación basada en `puede(...)`.

## Observación de cumplimiento

El diseño conserva el principio del plan 07: cada archivo de evidencia tiene una huella SHA-256, nunca se sobrescribe el archivo original, el historial de versiones se mantiene y la escritura exige una validación explícita de ciclo abierto y permisos. Esto reúne la intención del plan sin imponer decisiones de catálogo no validadas aún.
