# Tasks

## 1. Carga y validación del catálogo

- [x] 1.1 Implementar un lector del JSON existente que valide sus claves anidadas, extraiga el código/orden de las dimensiones solo si coincide con el prefijo observado y compruebe 6/24/65; verificar con pruebas del formato real y fixtures de estructura/totales inválidos.
- [x] 1.2 Implementar `cargar_catalogo` para cargar o actualizar por claves naturales, preservar referencias de versión de ciclos existentes y ejecutar la escritura en una transacción; verificar en SQLite con una fixture fuente-completa que dos cargas no duplican y que un error revierte la operación.
- [x] 1.3 Mapear únicamente valores respaldados por el JSON y `modelos_resumen.json`, incluidas evidencias, requisitos y referencias de modelo; verificar en SQLite, con una fixture completa, que 3.2.4 queda marcado solo en la Guía y se crean las asociaciones de modelo esperadas (20 criterios con modelo y 22 asociaciones). Aclarar y verificar que en este incremento no se crean `TipoEvidencia` ni `ModeloCampo`.
- [x] 1.4 Con una fixture del catálogo a la que le falten campos obligatorios (no el JSON real, que quedará completo tras 4.3), verificar que el comando informa qué campos faltan y se detiene sin crear registros; comprobar también que `TipoEvidencia` y `ModeloCampo` no se crean.

## 2. API de consulta

- [x] 2.1 Añadir los servicios, serializadores y rutas de solo lectura para árbol, ficha de criterio, modelos y versiones; verificar con pruebas SQLite que la respuesta del árbol contiene 6/24/65 y que la ficha devuelve 404 estándar para un código inexistente y los datos de referencia para uno existente.
- [x] 2.2 Restringir la exposición al ajuste de desarrollo, apagado por defecto y rechazado en producción; verificar que la configuración por defecto no expone el catálogo, que el desarrollo habilitado permite GET y que las escrituras devuelven 405.

## 3. Interfaz de consulta

- [x] 3.1 Implementar el árbol colapsable con búsqueda por código o texto y marcas de tipo de dato/solo en la Guía, consumiendo la API mediante `src/api/cliente.js`; verificar con Vitest el árbol de seis dimensiones, búsqueda y marca de 3.2.4.
- [x] 3.2 Implementar la ruta y ficha de criterio con evidencias, requisitos por categoría como referencia, aviso de que no se calcula la categoría, nota y modelos relacionados; verificar con Vitest la navegación y los estados de carga/error.

## 4. T4 — Cotejo del catálogo

- [x] 4.1 Crear `sistema/docs/decisiones/03-estructura.md` con las preguntas abiertas de `design.md`, `sistema/docs/avance/03-estructura.md` con el estado del incremento y los bloqueos, y `sistema/docs/avance/03-cotejo-catalogo.md` vacío con encabezado; verificar que los documentos existen y no presentan como confirmados valores pendientes.
- [x] 4.2 Cotejar, buscando cada criterio por separado en el Manual 2025 y la Guía de `docs/fuentes/`, al menos 12 criterios distintos: 3.2.1–3.2.3, 2.2.1, 2.4.2, al menos tres con requisito por categoría, criterios 3.3.x y 3.4.x, 4.4.4 y 5.2.4–5.2.6. La Guía está en el Anexo II de `Resolución No.36-2024 SEA-CU.md` (líneas aproximadas 251–444), no en un archivo aparte. Incluir el desplazamiento de numeración: la Guía no trae 3.3 y su 3.4 tiene el texto que el Manual da al 3.3 (Manual:478 y 484; Guía:368). Escribir la tabla de cotejo en `sistema/docs/avance/03-cotejo-catalogo.md` con campo, valor del dato, valor de cada fuente, ubicación y estado para cada criterio comparado; verificar que incluya las fuentes y líneas cotejadas.
- [ ] 4.3 Completar los valores obligatorios autorizados por la tesista y respaldados con fuente y línea: en `catalogo_sea_cu_2025.json`, agregar `fecha_aprobacion` y `texto` de los 24 indicadores; en `modelos_resumen.json`, agregar `nombre.valor` de los 11 modelos. Mantener `codigo_manual` sin modificar, incluidos 4.4.4 y 5.2.4–5.2.6, y conservar `codificacionFuente` fuera del alcance autorizado. Registrar cada valor y ubicación en `sistema/docs/avance/03-cotejo-catalogo.md`. Verificar JSON válido en UTF-8 estricto, totales 6/24/65, texto en los 24 indicadores, nombre en los 11 modelos y escaneo de `\w\?`, `\?\w`, U+FFFD y mojibake sin casos nuevos.
- [ ] 4.4 Corregir el catálogo solo con evidencia directa; verificar la carga real mediante `cargar_catalogo` sobre el JSON real en SQLite (6/24/65, 11 modelos, 22 asociaciones y una segunda carga sin duplicados) y completar el reporte de avance. Si algún valor obligatorio sigue sin respaldo, dejar el cargador y el cotejo pendientes con la causa documentada y no marcar el cotejo como hecho.
