# Design

## Context

Consulta `proposal.md` para la motivación y `specs/estructura-normativa/spec.md` para el comportamiento observable. Los diez modelos de estructura y su migración ya existen en `sistema/backend/estructura/`; todavía no hay servicios, serializadores, vistas ni rutas API para el catálogo. El proyecto cuenta con un manejador común de excepciones DRF y paginación; el frontend dispone del cliente API compartido `peticion` y de una estructura mínima con React Router.

El JSON del catálogo existente se inspeccionó, no se regeneró desde el CSV. Tiene las claves raíz `catalogo`, `version`, `fuente`, `codificacionFuente`, `resumen` y `dimensiones`; las dimensiones contienen `nombre` e `indicadores`; los indicadores, `codigo` y `criterios`; y los criterios, `criterio`, `criterio_texto`, `codigo_guia`, `solo_en_guia`, `tipo_dato`, `modelos_manual`, `requisito_por_categoria`, `evidencias_guia`, cuatro campos `requisito_*` y `nota_normativa`. El resumen y los conteos anidados coinciden en 6 dimensiones, 24 indicadores y 65 criterios. `criterio` y `criterio_texto` no son nombres de campos del modelo, y el JSON no contiene `codigo_manual` ni texto de indicador.

Existe `modelos_resumen.json` con 11 identificadores confirmados. Sus nombres se toman del Manual y se incorporan en este incremento; sus definiciones de celdas quedan pendientes. El catálogo contiene 20 criterios con `modelos_manual` no vacío, que corresponden a 22 asociaciones al separar las referencias múltiples. Los dos documentos normativos están disponibles como Markdown bajo `docs/fuentes/`. El cotejo final debe resolver las dudas de numeración 4.4.4 y 5.2.4–5.2.6 sin conjeturas. D-14 limita la verificación de base de datos a SQLite.

## Goals / Non-Goals

**Goals:**
- Cargar el catálogo observado en las entidades de estructura existentes, preservando el texto de las fuentes y las relaciones de versión.
- Proporcionar endpoints de consulta de solo lectura y vistas React navegables con la infraestructura existente.
- Mantener visibles las asignaciones de fuente no resueltas y hacer del cotejo criterio por criterio la sección final de tareas.

**Non-Goals:**
- Recrear el JSON o el CSV, inferir valores normativos faltantes o corregir el texto del catálogo sin evidencia directa de las fuentes.
- Definir celdas de modelo, calcular categorías de acreditación ni permitir la edición del catálogo desde la interfaz.
- Cambiar los diez modelos de estructura existentes ni probar comportamiento específico de bases de datos distintas de SQLite.
- Agregar dependencias o cambiar la configuración de la base de datos de producción.

## Decisions

1. **Adaptar el cargador al JSON existente.** Validar las claves anidadas y los totales calculados 6/24/65 antes de escribir. Los seis nombres de dimensión observados empiezan con su código numerado; interpretar ese entero inicial como código/orden y rechazar nombres que no sigan el patrón observado. Mapear solo campos presentes, con normalización explícita de representaciones conocidas (como `sí`/`no`, `criterio_texto` y los cuatro campos de requisito por categoría). Separar `evidencias_guia` únicamente por sus separadores visibles `|` y preservar cada texto de evidencia; marcar entrevistas y visitas como verificaciones externas solo según lo indicado por el Plan 03. Un formato inválido o un total distinto debe producir un error claro; la importación se ejecuta en una transacción para impedir versiones parciales.
2. **Reutilizar los modelos ORM y los datos de versión existentes.** Ubicar el comando de gestión y la lógica de dominio en la app `estructura` y su capa de servicios; no introducir modelos paralelos ni cambios de esquema. Resolver referencias de modelo a partir de los identificadores existentes en `modelos_resumen.json`, sin inventar celdas. Hacer idempotentes las recargas mediante claves naturales y no reasignar ciclos existentes a otra versión normativa.
3. **Bloquear la importación completa si faltan valores obligatorios sin respaldo.** No usar valores en blanco, derivados del código ni de relleno para satisfacer campos obligatorios de los modelos. Los valores obligatorios faltantes se incorporan al JSON únicamente cuando exista evidencia directa de las fuentes, con archivo y línea registrados en `sistema/docs/avance/03-cotejo-catalogo.md`, en campos con nombre documentado; el cargador los lee de esos campos. Si siguen faltando, el comando informa cuáles y se detiene antes de crear o modificar registros.
4. **Mantener explícita y conservadora la política de API.** Añadir únicamente recursos GET del catálogo bajo `/api/`, usando las convenciones DRF existentes, el formato de errores compartido, paginación donde corresponda y la configuración actual de sesión/CSRF. La opción de exposición en desarrollo queda apagada por defecto y debe rechazarse en producción; no agregar el comportamiento de autenticación reservado al Plan 05.
5. **Usar el cliente compartido del frontend y la estructura actual.** Añadir rutas y vistas del catálogo a la aplicación React existente; obtener datos de la API mediante `src/api/cliente.js`. Mantener la búsqueda y expansión del árbol en el cliente salvo que la API requiera otra cosa; mostrar los requisitos como referencia e incluir el aviso prescrito de que no se calcula la categoría.
6. **Tratar el cotejo de fuentes como una tarea final con condiciones.** Buscar cada criterio en los documentos Markdown por separado, no leer los archivos completos. La sección final T4 compara al menos 12 criterios distintos, incluye los grupos del Plan 03 y registra evidencia y estado en una tabla. Solo se modifican valores del catálogo cuando la fuente respalda directamente la corrección. Las diferencias no resueltas se documentan y no se marcan como concluidas.
7. **Usar las ubicaciones de documentación solicitadas.** Registrar el avance en `sistema/docs/avance/` y las decisiones abiertas en `sistema/docs/decisiones/`, aunque ya exista `docs/decisiones/README.md` en la raíz.
8. **Registrar la fecha de aprobación pendiente de confirmación.** Por decisión de la tesista, usar `2024-04-29`, fecha de la Resolución No. 36/2024 (`Resolución No.36-2024 SEA-CU.md`, líneas 35 y 47). El Manual 2025 no contiene fecha propia; en `Manual:13` solo aparece el año. Guardar la fecha en el campo documentado `fecha_aprobacion` del JSON del catálogo. La confirmación del tutor queda abierta.
9. **Mapear `VersionNormativa` desde las claves del catálogo.** `nombre` se obtiene de las claves `catalogo` y `version`; `fuentes`, de la clave `fuente`. `activa` representa el estado del sistema, no un dato normativo: el cargador la fija en verdadero para la versión que carga, que por ahora es la única.
10. **Obtener `Indicador.texto` del Manual.** Extraer el texto completo de los 24 indicadores en la tarea 4.3; las ubicaciones son: 1.1=375, 1.2=383, 1.3=391, 2.1=402, 2.2=406, 2.3=418, 2.4=433, 2.5=441, 2.6=445, 3.1=463, 3.2=469, 3.3=478, 3.4=484, 4.1=490, 4.2=498, 4.3=502, 4.4=523, 5.1=537, 5.2=541, 5.3=556, 5.4=558, 6.1=566, 6.2=570 y 6.3=580 (`Manual`, líneas indicadas).
11. **Mapear desde el JSON los campos obligatorios de `Criterio`.** `codigo` ← `criterio`; `codigo_guia`, `solo_en_guia` y `tipo_dato` ← las claves homónimas; `texto` ← `criterio_texto`; `valoracion_por_categoria` ← `requisito_por_categoria`, convirtiendo `sí`/`no` a booleano. El cargador falla ante cualquier otro valor de requisito.
12. **Asignar `codigo_manual` solo cuando lo confirme el cotejo.** Los 64 criterios que no son solo-Guía aparecen en el Manual con el mismo código; por tanto, `codigo_manual` = `criterio` para ellos, excepto los casos que el cotejo de 4.2 deje en duda: 4.4.4 y 5.2.4–5.2.6. El criterio 3.2.4, que es solo de la Guía, no recibe `codigo_manual`. La comprobación automática previa solo comparó el tramo común de palabras y no sustituye el cotejo.
13. **Completar los nombres de `ModeloDefinicion` con el Manual.** `numero` ← `modelos[].numero`; `nombre` se obtiene del Manual y se escribe como `nombre.valor` en `modelos_resumen.json` en la tarea 4.3: 1 Resumen del claustro (línea 1234); 2 Publicaciones (1244); 3 Presentación de ponencias en eventos (1261); 4 Proyectos de investigación (1274); 5 Incorporación a proyectos de investigación (1280); 6 Incorporación a proyectos comunitarios y extensionistas (1296); 7 Resumen de los premios obtenidos (1317); 8 Actividad de postgrado (1371); 9 Postgrados y acreditación (1381); 10 Resultados de los ejercicios integradores (1396); 11 Resumen promoción, eficiencia, retención (1409). Las ubicaciones corresponden al Manual, líneas indicadas.
14. **Dejar los atributos de `ModeloCampo` para el Plan 09.** Ninguna fuente define `tipo_valor` ni `orden`, e `items` está vacío en `modelos_resumen.json`. No se cargan `fila`, `columna`, `tipo_valor` ni `orden` en este incremento y no bloquean la carga. Las tablas del Manual (líneas 1234–1409) quedan como insumo para el Plan 09 (cuantitativos).
15. **Registrar las asociaciones criterio–modelo según las referencias del catálogo.** Son 20 criterios con `modelos_manual` no vacío y 22 asociaciones tras separar las referencias múltiples.
16. **No poblar `TipoEvidencia` en este incremento.** El JSON no contiene una lista por dimensión y el Manual no define naturaleza ni soporte por elemento. No se crea esta entidad ni bloquea la carga en este incremento.
17. **Tratar `codificacionFuente` sin corregir otros datos.** El carácter `?` es literal y es el único caso en ambos JSON; el escaneo no encuentra U+FFFD ni mojibake. El campo no alimenta ningún modelo. En la tarea 4.3 se corrige a `decodificación estricta`.
18. **Ubicar la Guía en la fuente normativa existente.** La Guía es el Anexo II de `Resolución No.36-2024 SEA-CU.md` (líneas aproximadas 251–444); no existe un archivo de Guía aparte.

## Risks / Trade-offs

- [El JSON no contiene todos los atributos obligatorios de los modelos, incluidos el código del Manual y el texto de indicador] → No inferir valores; mantener las asignaciones exactas visibles y no presentar suposiciones como datos de fuente.
- [Faltan valores obligatorios del ORM en los datos actuales] → No declarar completa la carga del catálogo hasta resolver las fuentes; probar que el comando se detenga antes de cualquier mutación.
- [El JSON y las fuentes muestran posibles códigos distintos para 4.4.4 y 5.2.4–5.2.6] → Conservar los datos originales hasta que el cotejo por criterio establezca la correspondencia; registrar ambos valores y las ubicaciones de fuente.
- [Los identificadores de modelo están confirmados, pero los campos de los modelos están pendientes] → No inventar campos; dejar el contenido de `items` vacío y reservar esos atributos para el plan correspondiente.
- [La opción de catálogo público en desarrollo podría habilitarse por error en producción] → Mantenerla apagada por defecto y rechazarla en la configuración de producción; probar ambas rutas de configuración.
- [El comportamiento del backend puede variar entre motores de base de datos] → Ejecutar las pruebas de modelos, carga y API solo en SQLite, según D-14.

## Migration Plan

1. No se planifica una migración de modelos; confirmar el estado de migraciones existente y construir el cargador sobre el esquema actual.
2. Validar los documentos fuente y los totales esperados antes de modificar datos; completar los valores obligatorios solo con respaldo directo y ejecutar la carga en SQLite en una transacción repetible.
3. Verificar primera carga, recarga, entrada inválida, conservación de versión, comportamiento de endpoints y pruebas de interfaz.
4. Una carga rechazada o fallida no deja registros parciales porque valida antes de mutar y se ejecuta transaccionalmente. Una fuente corregida con respaldo puede cargarse sin cambiar las referencias de versión de los ciclos.

## Open Questions

- Confirmación del tutor sobre la fecha de aprobación (2024-04-29).
- Cómo representar “M7 (7.1)”: el catálogo lo cita, `modelos_resumen.json` no tiene un 7.1 separado y el Manual tiene una tabla 7.1 (`Manual:1342`). Propuesta: asociar a M7 conservando “7.1” como calificador si `CriterioModelo` lo permite; si no, consultarlo.
- Numeración desplazada 3.3/3.4: la Guía no trae 3.3 y su 3.4 tiene el texto que el Manual da al 3.3 (`Manual:478` y `484`; `Guía:368`). Se resuelve en 4.2.
- Conflictos de numeración 4.4.4 y 5.2.4–5.2.6 (4.2).
- La Resolución presenta 10 modelos y el Manual 11 con numeración distinta; verificar en 4.2 que `modelos_manual` y los 11 identificadores siguen la numeración del Manual.
- `TipoEvidencia`: naturaleza y soporte, para el incremento de evidencias.
- Campos de `ModeloCampo`, para el Plan 09.
