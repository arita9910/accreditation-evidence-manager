# Plan 03 — Módulo estructura: catálogo SEA-CU 2025 (incremento 0)

## Objetivo
Cargar el catálogo normativo versionado desde un fichero de datos, exponerlo por una API de solo lectura y mostrarlo en el frontend como árbol dimensión → indicador → criterio con la ficha de cada criterio.

## Convenciones comunes
- Stack: Django 5.2 + DRF; React 18 + Vite (JS); SQLite en desarrollo, PostgreSQL en producción; sin SQL propio de un gestor.
- Nombres en español (PEP 8). App `sistema/backend/estructura/` con `modelos.py`, `servicios.py`, `serializadores.py`, `vistas.py`, `urls.py`, `tests/`. Lógica en servicios; vistas delgadas.
- API bajo `/api/`, JSON, sesión + CSRF. El frontend solo consume la API.
- Terminología: indicador = 2.º nivel (24); criterio = 3.er nivel (65).
- Ambigüedad → anotar en `docs/decisiones/`, no inventar.

## Contexto
Historias 0.5, 0.6, 0.7 (parte catálogo) y 0.9. Depende de: plan 01 oleada A (modelos de estructura), plan 02 (modelo base, cliente de la API).
Fuente de datos: `sistema/datos/catalogo_sea_cu_2025.json` (versión 3, 1 nov 2026): totales {6 dimensiones, 24 indicadores, 65 criterios, 1 criterio solo en la Guía}. Campos por criterio: `codigo`, `texto`, `codigo_manual`, `codigo_guia`, `solo_en_guia`, `tipo_dato`, `modelos_manual`, `valoracion_por_categoria`, `nota_normativa`, y las evidencias y requisitos de la Guía. También hay `.csv`. **Primero inspeccionar la estructura real del JSON** y adaptar el cargador; no asumir nombres de campos que no estén.

## Entidades (plan 01, oleada A)
VersionNormativa, Dimension, Indicador, Criterio, EvidenciaSugerida, RequisitoCategoria, TipoEvidencia, ModeloDefinicion, ModeloCampo, CriterioModelo. Atributos y reglas: ver `01-modelo-de-datos.md`. Los 11 modelos resumen se cargan desde un fichero de datos propio (`sistema/datos/modelos_resumen.json`); si no existe todavía, crearlo con la definición de número, nombre y (cuando se tenga) celdas, y marcar las celdas pendientes como tarea abierta (D-04).

## Tareas

### T1 — Orden `cargar_catalogo` (historia 0.5)
- Orden de gestión `python manage.py cargar_catalogo [--fichero RUTA] [--version NOMBRE]` repetible (idempotente): crea o actualiza por claves naturales; no duplica al recargar.
- Crea VersionNormativa, 6 Dimension, 24 Indicador, 65 Criterio, EvidenciaSugerida, RequisitoCategoria, TipoEvidencia (lista de evidencias del Manual por dimensión, si están en los datos), ModeloDefinicion, CriterioModelo.
- Comprueba al final los totales 6/24/65 y falla con mensaje claro si no coinciden.
- El 3.2.4 queda con `codigo_manual` nulo y `solo_en_guia=True`; las entrevistas/visitas de la Guía se marcan `es_verificacion_externa=True`.
- Si se carga otra versión, un ciclo existente conserva la suya.
- **Aceptación (pruebas):** exactamente 6/24/65; recargar no duplica; 3.2.4 marcado solo en la Guía; 20 criterios con modelo; el fichero de pruebas incorrecto (totales distintos) hace fallar la orden.

### T2 — API del catálogo (historia 0.6)
Solo lectura (`ReadOnlyModelViewSet`/vistas `GET`). Sin login hasta el incremento 1: los endpoints son accesibles solo si `CATALOGO_PUBLICO_EN_DESARROLLO=True` en ajustes de desarrollo (apagado por defecto y prohibido en producción). Cuando exista el plan 05, pasar a "autenticado".
- `GET /api/catalogo/arbol/` — árbol completo de la versión activa: dimensiones → indicadores → criterios (código, texto resumido, tipo_dato, solo_en_guia).
- `GET /api/catalogo/criterios/{codigo}/` — ficha: texto completo, códigos de Manual y Guía, tipo de dato, evidencias sugeridas, requisito por categoría (solo lectura), nota normativa, modelos relacionados.
- `GET /api/catalogo/modelos/` — los 11 modelos con sus campos.
- `GET /api/catalogo/versiones/` — versiones disponibles.
- **Aceptación:** pruebas de la API: el árbol devuelve 6/24/65; la ficha del 3.2.4 trae `solo_en_guia`; códigos inexistentes dan 404 con el formato de error estándar; los métodos de escritura devuelven 405.

### T3 — Pantallas del catálogo (historia 0.7)
- Página `Catalogo`: árbol colapsable dimensión → indicador → criterio con búsqueda por código o texto, y marca visible en el 3.2.4 («solo en la Guía») y en el tipo de dato.
- Página `FichaCriterio` (`/catalogo/criterios/:codigo`): texto completo, evidencias sugeridas (distinguiendo documentos y verificaciones externas), **requisito de la Guía por categoría como referencia** con el aviso «El sistema no calcula la categoría», nota normativa y modelos relacionados.
- **Aceptación (Vitest):** el árbol muestra 6 dimensiones; la ficha muestra el requisito por categoría y el aviso; el 3.2.4 muestra su marca.

### T4 — Cotejo del catálogo con los PDF (historia 0.9)
- Con los PDF del Manual 2025 y de la Guía (RM 36/2024), comparar al menos 12 criterios: los tres del grupo 3.2, el 2.2.1, el 2.4.2, tres con requisito por categoría y los de numeración distinta entre Manual y Guía (3.2.2, 3.3.x, 3.4.x, 4.4.4, 5.2.4 a 5.2.6).
- Entregar `docs/avance/03-cotejo-catalogo.md` con una tabla (criterio, campo, valor en datos, valor en PDF, estado) y corregir los datos si hay diferencias. Si no se tiene acceso a los PDF, dejarlo documentado como pendiente de Arianne; **no marcarlo como hecho**.

## Fuera de alcance
Edición del catálogo desde la interfaz (CU-03 se hace por la orden de gestión y, más adelante, la interfaz de administración), valores cuantitativos (plan 09), evidencias (plan 07).

## Definición de terminado
`cargar_catalogo` correcto y repetible; API y pantallas probadas; cotejo hecho o declarado pendiente; avance en `docs/avance/03-estructura.md`. Casos de uso: CU-03, CU-06 (consulta).
