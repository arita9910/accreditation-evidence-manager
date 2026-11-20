# Proposal

## Why

El incremento 12 completa la producción del informe de autoevaluación y el acceso controlado del expediente al par evaluador externo. El Plan 12 exige convertir los datos y análisis acumulados en un informe DOCX editable, con versiones trazables y consulta de solo lectura, alineado con el contenido obligatorio del Manual y la mejora continua definida por el SEA-CU.

Fuentes obligatorias: [Plan 12, objetivo y alcance](docs/origin-plans/12-modulo-informes.md:3-18), [Plan 12, entidades y tareas](docs/origin-plans/12-modulo-informes.md:20-52); [Manual 2025, contenido del informe](docs/fuentes/Manual%20implementaci%C3%B3n%20SEA-CU%202025.md:176-205); [Resolución No.36/2024 SEA-CU, objetivos y mejora continua](docs/fuentes/Resolución%20No.36-2024%20SEA-CU.md:22-27), [Resolución No.36/2024 SEA-CU, dimensiones](docs/fuentes/Resolución%20No.36-2024%20SEA-CU.md:68-107).

## What Changes

- Incorporar los modelos `TextoInforme` y `VersionInforme` y los servicios para editar textos cualitativos, generar versiones DOCX y contar páginas.
- Generar un informe de autoevaluación con portada, caracterización, fortalezas y debilidades por dimensión, plan de mejora, estrategia de sostenibilidad, datos de los 11 modelos anexos y el plan anterior valorado cuando exista.
- Mantener formato DOCX editable con Arial 12 e interlineado sencillo, Python `python-docx`, porcentajes con su relación de origen y aviso de longitud superior a 50 páginas sin anexos.
- Exponer la generación, el historial y la descarga de versiones bajo `/api/`, con autorización centralizada mediante `puede(...)`, obligatoriedad de ciclo abierto para operaciones de edición mediante `exigir_ciclo_abierto(...)` y trazabilidad mediante `registrar(...)`.
- Incorporar el expediente de solo lectura CU-19 para el par evaluador, limitado a su ciclo y a una asignación vigente; auditar consultas, descargas y rechazos de acceso caducado.
- Incorporar las pantallas React de edición, generación, historial, descarga y expediente de lectura.

## Capabilities

### New Capabilities
- `informes-autoevaluacion`: cubre textos cualitativos, composición y generación DOCX, versiones, conteo de páginas y descarga autorizada del informe.
- `expediente-evaluador`: cubre la consulta de solo lectura del expediente y la auditoría de consultas y descargas para el par evaluador externo.

### Modified Capabilities
- `docx-generation`: amplía el prototipo de DOCX a la generación real del informe con secciones obligatorias, 11 modelos, formato base y revisión manual.

## Impact

- Backend: `sistema/backend/informes/` con modelos, servicios, generador, serializadores, vistas y pruebas.
- API: rutas bajo `/api/ciclos/{id}/informe/...`, `/api/informes/versiones/{id}/descarga/` y `/api/ciclos/{id}/expediente/`.
- Permisos y auditoría: reutilización de `cuentas.permisos.puede(...)`, `ciclos.servicios.exigir_ciclo_abierto(...)` y `auditoria.servicios.registrar(...)`.
- Frontend: editor, página de generación e historial, y expediente de solo lectura reutilizando componentes del catálogo y evidencias.
- Dependencias: no se añaden paquetes; la generación DOCX reutiliza `python-docx` ya previsto por el proyecto.
