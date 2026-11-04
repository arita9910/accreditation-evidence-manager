# Avance del módulo núcleo

## Estado

El núcleo del plan 02 está implementado: `ModeloBase` y atribución reutilizable, almacenamiento privado, convenciones comunes de API, endpoint de salud, esquema OpenAPI solo en desarrollo y plantilla frontend con cliente API y rutas preparadas. No se modificó `cuentas.Usuario` ni se añadieron modelos de estructura o dominio.

## Verificaciones ejecutadas

- `python manage.py test --settings=config.ajustes.desarrollo`: 17 pruebas backend aprobadas en SQLite, incluyendo salud anónima, errores, paginación, OpenAPI en desarrollo y ausencia de la ruta cuando `DEBUG` es falso.
- Se ejecutaron las migraciones Django sobre una base SQLite temporal; terminaron correctamente sin modificar el `db.sqlite3` de desarrollo existente.
- Las pruebas de configuración verificaron que `EVIDENCIAS_ROOT` es configurable y permanece separada de `MEDIA_ROOT` y `STATIC_ROOT`.
- `npm run test:run -- --pool=vmThreads --maxWorkers=1`: 4 pruebas Vitest aprobadas, incluyendo CSRF en POST y presentación de errores mediante `Mensaje`.
- `npm run build` y `npm run lint`: ambos finalizaron correctamente. El cliente conserva las credenciales del mismo origen y Vite reenvía `/api` a `http://localhost:8000`.
- Se descargaron las dependencias fijadas al almacén local de paquetes y se verificó la instalación con `pip --no-index --find-links`; el almacén bajo `sistema/almacen/` está ignorado por Git según la configuración del proyecto.

## Incidencias

- Las primeras ejecuciones detectaron ajustes necesarios en las pruebas (limpieza del DOM y negociación JSON del esquema); se corrigieron y las verificaciones finales pasaron.
- No quedan incidencias de implementación pendientes.

## Decisiones pendientes

- Confirmar si `cuentas.Usuario` debe heredar de `ModeloBase` antes de una migración de identidad.
