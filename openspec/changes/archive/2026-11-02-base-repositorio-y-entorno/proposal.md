# Proposal

## Why

El repositorio actual contiene la documentación de planificación, pero todavía no proporciona una base ejecutable que otra persona pueda instalar desde cero y arrancar en el entorno Windows objetivo. Este incremento establece esa base antes de que los módulos de dominio dependan de una estructura, configuración y flujo de instalación concretos.

## What Changes

- Crear la estructura monorepo prevista para Django/DRF y React/Vite, con las once apps de backend registradas, catálogo y definición de modelos versionados, documentación y exclusiones de archivos generados o locales.
- Incluir el modelo propio mínimo `Usuario` en `cuentas` y su presencia en la migración inicial, antes de cualquier otra migración.
- Documentar la instalación y el arranque desde cero; fijar dependencias y añadir scripts para preparar e instalar paquetes sin conexión desde `almacen/`.
- Separar configuración de desarrollo (SQLite) y producción (PostgreSQL), con selección por `DJANGO_SETTINGS_MODULE`, secretos y conexión por variables de entorno, registro de errores rotativo y almacenamiento de evidencias fuera del contenido público.
- Añadir un prototipo aislado de generación DOCX para validar estilos, tabla y salto de sección, registrando el resultado observado.
- Registrar las decisiones D-01 a D-18 y el avance del incremento; mantener el flujo de trabajo de una rama por incremento.
- No implementar otros modelos de dominio, API ni pantallas de los planes 01 a 12, ni despliegue de producción.

## Capabilities

### New Capabilities

- `project-bootstrap`: estructura del repositorio y flujo documentado para instalar y arrancar el proyecto, incluida la preparación sin conexión.
- `runtime-configuration`: configuración de ejecución por entorno, base de datos, secretos, logs y ubicación protegida de archivos.
- `docx-generation`: prototipo verificable de generación de documentos DOCX requerido para validar la biblioteca y el formato inicial.
- `user-identity`: modelo de usuario propio requerido por Django antes de crear la migración inicial, sin incluir autenticación ni gestión de roles.

### Modified Capabilities

Ninguna. El directorio `openspec/specs/` no contiene capacidades existentes.

## Impact

- Nuevos directorios y archivos bajo `sistema/` según el plan de origen, junto con scripts de PowerShell y shell, dependencias de Python/Node y documentación.
- Configuración Django, registro de las apps previstas y modelo propio de usuario inicial; no se añaden todavía endpoints, gestión de roles ni otros comportamientos de negocio.
- El modelo `Usuario` se incluye en el incremento 0 para que exista en la migración inicial, aunque el plan de origen lo asigna al plan 05; la autenticación y la gestión de roles siguen fuera de alcance.
- Las decisiones D-01 a D-18 se documentarán a partir de la sección 5 de `docs/condiciones-incremento-0(seccion 5).md`; el catálogo SEA-CU 2025 v3 se tomará de `docs/Catálogo SEA-CU 2025 — criterios, evidencias y valoración v3 - Untitled.csv`. El CSV presenta caracteres acentuados que parecen mal decodificados; su codificación debe validarse antes de transformar los datos, sin corregir texto por conjetura. Sus recuentos observados son 6 dimensiones, 24 indicadores y 65 criterios.
- El entorno indicado es Python 3.12.16, Node v24.22.1, npm 11.19.1 y Git 2.56.0. El entorno virtual será `.venv`, creado con `uv venv --python 3.12`; el README debe documentar y permitir verificar su preparación.
- La validación de backend de este incremento ejecuta migraciones y pruebas en SQLite. PostgreSQL sigue siendo el gestor de producción según D-14; las pruebas contra una instancia real quedan pendientes hasta disponer del servidor del cliente o una instalación local, no bloquean el cierre de este incremento y no se registrarán como ejecutadas antes de realizarlas.
