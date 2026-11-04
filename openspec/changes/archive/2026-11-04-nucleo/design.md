# Design

## Context

El plan 02 entrega servicios comunes en la app `nucleo`, que ya está registrada en Django pero solo contiene `apps.py`. `cuentas.Usuario` ya existe y `AUTH_USER_MODEL` apunta a él. La configuración actual define `EVIDENCIAS_ROOT`, pero también asigna `MEDIA_ROOT = EVIDENCIAS_ROOT`; esa coincidencia debe resolverse para mantener separada la ubicación privada de evidencias. En el frontend ya están instalados `react-router-dom` y Bootstrap; `App.jsx` todavía es la plantilla inicial de Vite.

El diseño sigue el modelo abstracto del plan 01 y los contratos existentes de `runtime-configuration` y `user-identity`. No añade entidades de estructura ni modifica el modelo de cuentas.

## Goals / Non-Goals

**Goals:**
- Entregar el modelo abstracto y la asignación reutilizable de autoría para solicitudes de API.
- Proteger el almacenamiento bajo `EVIDENCIAS_ROOT` y mantenerlo separado de los directorios servidos públicamente.
- Establecer los comportamientos de API y frontend compartidos definidos por el plan 02.
- Dejar una base que los módulos posteriores puedan reutilizar sin crear modelos de estructura en este cambio.

**Non-Goals:**
- Crear modelos de `VersionNormativa`, `Dimension`, `Indicador`, `Criterio` ni otras entidades de estructura o dominio.
- Reimplementar, renombrar o migrar `cuentas.Usuario`; tampoco decidir ahora si hereda de `ModeloBase`.
- Implementar login, permisos, pantallas de dominio o rutas protegidas activas antes de que exista `/api/cuentas/yo/`.
- Servir evidencias desde Django, Vite, `STATIC_ROOT` o `MEDIA_ROOT`.

## Decisions

1. **Mantener `ModeloBase` abstracto y aislado de las entidades del dominio.** Implementar sus cuatro campos en `sistema/backend/nucleo/modelos.py`, con los nombres del plan, marcas temporales automáticas y referencias anulables con `on_delete=PROTECT` a `settings.AUTH_USER_MODEL`. Como Django descubre modelos mediante `models.py` y el plan prescribe el nombre español, proporcionar el puente de importación necesario en `sistema/backend/nucleo/models.py`. Las pruebas usarán un modelo concreto temporal para verificar la herencia; no se añadirá un modelo de estructura al producto.
2. **Asignar autoría desde los serializadores, no desde middleware.** Proporcionar un mixin o helper común para que el serializador asigne `creado_por` en altas y `modificado_por` en altas y cambios usando `request.user` cuando esté autenticado. Así la atribución queda acotada a escrituras de API y no depende de estado global o contexto de ejecución. Las referencias podrán quedar vacías en operaciones sin usuario autenticado.
3. **Usar `EVIDENCIAS_ROOT` como raíz privada única de ficheros.** Conservar la configuración por entorno existente y cambiar el alias actual que iguala `MEDIA_ROOT` a `EVIDENCIAS_ROOT`: las dos raíces serán distintas y el servicio de evidencias no dependerá de `MEDIA_ROOT`. Validar rutas relativas tras resolverlas, rechazar rutas absolutas y componentes `..`, y comprobar que el destino permanece bajo la raíz privada. El servicio generará UUID con extensión saneada y calculará la huella SHA-256 por bloques durante la escritura.
4. **Mantener el contrato de archivos del plan.** Ubicar las operaciones en `sistema/backend/nucleo/almacenamiento.py`: guardado con metadatos, apertura, cálculo y verificación de huella, y borrado limitado a pruebas o limpieza explícita de huérfanos. El borrado no formará parte de operaciones normales de negocio.
5. **Centralizar utilidades DRF.** Añadir paginación con tamaño configurable y manejador de excepciones que preserve el detalle estructurado en español. Montar `/api/salud/` sin autenticación. Instalar `drf-spectacular` como dependencia fijada y habilitar `/api/esquema/` solo en desarrollo, conforme a D-18.
6. **Reutilizar dependencias y establecer el cliente común en el frontend.** Implementar el cliente `fetch` con credenciales de mismo origen y CSRF en métodos de escritura, el proxy `/api` de Vite y los componentes `Diseno`, `Mensaje` y `Cargando`. Configurar el router con `react-router-dom` existente y preparar la protección sin activarla mientras falte `/api/cuentas/yo/`. Usar Bootstrap local ya instalado; no modificar `package.json` para volver a añadir ninguna de esas dependencias.
7. **Registrar trazabilidad en las rutas indicadas.** Anotar el resultado del incremento en `sistema/docs/avance/02-nucleo.md`. Registrar la pregunta de herencia de usuario bajo `sistema/docs/decisiones/` y dejarla abierta, sin resolverla implícitamente mediante el código de este cambio.

## Risks / Trade-offs

- [La configuración actual hace coincidir `MEDIA_ROOT` y `EVIDENCIAS_ROOT`] → Separar ambas raíces y probar que la ruta de evidencias no se encuentra bajo directorios públicos ni se publica mediante URL.
- [Los consumidores futuros podrían omitir el helper de autoría] → Proveer una integración común en serializadores y pruebas que demuestren la asignación en altas y cambios.
- [Una ruta manipulada puede escapar del directorio privado] → Validar entradas antes de acceso y verificar el destino resuelto permanece dentro de `EVIDENCIAS_ROOT`; probar rutas absolutas y traversal.
- [`drf-spectacular` no está actualmente en `requirements.txt`] → Fijar la dependencia y actualizar el procedimiento/almacén offline del proyecto para que pueda instalarse reproduciblemente.
- [El contrato de identidad no especifica la herencia de `ModeloBase`] → Mantener intacto `cuentas.Usuario` en este cambio y registrar la pregunta pendiente para una decisión explícita.

## Migration Plan

No se requiere migración de datos existente por `ModeloBase`, ya que es abstracto; los módulos concretos incorporarán los campos cuando adopten la base. Implementar primero la separación de ajustes privados/públicos y el modelo/servicio de archivos con pruebas; después las utilidades DRF y la dependencia OpenAPI; finalmente cliente, componentes y router. Ejecutar migraciones y pruebas backend en SQLite, pruebas Vitest y las comprobaciones pertinentes de configuración. Registrar los resultados efectivamente observados en el avance del núcleo. No habilitar publicación de ficheros ni protección de sesión antes de contar con sus servicios/endpoints correspondientes.

## Open Questions

- **¿Debe `cuentas.Usuario` heredar de `ModeloBase`?** El modelo actual hereda de `AbstractBaseUser` y `PermissionsMixin`, mientras que el plan 01 establece `ModeloBase` como convención para las entidades. Este cambio no modifica `Usuario`; la respuesta debe registrarse y decidirse antes de integrar esa herencia en una migración.
