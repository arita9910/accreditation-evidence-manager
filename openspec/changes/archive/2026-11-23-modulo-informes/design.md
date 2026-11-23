# Design

## Context

El cambio sigue el alcance del Plan 12 y reutiliza los módulos ya implementados de análisis, valoración, mejora, evidencias y permisos. Las decisiones se basan en `docs/origin-plans/12-modulo-informes.md:6-18`, en el contenido del informe exigido por el Manual 2025 y en la mejora continua establecida por la Resolución No.36/2024.

## Goals / Non-Goals

**Goals:**
- Persistir textos cualitativos y versiones numeradas por ciclo.
- Componer un DOCX editable con datos reales, análisis y 11 modelos anexos.
- Mantener autorizaciones y auditoría centralizadas.
- Entregar una vista de expediente de solo lectura al par evaluador con vigencia limitada y descarga de ficheros autorizada.
- Mantener coherencia con la decisión vigente de roles reales del proyecto (`administrador_tecnico`, `director_carrera`) y extenderlos explícitamente solo cuando el cambio lo requiera.

**Non-Goals:**
- Exportación PDF, firma electrónica, edición del DOCX dentro del sistema o plantillas personalizables.
- Implementación de PostgreSQL específica; las pruebas se realizan con SQLite.
- Resolución de la adaptación exacta del Anexo 6 antes de la confirmación de la tutora.

## Decisions

### Organizar la implementación en `sistema/backend/informes/`
Se usarán `modelos.py`, `servicios.py`, `generador.py`, `serializadores.py`, `vistas.py`, `urls.py` y `tests/`, conforme al Plan 12. La lógica de dominio permanecerá en servicios y las vistas DRF serán delgadas.

**Alternativa considerada:** dispersar la generación y los permisos en las vistas. Se descarta porque contradice la arquitectura existente y dificulta probar el comportamiento.

### Aplicar las funciones de autorización y auditoría existentes
Las operaciones editables SHALL pasar por `exigir_ciclo_abierto(...)`, las decisiones de acceso SHALL usar `puede(...)` y los eventos relevantes SHALL usar `registrar(...)`. Los accesos denegados 403 no se duplicarán en servicios; se registran por middleware.

**Alternativa considerada:** reglas locales por vista. Se descarta por duplicación y por el contrato ya definido en el módulo de cuentas.

### Mantener lógica declarativa de secciones
Las secciones cualitativas se definirán en una constante documentada. `guardar_texto(ciclo, seccion, contenido, usuario)` validará sección, autorización y ciclo abierto.

**Alternativa considerada:** columnas fijas por tipo de texto. Se descarta porque el Plan 12 exige secciones extensibles y asociadas por nombre.

### Generar y almacenar versiones con trazabilidad
`generar_version(ciclo, usuario)` ejecutará completitud sin bloquear, generará el DOCX, lo almacenará mediante `nucleo.almacenamiento`, calculará SHA-256 y asignará número, método de conteo y avisos. LibreOffice se usará si está disponible; en caso contrario se usará estimación por caracteres con declaración explícita.

**Alternativa considerada:** almacenar únicamente la ruta sin metadatos. Se descarta porque el plan exige número, huella, conteo, método y avisos.

### Componer el expediente como vista de lectura
`GET /api/ciclos/{id}/expediente/` devolverá el árbol de evidencias y datos solo a un par evaluador con asignación vigente. Todos los endpoints de escritura seguirán denegando 403 a ese rol. Las consultas y descargas usarán `registrar(...)`.

**Alternativa considerada:** reutilizar los endpoints administrativos con filtros. Se descarta porque el rol expuesto requeriría una lectura aislada y sin acciones de escritura.

### Extender cuentas para soportar CU-19 sin ambigüedad
Se incorporará `par_evaluador` y una asignación de rol por ciclo con `vigente_desde` y `vigente_hasta` para evaluar vigencia en cada consulta/descarga. El acceso de concesión se ejecutará por backend y, como medida provisional, la asignación inicial se hará por Django Admin si no entra una pantalla de gestión en este bloque.

**Alternativa considerada:** dejar CU-19 en cambio aparte. Se descarta por alcance confirmado del Plan 12 para el incremento 4.

## Risks / Trade-offs

- [Conteo LibreOffice indisponible] → Usar estimación por caracteres y persistir `metodo_conteo='estimado'`.
- [Documento mayor de 50 páginas sin anexos] → Mostrar advertencia sin bloquear la generación.
- [Datos incompletos de completitud] → Conservar los avisos en la versión y permitir generar.
- [Adaptación pendiente del Anexo 6] → Usar una estructura documentada y registrar la confirmación de la tutora antes de cerrar el formato manual.
- [Asignación caducada durante una consulta] → Evaluar vigencia en cada acceso y auditar el rechazo.
- [“Versión final” no definida explícitamente] → Regla provisional: versión de mayor `numero` por ciclo; documentar como decisión abierta.
- [Conteo “sin anexos” difícil con una sola salida DOCX] → Medir sobre copia de cuerpo sin anexos cuando haya LibreOffice; si no, estimación por caracteres documentada.

## Migration Plan

1. Crear las migraciones de `TextoInforme` y `VersionInforme`.
2. Crear migración de cuentas para `par_evaluador` y asignación por ciclo con vigencia.
3. Agregar servicios, generador y rutas sin modificar dependencias existentes.
4. Verificar `migrate` y `showmigrations` en SQLite.
5. Integrar las pantallas React con los endpoints disponibles.
6. Ejecutar las pruebas bajo SQLite.
7. Revisar manualmente el DOCX en Word o LibreOffice y registrar hallazgos en `sistema/docs/avance/12-informes.md`.

No se define rollback de datos normativo; ante fallo, se conserva la versión anterior y se corrige la generación sin borrar versiones existentes.

## Open Questions

- ¿Cuál es la adaptación exacta del Anexo 6 del Manual para este sistema? El plan exige confirmación con la tutora y documentar la estructura usada.
- ¿Qué secciones cualitativas concretas integran la constante `TextoInforme` además de caracterización y estrategia de sostenibilidad?
- ¿Qué campos o derivaciones define “datos del ciclo” en los 11 modelos anexos cuando no existan datos cargados?
- ¿Se incorpora en este mismo bloque la pantalla para que director conceda/revoque el acceso del par evaluador o se mantiene temporalmente por Django Admin?
- ¿La “versión final” se mantiene como mayor número por ciclo o requiere marca explícita en el modelo?
- ¿Cuál constante de caracteres por página se adopta para la estimación declarada cuando LibreOffice no esté disponible?

Fuentes: Plan 12 en `docs/origin-plans/12-modulo-informes.md:6-18`, `docs/origin-plans/12-modulo-informes.md:20-52`; Manual 2025 en `docs/fuentes/Manual implementación SEA-CU 2025.md:176-205`; Resolución No.36/2024 SEA-CU en `docs/fuentes/Resolución No.36-2024 SEA-CU.md:22-27` y `docs/fuentes/Resolución No.36-2024 SEA-CU.md:68-107`.
