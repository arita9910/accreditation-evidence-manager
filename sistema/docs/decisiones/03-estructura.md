# Decisiones abiertas sobre la estructura normativa

## Preguntas abiertas

- ¿Cómo representar “M7 (7.1)”? El catálogo lo cita, `modelos_resumen.json` no tiene un 7.1 separado y el Manual contiene una tabla 7.1 (`Manual:1342`). Se debe confirmar si `CriterioModelo` permite conservar “7.1” como calificador o si hace falta otra representación.
- ¿Cómo resolver el desplazamiento de numeración 3.3/3.4? La Guía no trae 3.3 y su 3.4 contiene el texto que el Manual asigna a 3.3 (`Manual:478`, `Manual:484`, `Guía:368`).
- ¿Qué correspondencias del Manual aplican a 4.4.4 y 5.2.4–5.2.6? Mantener `codigo_manual` vacío hasta resolver el cotejo.
- La Resolución presenta 10 modelos y el Manual 11 con numeración distinta. Confirmar en el cotejo que las referencias `modelos_manual` y los 11 identificadores siguen la numeración del Manual.
- ¿Qué campos de `ModeloCampo` deben definirse? Queda pendiente para el Plan 09.

## Estado

Las preguntas permanecen abiertas; no se asignan valores de catálogo por inferencia. El cotejo de fuentes de la tarea 4.2 debe registrar las ubicaciones y los resultados antes de modificar datos.
 


## Decisiones tomadas (Registro oficial)

A continuación se registran las decisiones cerradas correspondientes al Plan 03:

- Fecha de aprobación: Se asume 2024-04-29 (fecha de la Resolución No. 36/2024). *Nota: Confirmada y aprobada por la tutora.*
- Catálogo: 6 dimensiones, 24 indicadores (texto del Manual, líneas 375 a 580) y 65 criterios.
- Códigos manuales: codigo_manual vacío en 4.4.4 y 5.2.4–5.2.6 por duda documentada; 3.2.4 es solo Guía.
- Modelos: Los 11 del Manual (líneas 1234 a 1409). La Resolución tiene 10 con otra numeración; el catálogo sigue la del Manual.
- Asociaciones criterio–modelo: 20 criterios, 22 asociaciones.
- Alcance: ModeloCampo NO se carga (va al Plan 09) y TipoEvidencia NO se puebla en este plan (va al Plan 07).
- Cargador: Valida estructura y totales, usa transacción, es repetible por claves naturales y no repunta ciclos existentes.
- Modelo de ejemplo: Para la tabla DOCX del prototipo se usará el Modelo 1 (Resumen del claustro).