# Tasks

## 1. Modelo y migración

- [x] 1.1 Definir `Evidencia`, `FicheroEvidencia` y `Clasificacion` con su relación con ciclo, criterio y usuario, y verificar que la unicidad y la vigencia del archivo queden documentadas en pruebas. Verificación: pruebas del modelo y migración en SQLite.
- [x] 1.2 Añadir restricciones de negocio para soporte papel, ausencia de fichero y regla de ciclo abierto, y comprobar que el error se reporta con mensajes del proyecto. Verificación: tests de validación y casos de rechazo.
- [x] 1.3 Crear la migración inicial y comprobar que la estructura no rompe la base existente ni los ciclos ya abiertos. Verificación: ejecutar la migración y la batería de pruebas del módulo.

## 2. Carga, huella y almacenamiento sin sobrescritura

- [x] 2.1 Implementar el servicio de almacenamiento seguro con rutas internas protegidas y cálculo de SHA-256 por bloques. Verificación: prueba de generación de huella y de ruta insegura.
- [x] 2.2 Implementar `crear_evidencia` con validación de metadatos, soporte, tipo de fichero y tamaño, y registro de auditoría. Verificación: tests positivos y negativos de alta de evidencia.
- [x] 2.3 Implementar `reemplazar_fichero` con una nueva versión, marcado de `vigente=False` sobre la anterior y conservación del historial. Verificación: pruebas de reemplazo y de historial de versiones.
- [x] 2.4 Implementar `verificar_huella` y `verificar_huellas` para comparar el contenido real con el registro almacenado. Verificación: pruebas de archivo correcto y archivo alterado.
- [x] 2.5 Implementar `descargar` con control de permisos, auditoría y entrega diferida según entorno. Verificación: tests de descarga autorizada y rechazada.

## 3. Búsqueda y API

- [ ] 3.1 Implementar el servicio de búsqueda con dos estrategias (SQLite y PostgreSQL) y filtros por dimensión, indicador, criterio, curso y soporte. Verificación: pruebas de búsqueda con texto y filtros.
- [ ] 3.2 Exponer endpoints de listado, detalle y creación de evidencias bajo `/api/evidencias/` con autenticación y paginación. Verificación: pruebas de API y casos de permiso.
- [ ] 3.3 Exponer endpoints de historial y descarga de fichero vigente, incluyendo `POST /api/evidencias/{id}/ficheros/` y `GET /api/ficheros/{id}/descarga/`. Verificación: pruebas de API de versiones y descargables.
- [ ] 3.4 Exponer la clasificación por criterio y la verificación de huellas por ciclo, con repuesta JSON coherente con el resto de la API. Verificación: pruebas de clasificación y verificación de integridad por ciclo.

## 4. Pantalla del módulo

- [ ] 4.1 Crear la vista de listado con búsqueda, filtros y marca visual de evidencias en papel. Verificación: pruebas Vitest de listado y filtros.
- [ ] 4.2 Crear el formulario de carga y el detalle con historial de versiones y estado de huella. Verificación: pruebas Vitest del formulario y del panel de detalle.

## Workflow follow-up

- Revisar la integración de la API y la UI con la rama del incremento actual antes de cierre.
- Archivar el cambio una vez que la revisión del módulo esté aprobada y las pruebas de SQLite estén en verde.
