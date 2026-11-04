# Proposal

## Why

Los módulos posteriores necesitan una base compartida para persistir la autoría de los cambios, almacenar evidencias de forma privada, exponer convenciones comunes de API y consumir esa API desde React. El plan 02 cubre estos servicios y la plantilla inicial del frontend, sin implementar entidades del módulo de estructura ni duplicar la identidad que ya proporciona `cuentas.Usuario`.

## What Changes

- Añadir a `nucleo` un `ModeloBase` abstracto con campos de creación y modificación, y un mecanismo reutilizable para asignar el usuario de la petición.
- Implementar el servicio de archivos sobre la configuración existente `EVIDENCIAS_ROOT`, con validación de rutas, nombres internos únicos y huellas SHA-256. Separar esa raíz privada de `MEDIA_ROOT` y de cualquier ubicación servida públicamente.
- Añadir utilidades comunes de API: paginación configurable, formato de errores en español, endpoint de salud y esquema OpenAPI opcional en desarrollo.
- Instalar `drf-spectacular` para el esquema OpenAPI.
- Crear el cliente API y los componentes base del frontend, y preparar rutas protegidas con React Router. Reutilizar React Router y Bootstrap, ya presentes en `package.json`.
- Registrar el avance en `sistema/docs/avance/02-nucleo.md` y la pregunta pendiente sobre la herencia de `Usuario` en `sistema/docs/decisiones/`.

## Capabilities

### New Capabilities

- `nucleo`: modelo abstracto común, almacenamiento privado de ficheros, utilidades de API y plantilla frontend compartida.

### Modified Capabilities

- `runtime-configuration`: separar la raíz privada `EVIDENCIAS_ROOT` de `MEDIA_ROOT` para que las evidencias permanezcan fuera de las ubicaciones públicas.

## Impact

- Backend: app existente `sistema/backend/nucleo/`, ajustes de almacenamiento, rutas API y dependencias backend.
- Frontend: `sistema/frontend/src/`, configuración de Vite y dependencias existentes de React Router y Bootstrap.
- Documentación: avance y pregunta abierta bajo `sistema/docs/`.
- La capacidad `user-identity` y el modelo `cuentas.Usuario` no cambian.
- No se modificará `cuentas.Usuario` ni se crearán modelos de estructura (`VersionNormativa`, `Dimension`, `Indicador`, `Criterio` u otros).
