# Tasks

## 1. Modelos/Servicios

- [ ] 1.1 Crear `TextoInforme` y `VersionInforme` con migraciones, relaciones al ciclo, editor y metadatos de versión, y verificar las migraciones y modelos bajo SQLite.
- [ ] 1.2 Implementar la constante documentada de secciones y `guardar_texto(ciclo, seccion, contenido, usuario)` con autorización, `exigir_ciclo_abierto(ciclo)`, `puede(...)` y `registrar(...)`; verificar pruebas positivas y negativas.
- [ ] 1.3 Implementar el almacenamiento de versiones y el cálculo de SHA-256 mediante `nucleo.almacenamiento`; verificar persistencia y huella con una versión de prueba.
- [ ] 1.4 Implementar conteo por LibreOffice y estimación por caracteres, incluyendo `metodo_conteo='estimado'` y advertencia de más de 50 páginas; verificar ambos métodos bajo SQLite.

## 2. Generación DOCX

- [ ] 2.1 Implementar `generar_docx(ciclo) -> ruta` con portada, datos del ciclo, caracterización, análisis por dimensión, plan de mejora, sostenibilidad y plan anterior valorado cuando exista.
- [ ] 2.2 Agregar fortalezas y debilidades por dimensión con criterios y referencias a evidencias por título y código; verificar títulos y referencias en el DOCX.
- [ ] 2.3 Incorporar los 11 modelos anexos con datos del ciclo y reutilizar `valoracion.servicios.formatear_porcentaje`; verificar los modelos y las relaciones numéricas.
- [ ] 2.4 Aplicar Arial 12 e interlineado sencillo, tablas legibles y estructura DOCX editable; abrir el resultado en Word o LibreOffice y verificar la revisión manual.

## 3. API

- [ ] 3.1 Implementar `POST /api/ciclos/{id}/informe/generar/`, autorizando solo al director y exigiendo ciclo abierto; verificar permisos positivos y negativos.
- [ ] 3.2 Implementar `GET/PUT /api/ciclos/{id}/informe/textos/{seccion}/` y `GET /api/ciclos/{id}/informe/versiones/`; verificar sesión, CSRF, permisos y ciclo abierto bajo SQLite.
- [ ] 3.3 Implementar `GET /api/informes/versiones/{id}/descarga/` para director, decano, rector y par evaluador solo en la versión final de su ciclo; verificar denegaciones.
- [ ] 3.4 Implementar `GET /api/ciclos/{id}/expediente/` para el par evaluador con asignación vigente, sin endpoints de escritura accesibles; verificar aislamiento por ciclo y caducidad de `vigente_hasta`.
- [ ] 3.5 Auditar generación, descarga, consulta del expediente, rechazo y acceso caducado con `registrar(...)`; verificar que los registros contienen usuario, entidad y resultado.

## 4. Pantalla

- [ ] 4.1 Crear el editor React de textos cualitativos y verificar carga, guardado y mensajes de ciclo cerrado.
- [ ] 4.2 Crear la página de generación con avisos de completitud, historial de versiones y descarga; verificar que los avisos no bloquean el botón de generar con Vitest.
- [ ] 4.3 Crear la vista React del expediente del par evaluador reutilizando el árbol del catálogo y evidencias; verificar que no aparecen acciones de escritura con Vitest.
- [ ] 4.4 Ejecutar las pruebas Vitest enfocadas en las pantallas nuevas con `npm run test:run -- --pool=vmThreads --maxWorkers=1`.

## 5. Verificación

- [ ] 5.1 Ejecutar las pruebas Django relacionadas con modelos, servicios, generador, permisos, versiones y expediente bajo SQLite.
- [ ] 5.2 Generar un informe DOCX de prueba largo y abrirlo en Word o LibreOffice; verificar secciones obligatorias, 11 modelos, estilo, aviso de 50 páginas y hallar errores observables.
- [ ] 5.3 Verificar que el par evaluador no puede escribir, pierde acceso tras `vigente_hasta` y solo ve su ciclo; mantener las pruebas SQLite en verde.
- [ ] 5.4 Registrar la revisión manual y el avance del incremento en `docs/avance/12-informes.md` según la definición de terminado.

## Workflow follow-up

- Después de revisión y pruebas, ejecutar la aplicación de este cambio por `/opsx-apply` u la instrucción de aplicación correspondiente.
- PostgreSQL queda pendiente como validación posterior y no se declara probado por esta propuesta.
