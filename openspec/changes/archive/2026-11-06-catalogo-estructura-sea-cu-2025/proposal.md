# Proposal

## Why

La app `estructura` ya persiste los modelos normativos, pero aún no permite cargar de forma repetible el catálogo SEA-CU 2025 ni consultarlo desde la API y la interfaz. Este incremento conecta los datos disponibles con esos modelos y deja explícito qué información requiere cotejo en las fuentes antes de corregirse.

## What Changes

- Incorporar una carga idempotente y validada del catálogo SEA-CU 2025, conservando versiones y sus asociaciones con criterios y modelos.
- Exponer consultas de solo lectura para el árbol, las fichas de criterio, los modelos y las versiones, con la habilitación de desarrollo restringida según el plan.
- Añadir las pantallas de consulta del árbol y ficha de criterio, reutilizando el cliente API y los componentes existentes.
- Cotejar como última tarea al menos 12 criterios con el Manual 2025 y la Guía RM 36/2024; documentar diferencias y preguntas sin corregir texto por conjetura.
- Registrar avance y preguntas abiertas en `sistema/docs/avance/` y `sistema/docs/decisiones/`.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `estructura-normativa`: amplía el comportamiento del catálogo con carga versionada, consultas de solo lectura y presentación navegable de criterios.

## Impact

- Backend: app Django `sistema/backend/estructura/`, configuración y rutas API existentes; pruebas con SQLite.
- Datos: `sistema/datos/catalogo_sea_cu_2025.json` y `sistema/datos/modelos_resumen.json`.
- Frontend: rutas, componentes y pruebas de `sistema/frontend/src/`, usando `src/api/cliente.js`.
- Documentación: cotejo y avance bajo `sistema/docs/avance/`; preguntas abiertas bajo `sistema/docs/decisiones/`.
- No se añade ni modifica ningún paquete externo.
