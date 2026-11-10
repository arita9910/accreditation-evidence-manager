# Tasks

## 1. Modelo y migración

- [ ] 1.1 Migrar el modelo `Usuario` para añadir el rol activo y la carrera asociada del usuario, manteniendo `AUTH_USER_MODEL` con `AbstractBaseUser` + `PermissionsMixin` y sin herencia de `ModeloBase`. Verificar la migración SQLite y la alineación con la decisión del núcleo.
- [ ] 1.2 Definir la regla de negocio de un único rol activo por usuario, con los valores `Administrador Técnico` (acceso global) y `Director de Carrera` (acceso restringido a su carrera mediante `ForeignKey`), y validar que la integridad del modelo impide roles inconsistentes.
- [ ] 1.3 Validar la compatibilidad de la migración con el registro de auditoría, asegurando que el `rol` y la `carrera` queden disponibles para la trazabilidad y para la función `puede(...)` sin duplicar reglas en otros módulos.

## 2. Lógica de permisos real y reemplazo del stub

- [ ] 2.1 Implementar la matriz de permisos y la función `puede(usuario, accion, objeto=None)` en `cuentas/permisos.py`, respetando exactamente la regla de negocio: el director solo ve su carrera y el administrador ve todo.
- [ ] 2.2 Sustituir el stub de permisos del módulo de ciclos por la lógica real del módulo `cuentas`, manteniendo la firma actual y verificando que `abrir_ciclo`, `cerrar_ciclo` y `asignar_dimension` siguen funcionando.
- [ ] 2.3 Reemplazar la comprobación de acceso de auditoría por la autorización real de `cuentas`, y verificar que un director solo vea registros de su ámbito y que el administrador técnico conserva acceso global.
- [ ] 2.4 Incorporar la trazabilidad de accesos denegados a la auditoría y verificar que el registro conserva usuario, acción y entidad sin contenido sensible.

## 3. API de autenticación y administración

- [ ] 3.1 Crear `POST /api/sesion/`, `DELETE /api/sesion/`, `POST /api/cuentas/cambiar-clave/` y `GET /api/cuentas/yo/`, y verificar login, logout, cambio de contraseña y respuesta del perfil autenticado.
- [ ] 3.2 Implementar los endpoints de gestión de usuarios y roles para el administrador técnico (`GET/POST/PATCH /api/usuarios/` y `GET/POST/DELETE /api/usuarios/{id}/roles/`), y verificar el flujo de alta, edición y revocación.
- [ ] 3.3 Añadir la validación de CSRF y la política de bloqueo por intentos fallidos, y verificar que los POST/DELETE requieren sesión segura y que el acceso denegado queda registrado.

## 4. Pantallas de gestión de usuarios y roles

- [ ] 4.1 Diseñar la pantalla de acceso (login), cambio de clave y perfil del usuario autenticado, y verificar la navegación protegida con rutas del plan 02.
- [ ] 4.2 Implementar la administración de usuarios y roles para el administrador técnico, con filtros, listado y acciones de asignación/revocación, y verificar la experiencia de uso en Vitest.
- [ ] 4.3 Ocultar o deshabilitar acciones en la UI según el perfil del usuario sin depender de la interfaz como guardia de seguridad, y verificar que la seguridad del servidor sigue siendo la fuente de verdad.

## 5. Verificación final

- [ ] 5.1 Ejecutar la prueba de la matriz de permisos del plan 05, cubriendo tanto las autorizaciones positivas como las negativas, y verificar que la regla de roles con ámbito funciona para cada perfil.
- [ ] 5.2 Ejecutar las pruebas de backend para autenticación, roles, auditoría y ciclos, y verificar que la integración con el stub real de permisos no rompe la operación previa.
- [ ] 5.3 Revisar la documentación de avance y el cierre del módulo, y confirmar que la propuesta queda alineada con el plan 05, D-06, D-13 y la evaluación del núcleo.
