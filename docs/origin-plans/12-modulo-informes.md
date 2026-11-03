# Plan 12 — Módulo informes (incremento 4)

## Objetivo
Componer y exportar el informe de autoevaluación en .docx editable, con versiones para decano y rector, y ofrecer al par evaluador externo la consulta de solo lectura del expediente (CU-19).

## Convenciones comunes
- Django 5.2 + DRF; React 18 + Vite (JS); SQLite en desarrollo y PostgreSQL en producción.
- Nombres en español. App `sistema/backend/informes/` con `modelos.py`, `servicios.py`, `generador.py`, `serializadores.py`, `vistas.py`, `urls.py`, `tests/`. Lógica en servicios; vistas delgadas.
- API bajo `/api/`, JSON, sesión + CSRF. Permisos con `cuentas.permisos.puede(...)`; auditoría con `registrar(...)`.
- Indicador = 2.º nivel; criterio = 3.er nivel. Ambigüedad → `docs/decisiones/`.

## Contexto
CU-14 (generar el informe) y CU-19 (expediente en solo lectura). Depende de todos los módulos anteriores a través de análisis (plan 11) y del prototipo del plan 00 (T4). Requisitos del informe:
- Contenido según la RM 160/2023 (arts. 18.2 y 71) y el Manual: caracterización general de la carrera (matrícula, ingreso, graduados del período); fortalezas y debilidades por dimensión y, en una reacreditación, las mejoras respecto al proceso anterior; estrategia de sostenibilidad del claustro; plan de mejora con acciones, plazos y valoración de resultados; modelos anexos con sus datos, referenciados desde el cuerpo.
- Estructura del **Anexo 6 del Manual**, adaptada a la autoevaluación (RM 160/2023, art. 18.2) — la adaptación exacta se confirma con la tutora; documentar la que se use.
- Formato: Arial 12, interlineado sencillo; aviso si el cuerpo supera 50 páginas sin anexos (D-10: contar con LibreOffice si está en el servidor; si no, estimación declarada como tal).
- Porcentajes con su relación de origen (reutilizar `valoracion.servicios.formatear_porcentaje`).
- Descarga editable (.docx), con python-docx.

## Entidades (plan 01, oleada E)
- **TextoInforme:** ciclo (FK), seccion, contenido, editado_por. Texto cualitativo que redactan los usuarios (caracterización, estrategia de sostenibilidad).
- **VersionInforme:** ciclo (FK), numero, fichero (nombre interno), sha256, paginas, metodo_conteo (LibreOffice/estimado), avisos.

## Tareas

### T1 — Modelos, migraciones y pruebas.

### T2 — Textos del informe
`guardar_texto(ciclo, seccion, contenido, usuario)` con las secciones definidas en una constante documentada; director o miembro (según la matriz); ciclo abierto. API `GET/PUT /api/ciclos/{id}/informe/textos/{seccion}/`.

### T3 — Generador (`generador.py`)
`generar_docx(ciclo) -> ruta` que compone: portada y datos del ciclo, caracterización (texto + datos), fortalezas y debilidades por dimensión (con criterios y referencias a evidencias), plan de mejora, modelos anexos con los datos del ciclo (los 11), y el plan del ciclo anterior valorado cuando exista. Estilo Arial 12 interlineado sencillo; tablas legibles; referencias a evidencias por título y código del criterio.
- **Aceptación (pruebas):** el documento contiene las secciones obligatorias (se abre con python-docx y se comprueban títulos); los porcentajes llevan su relación; el estilo es Arial 12 en el cuerpo; los 11 modelos aparecen con los datos del ciclo de prueba.

### T4 — Versiones y conteo de páginas
`generar_version(ciclo, usuario)`: ejecuta `completitud` (plan 11) y guarda los avisos en la versión (sin bloquear); genera el .docx, lo guarda con `nucleo.almacenamiento`, registra SHA-256, cuenta páginas (LibreOffice en modo sin pantalla si está disponible; si no, estimación por caracteres, `metodo_conteo='estimado'`) y avisa si supera 50 páginas sin anexos. Cada versión queda disponible para decano y rector.
- **Aceptación:** número de versión incrementa; el aviso de 50 páginas aparece con un documento de prueba largo; sin LibreOffice se usa el método estimado y se declara.

### T5 — API
`POST /api/ciclos/{id}/informe/generar/`, `GET /api/ciclos/{id}/informe/versiones/`, `GET /api/informes/versiones/{id}/descarga/`. Permisos: genera el director; descargan director, decano, rector y, solo la versión final de su ciclo, el par evaluador. **Aceptación:** pruebas de permisos positivos y negativos.

### T6 — Expediente de solo lectura (CU-19)
`GET /api/ciclos/{id}/expediente/`: árbol del ciclo con evidencias clasificadas, datos y vínculos, y descarga de ficheros, solo para el par evaluador con asignación vigente a ese ciclo. Sin ningún endpoint de escritura accesible a ese rol. Cada consulta y descarga se audita. Acceso caducado → rechazo auditado.
- **Aceptación:** el par evaluador no puede escribir (todas las escrituras devuelven 403); tras `vigente_hasta` pierde el acceso; solo ve su ciclo.

### T7 — Pantallas React
Editor de textos cualitativos; página de generación con los avisos de completitud, historial de versiones y descarga; expediente del par evaluador (reutiliza el árbol del catálogo y la lista de evidencias en modo lectura). **Aceptación (Vitest):** los avisos se muestran y no bloquean el botón de generar; el modo lectura no muestra acciones de escritura.

## Fuera de alcance
Exportación a PDF, firma electrónica, edición del .docx dentro del sistema, plantillas personalizables por carrera.

## Definición de terminado
Pruebas en verde; informe .docx generado y revisado a mano en Word o LibreOffice (anotar hallazgos); CU-19 funcionando; avance en `docs/avance/12-informes.md`.
