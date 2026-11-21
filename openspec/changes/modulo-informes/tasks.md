# Tasks

## 1. Modelos/Servicios

- [x] 1.1 Crear `TextoInforme` y `VersionInforme` con migraciones, relaciones al ciclo, editor y metadatos de versión, y verificar las migraciones y modelos bajo SQLite.
- [x] 1.2 Implementar la constante documentada de secciones y `guardar_texto(ciclo, seccion, contenido, usuario)` con autorización, `exigir_ciclo_abierto(ciclo)`, `puede(...)` y `registrar(...)`; verificar pruebas positivas y negativas.
- [x] 1.3 Extender cuentas con rol `par_evaluador` y entidad de asignación por ciclo (`vigente_desde`, `vigente_hasta`), actualizando `puede(...)`; verificar permisos y vigencia con pruebas unitarias.
- [x] 1.4 Implementar `generar_version(ciclo, usuario)` en transacción: ejecutar `completitud`, persistir avisos JSON sin bloquear, generar DOCX, numerar versión con `unique(ciclo, numero)`, registrar SHA-256 y método de conteo; verificar con pruebas de concurrencia básica.
- [x] 1.5 Implementar el almacenamiento de versiones y el cálculo de SHA-256 mediante `nucleo.almacenamiento`; verificar persistencia y huella con una versión de prueba.
- [x] 1.6 Implementar conteo por LibreOffice y estimación por caracteres para “cuerpo sin anexos”, incluyendo `metodo_conteo='estimado'` y advertencia de más de 50 páginas; verificar ambos métodos bajo SQLite.

## 2. Generación DOCX

- [x] 2.1 Implementar `generar_docx(ciclo) -> ruta` con portada, datos del ciclo, caracterización, análisis por dimensión, plan de mejora, sostenibilidad y plan anterior valorado cuando exista.
- [x] 2.2 Agregar fortalezas y debilidades por dimensión con criterios y referencias a evidencias por título y código; verificar títulos y referencias en el DOCX.
- [x] 2.3 Incorporar los 11 modelos anexos con datos del ciclo y reutilizar `valoracion.servicios.formatear_porcentaje`; verificar los modelos y las relaciones numéricas.
- [x] 2.4 Aplicar Arial 12 e interlineado sencillo, tablas legibles y estructura DOCX editable; abrir el resultado en Word o LibreOffice y verificar la revisión manual.

## 3. API

- [x] 3.1 Implementar `POST /api/ciclos/{id}/informe/generar/`, autorizando solo al director y exigiendo ciclo abierto; verificar permisos positivos y negativos.
- [x] 3.2 Implementar `GET /api/ciclos/{id}/informe/textos/` y `GET/PUT /api/ciclos/{id}/informe/textos/{seccion}/`; verificar sesión, CSRF, permisos y ciclo abierto bajo SQLite.
- [x] 3.3 Implementar `GET /api/ciclos/{id}/informe/versiones/` y `GET /api/informes/versiones/{id}/descarga/` para roles vigentes y regla provisional de versión final (máximo `numero`) para par evaluador; verificar permisos positivos y negativos.
- [x] 3.4 Implementar `GET /api/ciclos/{id}/expediente/` y `GET /api/ciclos/{id}/expediente/ficheros/{fichero_id}/descarga/` para el par evaluador con asignación vigente, sin endpoints de escritura accesibles; verificar aislamiento por ciclo y caducidad de `vigente_hasta`.
- [x] 3.5 Auditar explícitamente generación, descargas autorizadas y consulta exitosa del expediente con `registrar(...)`, evitando duplicar registros de denegación 403 del middleware; verificar trazabilidad.

## 4. Pantalla

- [x] 4.1 Crear el editor React de textos cualitativos y verificar carga, guardado y mensajes de ciclo cerrado.
- [x] 4.2 Crear la página de generación con avisos de completitud, historial de versiones y descarga; verificar que los avisos no bloquean el botón de generar con Vitest.
- [x] 4.3 Crear la vista React del expediente del par evaluador reutilizando el árbol del catálogo y evidencias; verificar que no aparecen acciones de escritura con Vitest.
- [ ] 4.4 Definir provisoriamente la gestión de asignación del par evaluador (Django Admin si no entra pantalla de director en este bloque) y verificar el flujo extremo a extremo.
- [x] 4.5 Ejecutar las pruebas Vitest enfocadas en las pantallas nuevas con `npm run test:run -- --pool=vmThreads --maxWorkers=1`.

## 5. Verificación

- [ ] 5.1 Ejecutar `python manage.py migrate` y `python manage.py showmigrations` para confirmar migraciones del bloque en SQLite.
- [ ] 5.2 Ejecutar las pruebas Django relacionadas con modelos, servicios, generador, permisos, versiones y expediente bajo SQLite.
- [ ] 5.3 Verificar con `git check-ignore` que la ruta de salida de informes DOCX queda fuera de Git.
- [ ] 5.4 Generar un informe DOCX de prueba largo y abrirlo en Word o LibreOffice; verificar secciones obligatorias, 11 modelos, estilo, aviso de 50 páginas y hallar errores observables.
- [ ] 5.5 Verificar que el par evaluador no puede escribir, pierde acceso tras `vigente_hasta` y solo ve su ciclo; mantener las pruebas SQLite en verde.
- [ ] 5.6 Registrar la revisión manual y el avance del incremento en `sistema/docs/avance/12-informes.md` según la definición de terminado.

## Workflow follow-up

- Después de revisión y pruebas, ejecutar la aplicación de este cambio por `/opsx-apply` u la instrucción de aplicación correspondiente.
- PostgreSQL queda pendiente como validación posterior y no se declara probado por esta propuesta.
