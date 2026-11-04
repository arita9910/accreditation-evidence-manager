# Avance del módulo núcleo

## Estado

Se completaron las partes del backend que aportan la base reutilizable del sistema: `ModeloBase`, almacenamiento privado de evidencias, paginación y manejador de excepciones DRF.

## Verificaciones ejecutadas

- `python manage.py test nucleo` en SQLite con la configuración de desarrollo.
- `python manage.py test config.tests` para comprobar la separación de `EVIDENCIAS_ROOT` y `MEDIA_ROOT`.
- `npm run test:run -- --pool=vmThreads --maxWorkers=1` para la plantilla frontend y la comprobación de pruebas base.

## Incidencias

- El entorno no tenía `python` disponible en PATH directo; se validó usando `.venv` y `uv`.
- La decisión sobre la herencia de `cuentas.Usuario` desde `ModeloBase` queda abierta y no se implementó en este cambio.
- La apertura de `/api/esquema/` se habilita solo en modo de desarrollo y queda desactivada en producción.

## Decisiones pendientes

- Confirmar si `cuentas.Usuario` debe heredar de `ModeloBase` antes de una migración de identidad.
- Completar la integración de `/api/salud/`, el esquema OpenAPI y la plantilla frontend final del plan 02.
