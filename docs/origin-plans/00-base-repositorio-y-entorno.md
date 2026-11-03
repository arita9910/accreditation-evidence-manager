# Plan 00 — Base: repositorio, entorno y configuración (incremento 0)

## Objetivo
Dejar un repositorio que se instala desde cero con un README, arranca backend y frontend, y tiene la configuración por entornos, el registro de errores, el registro de decisiones y el prototipo de descarte del informe .docx.

## Contexto mínimo
- Sistema: gestión de evidencias de la autoevaluación SEA-CU 2025 (ver README-indice).
- Stack: Python 3.10+, Django 5.2 LTS, Django REST Framework, python-docx; React 18 + Vite (JavaScript), React Router, Bootstrap local, Vitest + Testing Library. SQLite en desarrollo; PostgreSQL en producción (psycopg).
- Equipo de desarrollo: portátil Windows 10, 8 GB, sin virtualización (no Docker, no WSL2). Node.js solo en desarrollo. Compilar el frontend es lento: usar el servidor de desarrollo de Vite.
- Instalación sin conexión a internet debe ser posible (paquetes en `almacen/`, fuera de Git).

## Entregables y tareas

### T1 — Estructura del repositorio (historia 0.1)
Crear dentro del repositorio existente:
```
sistema/
  backend/          Django + DRF: config/ y una app por módulo
                    (nucleo, estructura, ciclos, cuentas, auditoria, evidencias,
                     valoracion, cuantitativos, mejora, analisis, informes)
  frontend/         React 18 (Vite): src/api, src/componentes, src/paginas
  datos/            catalogo_sea_cu_2025.json (v3) y definición de los 11 modelos
  docs/             decisiones/, modelo-de-datos/, manuales/, avance/
  almacen/          paquetes sin conexión (pip y npm); en .gitignore
  README.md         instalación desde cero, paso a paso
```
- Crear las 11 apps de Django vacías (con `apps.py` y `__init__.py`), registradas en `INSTALLED_APPS`.
- `.gitignore` para Python, Node, `almacen/`, `media/` y bases de datos locales.
- **Aceptación:** un tercero sigue el README en un entorno limpio y arranca backend y frontend.

### T2 — Configuración por entornos (historia 0.2)
- Ajustes separados: `config/ajustes/base.py`, `desarrollo.py` (SQLite) y `produccion.py` (PostgreSQL; datos de conexión y `SECRET_KEY` por variables de entorno; `DEBUG=False`).
- Selección con la variable `DJANGO_SETTINGS_MODULE`; ejemplo en `.env.ejemplo`.
- Registro de errores en fichero con rotación (`logs/`), fuera de Git.
- `AUTH_USER_MODEL` apuntando al modelo propio (se crea en el plan 05, tarea de la historia 0.3; coordinar: el modelo debe existir antes de la primera migración).
- `MEDIA_ROOT`/carpeta de evidencias configurable, **fuera de la parte pública**.
- **Aceptación:** arranca en desarrollo; `python manage.py check --deploy` pasa con los ajustes de producción.

### T3 — Dependencias y almacén sin conexión (D-16)
- `backend/requirements.txt` con versiones fijas (Django 5.2.x, djangorestframework, python-docx, psycopg para producción, drf-spectacular opcional para OpenAPI — D-18).
- `frontend/package.json` y `package-lock.json` (React 18, React Router, Vite, Bootstrap, Vitest, Testing Library).
- Scripts `scripts/descargar_paquetes.(ps1|sh)` que llenan `almacen/` con `pip download` y la caché de npm, y `scripts/instalar_sin_conexion.(ps1|sh)`.
- **Aceptación:** con `almacen/` lleno y sin red, el README permite instalar todo.

### T4 — Prototipo de descarte del .docx (historia 0.8)
- Script `backend/informes/prototipo_docx.py` (aislado; se reutilizará en el plan 12): documento con python-docx en Arial 12, interlineado sencillo, una tabla (como un modelo resumen), un salto de sección.
- **Aceptación:** el fichero se abre bien en Word o LibreOffice. Anotar en `docs/avance/00-base.md` qué falla, si algo falla.

### T5 — Registro de decisiones (historia 0.10)
- Crear en `docs/decisiones/` una ficha por decisión D-01 a D-18 con: problema, alternativas, decisión, justificación, consecuencias, estado (confirmada o propuesta). El texto de cada decisión está en el documento «Condiciones para iniciar el incremento 0», sección 5; copiar sin cambiar su sentido. Resumen:
  D-01 modelo de usuario propio · D-02 dos entidades Indicador y Criterio · D-03 catálogo y modelos como ficheros versionados · D-04 los 11 modelos como celdas genéricas · D-05 datos cuantitativos solo en modelos resumen (confirmada) · D-06 autorización con función propia · D-07 auditoría de solo inserción · D-08 búsqueda solo en metadatos (confirmada) · D-09 entrega de ficheros por Nginx en producción · D-10 aviso de 50 páginas con LibreOffice si existe · D-11 reemplazar fichero = versión nueva · D-12 arquitectura desacoplada (confirmada) · D-13 sesión + CSRF · D-14 SQLite en desarrollo, PostgreSQL en producción (confirmada; interpretación pendiente) · D-15 Vite/JS/Router/Bootstrap/Vitest · D-16 paquetes sin conexión · D-17 repo único, rama por incremento · D-18 OpenAPI opcional.

### T6 — Rama y flujo
- Rama principal siempre funcional; una rama por incremento (`incremento-0`, …). Commits claros.

## Fuera de alcance
Modelos de dominio, API y pantallas (planes 01 a 12). Despliegue en el servidor (más adelante; faltan datos de informática).

## Definición de terminado
Repositorio con la estructura, README verificado, ajustes por entornos, registro de decisiones, prototipo .docx probado, `check --deploy` pasando. Párrafo de avance en `docs/avance/00-base.md`.
