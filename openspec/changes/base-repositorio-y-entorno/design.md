# Design

## Context

El repositorio actualmente contiene el README inicial y planes de implementación bajo `docs/origin-plans/`, sin código de aplicación ni capacidades OpenSpec previas. El plan de origen define `sistema/` como raíz del producto y fija como entorno de desarrollo un portátil Windows 10 de 8 GB sin Docker ni WSL2. Véase [proposal.md](./proposal.md) para motivación y alcance, y los deltas de especificación para los contratos observables.

## Goals / Non-Goals

**Goals:**
- Construir una base instalable y ejecutable que respete las restricciones de plataforma y permita añadir los módulos posteriores sin reorganizar el repositorio.
- Mantener una vía offline reproducible para las dependencias de Python y npm.
- Comprobar el formato DOCX en un prototipo aislado antes de integrarlo con el módulo de informes.

**Non-Goals:**
- Introducir virtualización, un servidor de producción o una arquitectura de despliegue no especificada.
- Implementar modelos de dominio distintos del `Usuario` mínimo requerido para la migración inicial, o añadir autenticación, roles, endpoints y pantallas de cuentas.
- Fijar datos de despliegue, credenciales, reglas de autorización o contenido de decisiones ausente en las fuentes disponibles.

## Decisions

1. **Mantener un monorepo con el producto bajo `sistema/`.** La estructura separará `backend/`, `frontend/`, `datos/`, `docs/`, `almacen/` y scripts del proyecto. Se conserva `docs/origin-plans/` en la raíz como documentación de origen. Se prefiere un solo repositorio a repositorios separados porque D-17 exige repositorio único y rama por incremento.
2. **Componer los ajustes Django desde módulos por entorno.** `base.py` contendrá valores compartidos; `desarrollo.py` y `produccion.py` configurarán sus respectivas bases de datos. `DJANGO_SETTINGS_MODULE` seleccionará el módulo. La configuración de producción leerá secretos y conexión de variables de entorno; `.env.ejemplo` documentará nombres y valores de ejemplo sin incluir secretos reales. Se prefiere esto a un único módulo con condicionales dispersos para hacer verificables las diferencias de entorno.
3. **Mantener el flujo local sin servicios de virtualización.** Django y Vite se iniciarán con sus servidores de desarrollo en procesos separados. La interfaz usará el servidor de Vite en vez de exigir una compilación completa, acorde con las limitaciones de rendimiento y la restricción de Node.js al desarrollo.
4. **Preparar paquetes para instalación offline con versiones fijadas.** `pip download` llenará el almacén local para backend; npm preparará su caché bajo `almacen/` usando el lockfile. Los scripts de instalación usarán exclusivamente los recursos locales cuando se solicite el modo sin conexión. Se prefiere este flujo a depender de descargas durante la instalación porque el equipo objetivo puede no tener red.
5. **Crear las once apps, con una excepción mínima para identidad.** Las apps se registrarán como estructura, sin lógica de negocio, salvo `cuentas.Usuario`: heredará de `AbstractBaseUser` y `PermissionsMixin` para conservar los campos de dominio exactos (`username`, `nombre`, `apellidos`, `email`, `activo`) sin duplicar los campos en inglés de `AbstractUser`. Tendrá el campo de compatibilidad necesario para Django Admin, una propiedad `is_active` ligada a `activo` y un manager que permita crear usuarios y superusuarios. `AUTH_USER_MODEL` apuntará a ese modelo antes de generar la migración inicial, que deberá incluirlo. Se prefiere esta opción a `AbstractUser` simplificado para respetar los nombres de dominio; no se añadirán roles, endpoints ni interfaces de cuentas.
6. **Aislar el prototipo DOCX del módulo de informes.** El prototipo se ubicará en el área de informes del backend y producirá un documento de prueba con el formato de la especificación. La prueba en Word o LibreOffice y su resultado se registrarán en el avance del incremento; no se incluirá generación de informes de negocio.
7. **Tratar el contenido fuente de decisiones como requisito de trazabilidad.** Se crearán fichas D-01 a D-18, pero las alternativas, justificaciones y consecuencias se transcribirán de la sección 5 del documento fuente cuando esté disponible. La lista resumida del plan no se ampliará mediante suposiciones.

## Risks / Trade-offs

- [La caché npm no contendrá artefactos compatibles con el entorno o lockfile utilizado] → Prepararla con el lockfile del proyecto, comprobar una instalación con red desactivada y registrar las versiones de Node/npm que se validaron.
- [Las comprobaciones de producción dependen de valores propios del futuro servidor] → Leerlos de variables de entorno, mantener `DEBUG=False` y validar `check --deploy` con valores de prueba explícitos, sin consignar secretos.
- [El modelo de usuario se registre después de la primera migración] → Crear y registrar `cuentas.Usuario` y configurar `AUTH_USER_MODEL` antes de generar o ejecutar la migración inicial; comprobar en pruebas que el modelo aparece en esa migración.
- [El documento fuente de decisiones no está presente en los archivos inspeccionados] → Localizarlo antes de completar las fichas; no completar contenido faltante a partir de títulos resumidos.
- [El portátil puede tener versiones de herramientas distintas de las esperadas] → Comprobar Python, Node.js, npm y Git durante la instalación y anotar discrepancias en el avance en vez de afirmar una validación no ejecutada.

## Migration Plan

No hay migración de datos ni despliegue de una aplicación existente. Implementar por etapas: crear primero la estructura y el entorno de desarrollo; añadir después la configuración por entorno y los archivos de dependencias; validar instalación y arranque desde cero y sin red; finalmente probar el prototipo DOCX y registrar los resultados. Si una etapa rompe el arranque, corregirla antes de continuar; no se requiere una estrategia de reversión de datos.

## Open Questions

- ¿Qué versión concreta de Python, Node.js, npm y Git está instalada en el portátil objetivo? Se resolverá durante la prueba del README y se documentará; no cambia el stack acordado.
- ¿Qué modelo resumen de los once se usará como contenido de ejemplo para la tabla DOCX? Se elegirá cuando la definición versionada de esos modelos esté disponible; no cambia el formato requerido.
