# Decisiones del Plan 12 - Módulo de informes

- Versionado por ciclo: la entidad de versiones se numera por ciclo (`numero` incremental) y conserva metadatos de trazabilidad (fecha, autor, hash SHA-256, advertencias y método de conteo).
- Regla provisional de “versión final”: mientras no exista marca explícita de cierre, se considera final la versión con mayor `numero` del ciclo para exposición al par evaluador.
- Manejo de completitud: los avisos de completitud no bloquean la generación; se persisten junto con la versión para consulta posterior.
- Conteo de páginas: se prioriza conteo con LibreOffice cuando está disponible; si no, se usa estimación por caracteres y se declara `metodo_conteo='estimado'`.
- Umbral de longitud: cuando el cuerpo sin anexos supera 50 páginas se mantiene la generación y se añade advertencia visible.
- Control de acceso del par evaluador: el acceso al expediente depende de asignación explícita por ciclo con `vigente_desde` y `vigente_hasta`, validada en cada consulta y descarga.
- Caducidad de asignación: al vencer `vigente_hasta`, el par evaluador pierde acceso inmediato a expediente y descargas del ciclo.
- Alcance de lectura: el par evaluador solo puede consultar su ciclo asignado y no dispone de endpoints ni acciones de escritura.
- Auditoría: se registran generación, consultas y descargas autorizadas en servicios; los rechazos 403 se conservan en el middleware central para evitar duplicidad de eventos.
- Alcance de validación: las pruebas del incremento se ejecutan en SQLite y PostgreSQL queda como pendiente documentado (D-14).
