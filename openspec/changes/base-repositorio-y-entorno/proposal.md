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
- La fuente indicada para el contenido completo de las decisiones («Condiciones para iniciar el incremento 0», sección 5) no está presente en la documentación disponible. Durante la implementación habrá que localizarla; no se deben inventar alternativas o consecuencias que no estén en la fuente.
- La disponibilidad de Python, Node.js, npm y Git en el portátil no se ha verificado. La instalación debe comprobarse en el entorno objetivo y dejar constancia de cualquier diferencia.
