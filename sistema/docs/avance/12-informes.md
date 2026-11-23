# Avance del incremento 12: módulo de informes

## Resumen de implementación

- Se implementó la generación del informe de autoevaluación en DOCX editable con secciones obligatorias, modelos anexos y formato base.
- Se incorporó el versionado del informe por ciclo con numeración, almacenamiento, huella SHA-256, avisos de completitud y método de conteo de páginas.
- Se habilitaron endpoints para generar, consultar textos, listar versiones y descargar informes bajo control de permisos por rol y ciclo.
- Se incorporó el acceso del par evaluador al expediente en modo solo lectura, limitado a asignación vigente por ciclo y sin operaciones de escritura.
- Se ajustó la interfaz React para edición cualitativa, generación con avisos, historial de versiones y consulta del expediente del par evaluador.

## Verificaciones registradas del cambio

- Migraciones del bloque aplicadas y comprobadas en SQLite.
- Pruebas backend de informes/permisos/expediente ejecutadas en SQLite.
- Pruebas frontend (Vitest) de pantallas nuevas ejecutadas con `npm run test:run -- --pool=vmThreads --maxWorkers=1`.
- Verificación de salida DOCX fuera de control de versiones (`git check-ignore` sobre la ruta de informes).
- Revisión manual de DOCX de prueba largo reportada en la tarea 5.4 del cambio.

## Pendientes

- Validación en PostgreSQL pendiente y documentada (D-14). No se declara como ejecutada en este incremento.
