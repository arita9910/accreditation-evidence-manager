# Plan 07 — Módulo evidencias (incremento 2)

## Objetivo
Gestionar el expediente documental del ciclo: cargar evidencias con metadatos y huella SHA-256, clasificarlas por criterio, buscarlas, descargarlas con control de permisos y verificar su integridad.

## Convenciones comunes
- Django 5.2 + DRF; React 18 + Vite (JS); SQLite en desarrollo y PostgreSQL en producción; sin SQL propio de un gestor **salvo dentro del servicio de búsqueda** (dos implementaciones).
- Nombres en español. App `sistema/backend/evidencias/` con `modelos.py`, `servicios.py`, `busqueda.py`, `serializadores.py`, `vistas.py`, `urls.py`, `tests/`. Lógica en servicios; vistas delgadas.
- API bajo `/api/`, JSON, sesión + CSRF. Permisos con `cuentas.permisos.puede(...)`; cada operación relevante con `auditoria.servicios.registrar(...)`; escrituras exigen `ciclos.servicios.exigir_ciclo_abierto(ciclo)`.
- Indicador = 2.º nivel; criterio = 3.er nivel. Ambigüedad → `docs/decisiones/`.

## Contexto
CU-07 (cargar), CU-08 (clasificar), CU-09 (buscar y recuperar). Decisiones: D-08 (búsqueda solo en metadatos), D-09 (entrega por Nginx en producción), D-11 (reemplazar = versión nueva). Depende de planes 02 (almacenamiento), 03, 04, 05, 06. **Los requisitos de metadatos y tipos de fichero son propuestos: se validan con las entrevistas antes de este incremento**; si aún no hay entrevistas, usar la propuesta y anotarlo.

## Entidades (plan 01, oleada C)
- **Evidencia:** ciclo (FK), tipo_evidencia (FK a TipoEvidencia), titulo, descripcion, curso_academico, periodo_desde, periodo_hasta, soporte (digital/papel), custodia_original. En papel: sin fichero y `custodia_original` obligatoria (el Manual exige papel para documentos oficiales firmados).
- **FicheroEvidencia:** evidencia (FK), version, nombre_original, nombre_interno (UUID), tamano, tipo_mime, sha256, vigente, subido_por. Nunca se sobrescribe; único (evidencia, version); un solo `vigente`.
- **Clasificacion** (N:M): evidencia (FK), criterio (FK), clasificada_por, fecha; único (evidencia, criterio).

## Tareas

### T1 — Modelos y migraciones con restricciones y pruebas.

### T2 — Servicios
- `crear_evidencia(ciclo, datos, archivo=None, usuario)`: valida metadatos obligatorios (título, tipo, curso/período, soporte), tipo y tamaño de fichero (listas y límite configurables en ajustes: extensiones permitidas, tamaño máximo — valores iniciales propuestos y anotados como pendientes de validar), guarda con `nucleo.almacenamiento.guardar_fichero`, crea `FicheroEvidencia` v1 con sha256, audita.
- `reemplazar_fichero(evidencia, archivo, usuario)`: crea versión nueva, marca la anterior `vigente=False`; nunca borra el anterior.
- `clasificar(evidencia, criterios, usuario)` / `quitar_clasificacion`: una evidencia puede respaldar varios criterios sin duplicar el fichero. La clasificación sugiere los tipos de evidencia de la Guía para el criterio (EvidenciaSugerida).
- `verificar_huellas(ciclo)` y `verificar_huella(fichero)`: recalcula SHA-256 y compara; devuelve estado (correcta/alterada/falta).
- `descargar(fichero, usuario)`: comprueba permisos y audita. En desarrollo devuelve el fichero con Django; en producción responde con cabecera `X-Accel-Redirect` hacia una ubicación interna de Nginx (D-09); el modo se elige por ajuste.
- Permiso por dimensión: un miembro solo carga/clasifica en dimensiones que tiene asignadas (el criterio pertenece a una dimensión).
- **Aceptación (pruebas):** huella guardada = recalculada; un fichero alterado en disco se detecta; evidencia en papel exige custodia y no admite fichero; reemplazo conserva versiones; ciclo cerrado rechaza escrituras; descarga denegada sin permiso y auditada; el administrador técnico no puede descargar.

### T3 — Servicio de búsqueda (`busqueda.py`, D-08)
Interfaz `buscar(ciclo, texto, filtros)` con dos implementaciones elegidas por ajuste: PostgreSQL (búsqueda de texto completo con `SearchVector`/`SearchQuery` sobre título, descripción y nombre original) y SQLite (coincidencia `icontains` por términos). Filtros: dimensión, indicador, criterio, tipo, curso, soporte. **No indexa el contenido de los ficheros.**
- **Aceptación:** misma batería de pruebas para ambas implementaciones (encuentra por palabra y por criterio); las pruebas de PostgreSQL se ejecutan antes de cerrar el incremento.

### T4 — API
- `GET/POST /api/evidencias/` (listar con filtros y búsqueda; crear con `multipart/form-data`), `GET/PATCH /api/evidencias/{id}/`.
- `POST /api/evidencias/{id}/ficheros/` (nueva versión), `GET /api/evidencias/{id}/fichero/` (descarga del vigente), `GET /api/ficheros/{id}/descarga/`.
- `POST/DELETE /api/evidencias/{id}/clasificaciones/`.
- `POST /api/ciclos/{id}/verificar-huellas/` (a demanda; orden de gestión `verificar_huellas` para programarla).
- `GET /api/criterios/{codigo}/evidencias/?ciclo=` (evidencias de un criterio en un ciclo).
- **Aceptación:** pruebas de API para cada endpoint con casos de permiso positivos y negativos.

### T5 — Pantallas React
Lista con búsqueda y filtros; formulario de carga con arrastrar y soltar (valida tipo/tamaño en cliente además del servidor); selector de criterios que muestra las evidencias sugeridas por la Guía; detalle con historial de versiones y estado de la huella; marca visual de evidencias en papel.
- **Aceptación (Vitest):** validación del formulario; la lista aplica filtros.

## Fuera de alcance
Búsqueda en el contenido de los ficheros (OCR), vista previa de documentos, firma electrónica.

## Definición de terminado
Pruebas en verde en SQLite y PostgreSQL; carga, clasificación, búsqueda, descarga y verificación de huella funcionando; avance en `docs/avance/07-evidencias.md`.
