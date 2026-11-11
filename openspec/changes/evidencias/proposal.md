# Proposal

## Why

El módulo de evidencias es necesario para que cada ciclo de acreditación pueda gestionar sus documentos, archivos y clasificaciones con trazabilidad, permisos y verificación de integridad. La funcionalidad central de la evidencia documental no existe todavía como pieza compartida y requiere una política clara de almacenamiento, versionado y auditoría para evitar pérdida o manipulación de documentos.

## What Changes

- Añadir un módulo de evidencias para ciclos con metadatos de evidencia, soporte en papel o digital, clasificación por criterio y control de acceso.
- Registrar archivos con huella SHA-256 y evitar la sobrescritura de documentos antiguos al reemplazar una versión.
- Exponer servicios de búsqueda, descarga y verificación de huellas orientados a los criterios del plan 07.
- Integrar permisos y auditoría con los módulos existentes de cuentas y ciclos, manteniendo las reglas de negocio del proyecto.
- Preparar la API y la pantalla necesarias para listar, cargar, clasificar y verificar evidencias en el flujo de acreditación.

## Capabilities

### New Capabilities
- evidencias: gestión documental del ciclo, incluyendo carga, permisos, huella, clasificación y descarga controlada de evidencias.

### Modified Capabilities
- Ninguna; este cambio introduce un nuevo comportamiento del sistema en un módulo nuevo.

## Impact

- Backend: módulo `sistema/backend/evidencias/` con modelos, servicios, búsquedas, API y pruebas.
- Integraciones: uso de `ciclos.servicios.exigir_ciclo_abierto(ciclo)`, `auditoria.servicios.registrar(...)` y `cuentas.permisos.puede(...)`.
- Almacenamiento: gestión de archivos con SHA-256 y rutas internas protegidas, sin sobrescritura del archivo original.
- Frontend: pantallas de listado, carga, detalle y filtros para evidencias dentro del ciclo de acreditación.
