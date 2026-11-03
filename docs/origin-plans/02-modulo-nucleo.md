# Plan 02 — Módulo núcleo (incremento 0)

## Objetivo
Entregar lo que comparten todos los módulos: modelo base, servicio de almacenamiento de ficheros, utilidades de API y la plantilla base del frontend con el cliente de la API.

## Convenciones comunes (valen en todos los planes)
- Stack: Django 5.2, DRF, React 18 + Vite (JS), React Router, Bootstrap local, Vitest + Testing Library. SQLite en desarrollo, PostgreSQL en producción; sin SQL propio de un gestor.
- Código y nombres en español (PEP 8). Una app de Django por módulo en `sistema/backend/<modulo>/`, con `modelos.py`, `servicios.py`, `serializadores.py`, `vistas.py`, `urls.py`, `tests/`.
- La lógica de negocio va en `servicios.py`. Las vistas de la API solo validan, comprueban permisos y delegan.
- Todo acceso va por la API bajo `/api/` (JSON, sesión de Django + CSRF). El frontend nunca toca la base de datos ni el disco.
- Permisos solo mediante `cuentas.permisos.puede(usuario, accion, objeto)` (cuando exista) y la clase de permisos de DRF que la invoca.
- Terminología: indicador = 2.º nivel (24); criterio = 3.er nivel (65).
- Si algo es ambiguo, no inventar: anotar en `docs/decisiones/` y seguir con lo demás.

## Contexto
Historia 0.4 y parte de la 0.7 del incremento 0. Depende del plan 00 (estructura y ajustes).

## Tareas

### T1 — Modelo base
- Clase abstracta `ModeloBase` en `nucleo/modelos.py`: `creado_en`, `modificado_en` (automáticos), `creado_por`, `modificado_por` (FK nulas a `AUTH_USER_MODEL`, `PROTECT`).
- Mixin/servicio que rellena `creado_por`/`modificado_por` desde el usuario de la petición (en el serializador o en un middleware sencillo; documentar la elección).
- **Aceptación:** una prueba con un modelo de prueba comprueba los cuatro campos.

### T2 — Servicio de almacenamiento (`nucleo/almacenamiento.py`)
- `guardar_fichero(archivo, subcarpeta) -> {nombre_interno, ruta_relativa, tamano, sha256}`: nombre interno = UUID + extensión original saneada; escribe en la carpeta de evidencias configurada (`EVIDENCIAS_ROOT`), **fuera de la parte pública**; calcula SHA-256 en streaming por bloques.
- `abrir_fichero(ruta_relativa)`, `calcular_sha256(ruta)`, `verificar_huella(ruta, sha256) -> bool`, `borrar_fichero` (solo para pruebas/limpieza de huérfanos; no se usa en operaciones normales).
- Rechazar rutas con `..` o absolutas (path traversal).
- **Aceptación (pruebas):** nombre único en dos cargas del mismo fichero; huella igual a `hashlib.sha256` del contenido; la ruta resuelta queda dentro de `EVIDENCIAS_ROOT` y fuera de `STATIC_ROOT`/`MEDIA_ROOT` públicos; path traversal rechazado; un fichero alterado en disco hace fallar `verificar_huella`.

### T3 — Utilidades de API
- Paginación estándar (`PageNumberPagination`, tamaño configurable).
- Manejador de excepciones de DRF que devuelve `{"codigo": "...", "mensaje": "...", "detalle": ...}` en español.
- Vista `GET /api/salud/` (sin autenticación) que responde `{"estado": "ok"}`.
- Esquema OpenAPI opcional (drf-spectacular) en `/api/esquema/` solo en desarrollo (D-18).
- **Aceptación:** pruebas de formato de error y de paginación.

### T4 — Frontend: plantilla base
- `frontend/src/api/cliente.js`: `fetch` con `credentials: 'same-origin'`, lectura del token CSRF de la cookie `csrftoken` y envío en `X-CSRFToken` en peticiones que escriben; manejo central de errores con el formato del servidor; proxy de Vite hacia `http://localhost:8000` para `/api` en desarrollo.
- `frontend/src/componentes/`: `Diseno` (barra superior, navegación, contenedor), `Mensaje` (errores/avisos), `Cargando`.
- Router (React Router) con rutas protegidas preparadas (hasta el incremento 1 no hay login: la protección se activa cuando exista `/api/cuentas/yo/`).
- Bootstrap instalado localmente (sin CDN).
- **Aceptación (Vitest):** el cliente envía el token CSRF en POST; un error de la API se muestra con `Mensaje`.

## Fuera de alcance
Autenticación y permisos (plan 05), pantallas del catálogo (plan 03), auditoría (plan 06).

## Definición de terminado
Pruebas del núcleo en verde (backend y frontend), servicio de almacenamiento usable por el plan 07, avance en `docs/avance/02-nucleo.md`.
