# Tasks

## 1. Crear la estructura del monorepo

- [x] 1.1 Crear `sistema/backend/` con el proyecto Django y las once apps `nucleo`, `estructura`, `ciclos`, `cuentas`, `auditoria`, `evidencias`, `valoracion`, `cuantitativos`, `mejora`, `analisis` e `informes`; verificar que cada app tiene `apps.py` y `__init__.py`, y que todas están registradas en `INSTALLED_APPS`.
- [x] 1.2 Crear `sistema/frontend/` con la base React 18/Vite y las carpetas `src/api`, `src/componentes` y `src/paginas`; verificar que el servidor Vite inicia y sirve la página inicial.
- [x] 1.3 Crear las carpetas de documentación, datos, scripts y almacén previstas bajo `sistema/`, y configurar `.gitignore` para Python, Node, almacén local, bases de datos, evidencias y logs; verificar con `git check-ignore` que cada tipo de artefacto local queda excluido.

## 2. Fijar dependencias y preparar la vía sin conexión

- [x] 2.1 Fijar las dependencias de backend y frontend de acuerdo con el stack del plan (Django 5.2.x, DRF, python-docx, psycopg y dependencias React/Vite/Bootstrap/Vitest); verificar la instalación online desde los archivos de dependencias y que existe un lockfile npm reproducible.
- [x] 2.2 Crear los scripts PowerShell y shell para preparar paquetes y caché npm en `almacen/` e instalarlos sin red; documentar esta parte en el README y verificar la instalación desde un almacén preparado con la red desactivada.

## 3. Incorporar el usuario propio antes de migrar

- [x] 3.1 Implementar `cuentas.Usuario` con `username`, `nombre`, `apellidos`, `email` y `activo`, usando almacenamiento seguro de contraseñas y la compatibilidad con Django Admin definida en el diseño; verificar con pruebas la creación de usuarios, contraseña no reversible y comportamiento de usuario activo.
- [x] 3.2 Configurar `AUTH_USER_MODEL` para `cuentas.Usuario`, registrar el modelo en Django Admin y crear la migración inicial antes de cualquier otra migración; verificar desde una base vacía que la migración contiene el modelo y que `createsuperuser` funciona.

## 4. Configurar los entornos y el almacenamiento

- [x] 4.1 Separar los ajustes Django compartidos, de desarrollo y producción, con selección por `DJANGO_SETTINGS_MODULE`, SQLite en desarrollo y PostgreSQL en producción; añadir `.env.ejemplo` sin secretos y pruebas que confirmen la base seleccionada en cada entorno.
- [x] 4.2 Configurar en producción `SECRET_KEY`, parámetros de conexión por variables de entorno y `DEBUG=False`; verificar `python manage.py check --deploy` con valores de prueba y sin guardar credenciales.
- [x] 4.3 Configurar el registro de errores con rotación y la ubicación configurable de evidencias fuera de la parte pública; verificar la rotación y que la ruta de evidencias no queda bajo el directorio servido públicamente ni aparece en Git.

## 5. Versionar catálogo y modelos resumen

- [x] 5.1 Usar `docs/Catálogo SEA-CU 2025 — criterios, evidencias y valoración v3 - Untitled.csv` como fuente del catálogo SEA-CU 2025 v3; verificar su codificación y cotejar los acentos con una fuente autorizada antes de normalizar texto. Crear `sistema/datos/catalogo_sea_cu_2025.json` y comprobar 6 dimensiones, 24 indicadores y 65 criterios; si la codificación o un dato no puede resolverse con certeza, documentar la discrepancia y no corregirlo por conjetura.
- [x] 5.2 Crear `sistema/datos/modelos_resumen.json` con las once definiciones disponibles y las celdas que puedan sustentarse en las fuentes; marcar como pendientes las celdas no disponibles y verificar que hay once modelos identificables y que el archivo distingue datos pendientes de valores confirmados.

## 6. Documentar la instalación y las decisiones

- [x] 6.1 Escribir `sistema/README.md` con requisitos previos y pasos reproducibles para instalar y arrancar backend y frontend en Windows 10 sin Docker/WSL2, incluyendo Python 3.12.16, Node v24.22.1, npm 11.19.1, Git 2.56.0, creación de `.venv` con `uv venv --python 3.12`, configuración de entorno y modo sin conexión; verificar cada paso siguiendo el README desde un checkout limpio.
- [x] 6.2 Usar la sección 5 de `docs/condiciones-incremento-0(seccion 5).md` para crear una ficha por cada decisión D-01 a D-18 con problema, alternativas, decisión, justificación, consecuencias y estado; cotejar las fichas con esa fuente, sin inventar detalles que no contenga.
- [x] 6.3 Aplicar el flujo de una rama por incremento usando `incremento-0`, manteniendo funcional la rama principal; verificar la rama de trabajo y ejecutar las comprobaciones base antes de integrar cambios.

## 7. Validar el prototipo DOCX y registrar el avance

- [x] 7.1 Crear el prototipo aislado en `sistema/backend/informes/prototipo_docx.py` con Arial 12, interlineado sencillo, una tabla de un modelo resumen y un salto de sección; verificar esas propiedades con pruebas del documento generado.
- [x] 7.2 Abrir el DOCX generado en Word o LibreOffice y anotar el resultado, incluidos los fallos si los hubiera, en `sistema/docs/avance/00-base.md`; comprobar que la anotación describe solo pruebas efectivamente ejecutadas.

## 8. Verificar la integración de la base

- [x] 8.1 Desde una instalación limpia, ejecutar las migraciones iniciales y las pruebas backend en SQLite; ejecutar Vitest; arrancar backend y Vite por separado y comprobar `check --deploy` con los ajustes de producción y valores de prueba, sin conectarse a PostgreSQL. Registrar los comandos y resultados efectivamente obtenidos en el avance del incremento. Indicar explícitamente que la verificación contra una instancia real de PostgreSQL queda pendiente y no registrarla como ejecutada.
