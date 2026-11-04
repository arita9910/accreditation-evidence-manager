# Decisión sobre herencia de `Usuario` en `ModeloBase`

## Pregunta abierta

Debe `cuentas.Usuario` heredar de `ModeloBase`? En este cambio no se decide ni implementa esa herencia.

## Contexto

- El plan 02 establece `ModeloBase` como convención compartida para entidades del dominio.
- `cuentas.Usuario` ya existe y hereda de `AbstractBaseUser` y `PermissionsMixin`, con `AUTH_USER_MODEL` apuntando a ese modelo.
- El cambio actual no añade modelos de estructura ni modifica la identidad de usuarios.

## Decisión provisional

Se deja la cuestión abierta para una decisión explícita en un cambio posterior, cuando el equipo defina si el modelo de autenticación debe compartir los campos comunes del núcleo o si debe mantenerse aislado.

## Consecuencias

- No se modifica `cuentas.Usuario` ni su migración en este incremento.
- Los módulos que reutilicen `ModeloBase` pueden hacerlo sin introducir dependencia de la entidad de usuario.
- La decisión final deberá evaluarse con la compatibilidad de autenticación, migraciones y cualquier dato existente.
