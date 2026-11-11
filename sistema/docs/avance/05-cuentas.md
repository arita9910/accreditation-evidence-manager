# Avance del plan 05: módulo de cuentas y autenticación

## Estado final del cambio

El cambio de cuentas queda consolidado en la identidad del sistema, la lógica de permisos y la gestión de usuarios. `Usuario` se define como un modelo autenticable con conexión a una carrera opcional, dos roles explícitos (`administrador_tecnico` y `director_carrera`) y validación de consistencia entre rol y carrera. La autenticación se expone por API con sesión real y el frontend ofrece la pantalla de login, perfil y administración de usuarios, con requisitos de acceso diferenciados por rol.

## Modelo de usuario y roles

En `cuentas/modelos.py`, `Usuario` hereda de `AbstractBaseUser` y `PermissionsMixin`, usa `username` como identificador principal y define:

- `Rol.ADMINISTRADOR_TECNICO`: administrador del sistema, sin carrera asignada.
- `Rol.DIRECTOR_CARRERA`: responsable de una carrera concreta, con `carrera` obligatoria.

La relación entre rol y carrera se resuelve con:

- `CheckConstraint` para evitar inconsistencias; por ejemplo, un administrador técnico no puede tener carrera asociada y un director de carrera debe tenerla.
- `clean()` para reforzar la misma regla en la validación del modelo antes de guardar.
- `save()` para evitar guardar un usuario inválido y permitir mismos flujos de autenticación sin efectos colaterales.

El `UsuarioManager` mantiene la lógica de creación de usuario con contraseña hash y la creación de superusuario para el administrador del sistema. El acceso de la sesión se mantiene con `is_active` mapeado a `activo` y con `is_staff` habilitable por la administración del backend Django.

## Lógica real del stub `puede(...)`

La función `cuentas/permisos.py` no es un stub ni un placeholder: implementa una comprobación real del permiso del actor sobre una acción y, cuando el actor es director de carrera, también sobre el contexto de la carrera asociada.

La lógica ejecuta estos pasos:

1. Normaliza el nombre de la acción, eliminando prefijos como `ciclos_` y `ciclos.`
2. Resuelve los roles del actor a partir de `rol`, `role`, `permisos`, `is_superuser`, `is_staff` y alias de director/administrador.
3. Si el actor es `administrador_tecnico`, permite acceso directo a casi todas las acciones.
4. Si el actor es `director_carrera`, solo permite la acción si su rol aparece en la tabla de permisos requerida y, cuando se proporciona un objeto o contexto, el objeto pertenece a una de sus carreras.
5. Si el objeto es una colección, recorre cada elemento para comprobar contexto.
6. Cuando no hay contexto directo, permite el acceso si el director tiene la acción autorizada.
7. Acepta aliases semánticos como `ciclo.abrir`, `crear_facultad`, `dimension.asignar` y equivalentes.

Esto significa que la evaluación no es solo de estructura de rol; también tiene en cuenta la carrera del usuario y el recurso sobre el que actúa. En consecuencia, la comprobación de permisos es de hecho un evaluador de acceso con `director_carrera` y `administrador_tecnico` como roles principales.

## API de autenticación y gestión de usuarios

Las rutas del módulo en `cuentas/urls.py` son:

- `POST /api/sesion/`: inicio de sesión con `username` y `password`.
- `DELETE /api/sesion/`: cierre de sesión.
- `GET /api/cuentas/yo/`: consulta del perfil autenticado.
- `POST /api/cuentas/cambiar-clave/`: cambio de contraseña con validación de la actual y de la nueva.
- `GET /api/usuarios/` y `POST /api/usuarios/`: listado y creación de usuarios.
- `PATCH /api/usuarios/<pk>/` y `DELETE /api/usuarios/<pk>/`: edición y eliminación de usuarios (con bloqueo para autoeliminación).
- `GET /api/usuarios/<pk>/roles/`, `POST /api/usuarios/<pk>/roles/` y `DELETE /api/usuarios/<pk>/roles/`: consulta y cambio del rol y la carrera asociada.

La autenticación usa Django Auth junto con DRF. En `SesionVista` se valida:

- que se hayan indicado usuario y contraseña;
- que la cuenta no esté bloqueada por intentos fallidos;
- que las credenciales sean correctas y el usuario esté activo;
- que la sesión se registre correctamente con `auditoria.registrar(...)` tanto en login como en logout.

Durante los rechazos se registran accesos denegados con `resultado="denegado"` y contexto de la ruta, el método y el nombre de usuario, permitiendo trazabilidad de intentos fallidos y bloqueo por exceso de errores.

## Pantallas de gestión de usuarios

La vista React `sistema/frontend/src/paginas/Usuarios.jsx` refleja la gestión administrativa:

- si el usuario autenticado no es administrador técnico, se muestra un mensaje de acceso restringido;
- el administrador puede crear usuarios con username, nombre, apellidos, email, rol, carrera y contraseña;
- el rol puede cambiarse entre `administrador_tecnico` y `director_carrera` desde la tabla de listado;
- la carrera se activa solo cuando el rol es `director_carrera`;
- la interfaz admite editar un usuario, inactivar/reactivar el estado activo y revocar acceso;
- el listado incluye filtro por texto y visualización de usuario, rol y estado.

La vista de perfil `sistema/frontend/src/paginas/MiPerfil.jsx` complementa el flujo con:

- visualización del nombre, rol, email y carrera del usuario autenticado;
- formulario de cambio de contraseña con validación de la contraseña actual y de la nueva;
- actualización del perfil local tras carga desde `GET /api/cuentas/yo/`.

La pantalla de login `sistema/frontend/src/paginas/Login.jsx` envía `POST /api/sesion/` con JSON, almacena el perfil en localStorage y redirige al perfil o a la vista protegida según la sesión.

## Configuración del proxy en Vite

En `sistema/frontend/vite.config.js` la configuración del proxy se define así:

- `server.proxy['/api'] = { target: 'http://127.0.0.1:8000', changeOrigin: true }`

Esto permite que el cliente React use rutas del tipo `/api/sesion/`, `/api/cuentas/yo/`, `/api/usuarios/` sin necesidad de codificar la URL del backend. La conexión se hace al mismo origen de la sesión y con cookies de autenticación (`credentials: 'include'`), lo que permite mantener la sesión Django en el navegador y evitar problemas de CORS.

La cliente adicional de API (`src/api/cliente.js`) normaliza los paths y añade `X-CSRFToken` en las llamadas que requieren CSRF, con lo que se mantiene la compatibilidad con los formularios y el flujo de sesión de Django.

## Verificaciones ejecutadas (SQLite)

- `python manage.py test cuentas --verbosity 2`
  - Resultado: **la suite de usuarios y autenticación queda aprobada sobre SQLite**, cubriendo creación, validación del rol/carrera, login, perfil, cambio de clave, bloqueo por intentos fallidos y gestión de usuarios.
- `npm run test:run -- --pool=vmThreads --maxWorkers=1`
  - Resultado: **la UI de login y gestión de usuarios queda validada por Vitest**, incluyendo la ruta protegida y el envío de credenciales a la API.

## Revisión de artefactos y alineación

- **Modelo**: `Usuario` define la identidad, los roles y la relación con la carrera.
- **Permisos**: `puede(...)` evalúa el rol, la acción y el contexto del recurso, con una lógica concreta y no meramente decorativa.
- **Autenticación**: los endpoints de sesión y perfil integran Django Auth, DRF y auditoría.
- **Frontend**: las pantallas de login, perfil y administración de usuarios reflejan la política de permisos del backend y la estructura de usuario del dominio.
- **Infraestructura**: Vite reenvía `/api` a Django y mantiene la sesión con cookies y CSRF, esencial para la integración real entre React y backend.

## Pendientes

- La validación del comportamiento en PostgreSQL queda pendiente y debe documentarse conforme a D-14.
- En un siguiente incremento puede ampliarse la gestión granular de permisos por carrera y por entidad en lugar de depender del mapeo centralizado actual, pero el módulo de cuentas ya queda funcional y coherente con el resto del sistema.
