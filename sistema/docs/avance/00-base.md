# Incremento 0: base de repositorio y entorno

## Instalación y comprobaciones

La verificación de instalación se realizó en una copia limpia temporal del
repositorio en Windows:

- `uv venv --python 3.12` creó `.venv` con Python 3.12.16.
- `python -m ensurepip --upgrade` y `python -m pip install -r sistema/backend/requirements.txt` terminaron correctamente.
- `npm ci` instaló las dependencias del lockfile; informó 111 paquetes añadidos y ninguna vulnerabilidad.
- `python manage.py migrate --noinput` aplicó las migraciones iniciales. `python manage.py check` terminó sin problemas.
- `npm run build` terminó correctamente con Vite 8.3.5.
- El servidor Django respondió HTTP 200 en `/admin/login/` y Vite respondió HTTP 200 en `/`.
- `python manage.py test` terminó con 7 pruebas aprobadas en SQLite, también en la copia temporal.
- Después de corregir el DOCX, `python manage.py test` volvió a terminar con 7 pruebas aprobadas en SQLite en el entorno de trabajo.
- `npm run test:run -- --pool=vmThreads --maxWorkers=1` terminó con 1 prueba Vitest aprobada en la copia temporal. Los pools `forks` y `threads` no iniciaron el worker en este entorno; el pool `vmThreads` sí lo hizo.
- La rama comprobada fue `incremento-0`. No se integraron ramas.

## Prototipo DOCX

`python informes\prototipo_docx.py` generó
`sistema/backend/informes/prototipo.docx` (archivo local excluido de Git).
`python manage.py test informes` aprobó la comprobación de una tabla M1, dos
secciones, Arial 12 e interlineado sencillo.

La primera versión abrió en Word, pero la usuaria vio la página en blanco salvo
una línea horizontal superior. Las variantes de diagnóstico confirmaron que
Word mostraba por separado texto, tabla y salto de sección. La causa fue asignar
`WD_LINE_SPACING.SINGLE`: su valor numérico se serializaba como espaciado cero.
Se sustituyó por el factor `1.0`, se mantuvo el salto de sección continuo al
final y se añadió una prueba que verifica el interlineado serializado. La
usuaria confirmó que la versión corregida muestra el título, la tabla M1, sus
criterios y el texto del prototipo. La automatización COM de esta sesión
no estuvo disponible (`CO_E_SERVER_EXEC_FAILURE` y `MK_E_UNAVAILABLE`); la
comprobación visual se realizó en Word por la usuaria.

## Configuración de producción

`python manage.py check --deploy` terminó con código 0 usando valores de prueba
para la configuración de producción y señaló cuatro advertencias relacionadas
con HSTS/HTTPS y cookies seguras. No se fijó una política TLS sin información
del servidor de despliegue.

## Verificación de integración (tarea 8.1)

Las siguientes comprobaciones se ejecutaron desde una copia limpia temporal
del repositorio en Windows, con `.venv` y `node_modules` creados desde cero:

- `uv venv --python 3.12`, `python -m ensurepip --upgrade`,
  `python -m pip install -r sistema/backend/requirements.txt` y `npm ci`
  finalizaron correctamente.
- `python manage.py migrate --noinput` aplicó las migraciones iniciales con los
  ajustes de desarrollo (SQLite).
- `python manage.py test` aprobó las 7 pruebas backend en SQLite.
- `npm run test:run -- --pool=vmThreads --maxWorkers=1` aprobó 1 prueba Vitest.
- Con `DJANGO_SETTINGS_MODULE=config.ajustes.produccion` y valores de prueba
  ficticios para las variables requeridas, `python manage.py check --deploy`
  terminó con código 0 y cuatro advertencias: `security.W004`, `security.W008`,
  `security.W012` y `security.W016`, relacionadas con HSTS, redirección HTTPS y
  cookies seguras. No se conectó a PostgreSQL durante esta comprobación.
- Django iniciado con
  `python manage.py runserver 127.0.0.1:18081 --noreload` respondió HTTP 200 en
  `/admin/login/`; Vite iniciado con
  `node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 15173 --strictPort`
  respondió HTTP 200 en `/`. Ambos procesos temporales se detuvieron al acabar.

La verificación de migraciones y pruebas contra una instancia real de PostgreSQL
queda pendiente hasta disponer del servidor del cliente o de una instalación
local. Conforme a D-14, no bloquea el cierre de este incremento y no se registra
como ejecutada.
