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
- Fijar datos de despliegue, credenciales o reglas de autorización no definidas en las fuentes disponibles.

## Decisions

1. **Mantener un monorepo con el producto bajo `sistema/`.** La estructura separará `backend/`, `frontend/`, `datos/`, `docs/`, `almacen/` y scripts del proyecto. Se conserva `docs/origin-plans/` en la raíz como documentación de origen. Se prefiere un solo repositorio a repositorios separados porque D-17 exige repositorio único y rama por incremento.
2. **Componer los ajustes Django desde módulos por entorno.** `base.py` contendrá valores compartidos; `desarrollo.py` y `produccion.py` configurarán sus respectivas bases de datos. `DJANGO_SETTINGS_MODULE` seleccionará el módulo. La configuración de producción leerá secretos y conexión de variables de entorno; `.env.ejemplo` documentará nombres y valores de ejemplo sin incluir secretos reales. Se prefiere esto a un único módulo con condicionales dispersos para hacer verificables las diferencias de entorno.
3. **Mantener el flujo local sin servicios de virtualización.** Django y Vite se iniciarán con sus servidores de desarrollo en procesos separados. La interfaz usará el servidor de Vite en vez de exigir una compilación completa, acorde con las limitaciones de rendimiento y la restricción de Node.js al desarrollo.
4. **Preparar paquetes para instalación offline con versiones fijadas.** `pip download` llenará el almacén local para backend; npm preparará su caché bajo `almacen/` usando el lockfile. Los scripts de instalación usarán exclusivamente los recursos locales cuando se solicite el modo sin conexión. Se prefiere este flujo a depender de descargas durante la instalación porque el equipo objetivo puede no tener red.
5. **Crear las once apps, con una excepción mínima para identidad.** Las apps se registrarán como estructura, sin lógica de negocio, salvo `cuentas.Usuario`: heredará de `AbstractBaseUser` y `PermissionsMixin` para conservar los campos de dominio exactos (`username`, `nombre`, `apellidos`, `email`, `activo`) sin duplicar los campos en inglés de `AbstractUser`. Tendrá el campo de compatibilidad necesario para Django Admin, una propiedad `is_active` ligada a `activo` y un manager que permita crear usuarios y superusuarios. `AUTH_USER_MODEL` apuntará a ese modelo antes de generar la migración inicial, que deberá incluirlo. Se prefiere esta opción a `AbstractUser` simplificado para respetar los nombres de dominio; no se añadirán roles, endpoints ni interfaces de cuentas. Esta decisión ubica `Usuario` en el incremento 0 por requisito de la primera migración y prevalece sobre la asignación al plan 05 que aparece en el documento de origen.
6. **Aislar el prototipo DOCX del módulo de informes.** El prototipo se ubicará en el área de informes del backend y producirá un documento de prueba con el formato de la especificación. La prueba en Word o LibreOffice y su resultado se registrarán en el avance del incremento; no se incluirá generación de informes de negocio.
7. **Tratar el contenido fuente de decisiones como requisito de trazabilidad.** Las fichas D-01 a D-18 se basarán en la sección 5 de `docs/condiciones-incremento-0(seccion 5).md`; las alternativas, decisiones y estados seguirán esa fuente, sin ampliar su contenido mediante suposiciones.
8. **Fijar las versiones del entorno local de desarrollo.** El entorno usa Python 3.12.16, Node v24.22.1, npm 11.19.1 y Git 2.56.0. El entorno virtual se llama `.venv` y se crea con `uv venv --python 3.12`. Se registran estas versiones y el comando para que la instalación documentada y verificada sea reproducible.
9. **Aplicar D-14 a la validación del incremento 0.** SQLite es el entorno de desarrollo y el gestor para migraciones y pruebas backend de este incremento. PostgreSQL se utiliza en producción, al instalar el sistema en el servidor del cliente. La verificación contra PostgreSQL real queda para cuando haya una instancia del cliente o una instalación local disponible; no es requisito para cerrar este incremento y no se registra como ejecutada antes de realizarla.

## Risks / Trade-offs

- [La caché npm no contendrá artefactos compatibles con el entorno o lockfile utilizado] → Prepararla con el lockfile del proyecto, comprobar una instalación con red desactivada y registrar las versiones de Node/npm que se validaron.
- [Las comprobaciones de producción dependen de valores propios del futuro servidor] → Leerlos de variables de entorno, mantener `DEBUG=False` y validar `check --deploy` con valores de prueba explícitos, sin consignar secretos.
- [El modelo de usuario se registre después de la primera migración] → Crear y registrar `cuentas.Usuario` y configurar `AUTH_USER_MODEL` antes de generar o ejecutar la migración inicial; comprobar en pruebas que el modelo aparece en esa migración.
- [El entorno de ejecución puede diferir de las versiones fijadas] → Comprobar las versiones de Python, Node.js, npm y Git durante la instalación y anotar discrepancias en el avance en vez de afirmar una validación no ejecutada.
- [La fuente CSV puede contener texto con codificación mal interpretada] → Validar su codificación antes de transformar los datos; si no se puede recuperar con certeza el texto correcto, documentar la discrepancia y no corregirlo por conjetura.
- [SQLite es más permisivo que PostgreSQL] → Las migraciones y restricciones que pasan en SQLite pueden fallar al desplegar en PostgreSQL. La verificación contra PostgreSQL real queda pendiente hasta disponer de una instancia del cliente o local; registrar cualquier resultado solo después de ejecutarla.

## Migration Plan

No hay migración de datos ni despliegue de una aplicación existente. Implementar por etapas: crear primero la estructura y el entorno de desarrollo; añadir después la configuración por entorno y los archivos de dependencias; validar instalación y arranque desde cero y sin red; ejecutar las migraciones iniciales y pruebas backend en SQLite; la verificación contra PostgreSQL real queda pendiente hasta disponer de una instancia y no bloquea el cierre de este incremento. No registrar esa verificación como ejecutada si no se hizo; finalmente probar el prototipo DOCX y registrar los resultados. Si una etapa rompe el arranque, corregirla antes de continuar; no se requiere una estrategia de reversión de datos.

## Open Questions

- ¿Qué modelo resumen de los once se usará como contenido de ejemplo para la tabla DOCX? Se elegirá cuando la definición versionada de esos modelos esté disponible; no cambia el formato requerido.
