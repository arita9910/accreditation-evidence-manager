# Plan 05 — Módulo cuentas: usuarios, roles y permisos (incremento 1; modelo Usuario en el 0)

## Objetivo
Autenticar usuarios con login propio, asignarles roles con ámbito y decidir los permisos de toda la aplicación con **una sola función de autorización**.

## Convenciones comunes
- Django 5.2 + DRF; React 18 + Vite (JS); SQLite en desarrollo y PostgreSQL en producción.
- Nombres en español. App `sistema/backend/cuentas/` con `modelos.py`, `servicios.py`, `permisos.py`, `serializadores.py`, `vistas.py`, `urls.py`, `tests/`. Lógica en servicios; vistas delgadas.
- API bajo `/api/`, JSON, **sesión de Django + CSRF** (D-13). Sin JWT.
- Indicador = 2.º nivel; criterio = 3.er nivel. Ambigüedad → `docs/decisiones/`.

## Contexto
CU-01 (autenticarse) y CU-02 (gestionar usuarios y roles). Depende de: plan 02, plan 04 (ámbitos: carrera, facultad, ciclo), plan 06 (auditoría). **El modelo `Usuario` se crea en el incremento 0** (historia 0.3) con la primera migración del proyecto, porque Django no permite cambiar `AUTH_USER_MODEL` después.

## Roles y ámbitos
Seis roles. Ámbito: miembro de comisión y director de carrera → su carrera; decano → su facultad; rector → toda la universidad; administrador técnico → el sistema; par evaluador externo → un ciclo con fecha de caducidad.

## Entidades (plan 01)
- **Usuario** (D-01; incremento 0): username, nombre, apellidos, email, activo; hereda de `AbstractBaseUser` + `PermissionsMixin` (o `AbstractUser` simplificado); contraseña con el almacenamiento seguro de Django; `USERNAME_FIELD = 'username'`.
- **AsignacionRol** (incremento 1): usuario (FK), rol, carrera/facultad/ciclo (FK nulas), vigente_desde, vigente_hasta (nula). Exactamente el ámbito del rol; el par evaluador exige ciclo y `vigente_hasta`.

## Tareas

### T1 — Usuario propio (historia 0.3, incremento 0)
Modelo `Usuario`, `AUTH_USER_MODEL = 'cuentas.Usuario'`, primera migración antes de cualquier otra, administrador de Django registrado, orden `createsuperuser` funcionando. **Aceptación:** `makemigrations` desde cero produce la inicial con `cuentas.Usuario`; las pruebas crean usuarios.

### T2 — Autenticación
- `POST /api/sesion/` (entrar: username, password → sesión + cookie CSRF), `DELETE /api/sesion/` (salir), `POST /api/cuentas/cambiar-clave/` (clave actual y nueva, con validadores de Django), `GET /api/cuentas/yo/` (usuario, roles con ámbito y lista de permisos efectivos que el frontend usa para mostrar u ocultar opciones).
- Límite de intentos fallidos (p. ej. bloqueo temporal tras N intentos; valores configurables) y registro en auditoría (`resultado=denegado` en los fallos).
- **Aceptación:** pruebas de login correcto/incorrecto, logout, cambio de clave, CSRF obligatorio en POST/DELETE.

### T3 — Roles y asignaciones
- Servicios: `asignar_rol`, `revocar_rol`, `rol_vigente`; el par evaluador caduca solo (se evalúa `vigente_hasta` al comprobar permisos, no hace falta tarea programada).
- API para el administrador técnico: `GET/POST/PATCH /api/usuarios/`, `GET/POST/DELETE /api/usuarios/{id}/roles/`.

### T4 — Función de autorización (D-06)
- `puede(usuario, accion, objeto=None) -> bool` en `cuentas/permisos.py`: única fuente de verdad. Acciones como cadenas constantes (p. ej. `catalogo.cargar`, `ciclo.abrir`, `evidencia.cargar`, `informe.generar`, `auditoria.consultar`…), una por fila de la matriz.
- Clase `PermisoSistema(BasePermission)` de DRF que invoca `puede` con la acción declarada en la vista (`accion_permiso`) y el objeto/ámbito (carrera, ciclo, dimensión).
- Reglas transversales: **nadie edita un ciclo cerrado**; el administrador técnico no ve el contenido de las evidencias; cada acceso denegado se registra en la auditoría; la asignación del par evaluador caduca sola.

Matriz (propuesta, se ajusta con las entrevistas) — Sí/No por rol: Miembro (M), Director (D), Decano (Dc), Rector (R), Admin. técnico (A), Par evaluador (P):

| Acción | M | D | Dc | R | A | P |
| :- | :- | :- | :- | :- | :- | :- |
| Consultar estructura | Sí | Sí | Sí | Sí | Sí | Sí |
| Cargar/actualizar catálogo | No | No | No | No | Sí | No |
| Gestionar usuarios, roles, facultades, carreras | No | No | No | No | Sí | No |
| Abrir y cerrar ciclos | No | Sí | No | No | No | No |
| Asignar dimensiones | No | Sí | No | No | No | No |
| Cargar y clasificar evidencias | Solo dimensiones asignadas | Sí | No | No | No | No |
| Buscar y descargar evidencias | Sí | Sí | Consulta (su facultad) | Consulta | No | Sí (su ciclo) |
| Registrar datos y vínculos | Solo dim. asignadas | Sí | No | No | No | No |
| Ver datos sin respaldo | Sí | Sí | Sí | Sí | No | Sí |
| Redactar fortalezas y debilidades | Solo dim. asignadas | Sí | No | No | No | No |
| Generar informe | No | Sí | No | No | No | No |
| Descargar informe generado | No | Sí | Sí | Sí | No | Sí (versión final) |
| Proponer acciones de mejora | Sí | Sí | No | No | No | No |
| Aprobar acciones y seguimiento | Seguimiento de sus acciones | Sí | Consulta | Consulta | No | No |
| Comparar ciclos | No | Sí | Sí | Sí | No | No |
| Consultar auditoría | No | Su carrera | No | No | Todo | No |
| Expediente solo lectura (CU-19) | — | — | — | — | — | Sí (ciclo y plazo) |

### T5 — Pruebas de la matriz
Una prueba por celda de la matriz, **incluidas las negativas** (el decano no edita; el administrador técnico no ve evidencias; un miembro no toca dimensiones no asignadas; el par evaluador pierde acceso al caducar). Como los demás módulos aún no existen, probar contra `puede(...)` directamente y añadir las pruebas de vista a medida que se implementen los planes 07 a 12.

### T6 — Pantallas
Acceso (login), cambio de contraseña, administración de usuarios y roles (solo administrador técnico), navegación que muestra solo lo permitido (usa `/api/cuentas/yo/`; ocultar botones es comodidad, **la seguridad es del servidor**). Activar las rutas protegidas del plan 02.

### T7 — Conectar el catálogo
Cambiar los endpoints del catálogo (plan 03) a "usuario autenticado" y retirar el ajuste de desarrollo `CATALOGO_PUBLICO_EN_DESARROLLO`.

## Fuera de alcance
Recuperación de contraseña por correo (no hay servidor de correo definido), doble factor, integración con directorios externos.

## Definición de terminado
Toda la matriz cubierta por pruebas en verde; login y roles funcionando de extremo a extremo; avance en `docs/avance/05-cuentas.md`.
