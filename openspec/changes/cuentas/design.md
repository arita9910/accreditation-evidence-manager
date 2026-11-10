# Design

## Context

El módulo de cuentas atiende el plan 05 y sus tareas T1 a T7, con la obligación de centralizar la autenticación, las asignaciones de rol y la matriz de permisos del sistema. La decisión D-06 exige una autorización propia basada en roles con ámbito, y el proyecto ya tiene la convención de `ModeloBase` en el núcleo y un stub de permisos en `ciclos`/`auditoria` que debe reemplazarse por la lógica real de cuentas. (Fuente: docs/origin-plans/05-modulo-cuentas.md:3-71; docs/decisiones/README.md:52-58, 115-124; sistema/backend/cuentas/permisos.py:1-119; sistema/backend/ciclos/servicios.py:1-80; sistema/backend/auditoria/vistas.py:110-149)

## Goals / Non-Goals

**Goals:**
- Centralizar la autenticación, la sesión y la gestión de la identidad en `cuentas` con una única función de autorización.
- Mantener la semántica del rol y del ámbito para carrera, facultad, ciclo y sistema sin duplicar comprobaciones de permisos por módulo.
- Sustituir el stub actual de `puede(...)` por la lógica real del módulo `cuentas` y dejar la API de auditoría y de ciclos alineada con esa regla.
- Definir la administración mínima de usuarios y roles en una interfaz de administración técnica y la navegación protegida por permisos.

**Non-Goals:**
- No se incluye recuperación de contraseña por correo ni autenticación externa.
- No se añade doble factor ni inventario de permisos externos al sistema.
- No se introduce una nueva arquitectura de autenticación ni dependencias ajenas a Django + DRF.
- No se modifica el modelo `Usuario` para heredar de `ModeloBase` en este cambio, porque esa decisión exige una evaluación de migración y compatibilidad específica. (Fuente: sistema/docs/decisiones/nucleo.md:1-23)

## Decisions

### 1. `cuentas.Usuario` no hereda de `ModeloBase`
`cuentas.Usuario` se mantiene con `AbstractBaseUser` + `PermissionsMixin` y no hereda de `ModeloBase`. La decisión es explícita para preservar la autenticación de Django y evitar mezclar el modelo de identidad con las entidades de dominio del núcleo. La trazabilidad de los eventos de usuario se hará mediante el servicio `registrar(...)` de auditoría, manteniendo el registro de acciones y contexto sin depender de una herencia de modelo compartida. (Fuente: sistema/docs/decisiones/nucleo.md:1-23; sistema/backend/cuentas/models.py:1-55; sistema/backend/auditoria/servicios.py:1-120)

### 2. Un único rol activo por usuario con dos perfiles concretos
El módulo de cuentas utilizará un modelo simple de un solo rol activo por usuario. Los roles admitidos serán `Administrador Técnico` y `Director de Carrera`; el rol de administrador técnico tiene acceso global y el director de carrera solo tiene acceso a la carrera asignada, representada como una `ForeignKey` al modelo de `Carrera`. Esta regla debe respetarse exactamente en `puede(...)` para que los módulos de ciclos y auditoría reflejen el mismo comportamiento: el director solo ve su carrera y el administrador ve todo. (Fuente: docs/origin-plans/05-modulo-cuentas.md:12-22, 32-38; sistema/backend/ciclos/servicios.py:1-80; sistema/backend/auditoria/vistas.py:110-149)

### 3. Un único punto de decisión: `puede(usuario, accion, objeto=None)`
La autorización debe pasar por una función central en `cuentas/permisos.py` para evitar que cada módulo recalcule los permisos a mano. Esta decisión sigue exactamente la decisión D-06 y el plan 05, que exigen una función propia sobre roles con ámbito invocada desde una clase de permisos de DRF y con una matriz de acciones gestionada por el equipo. (Fuente: docs/decisiones/README.md:52-58; docs/origin-plans/05-modulo-cuentas.md:36-61)

### 4. Reemplazo del stub `puede(...)` por la lógica real de `cuentas`
El stub actual del módulo de ciclos y la comprobación de auditoría ya consumen `puede(...)`, pero esa función debe pasar a ser la real del módulo de cuentas, no una tabla de permisos local. El diseño conserva la firma pública existente en `ciclos/servicios.py` y en `auditoria/vistas.py`, evitando romper el flujo del sistema y reduciendo el riesgo de regresión mientras se integra la igualdad de permisos. (Fuente: sistema/backend/cuentas/permisos.py:1-119; sistema/backend/ciclos/servicios.py:1-80; sistema/backend/auditoria/vistas.py:110-149)

### 5. Sesión de Django + CSRF y no JWT
La API del módulo de cuentas usará la sesión de Django y la protección CSRF, siguiendo la decisión D-13 y la propuesta del plan 05; no se introduce JWT ni tokens de navegador. Esta decisión minimiza la superficie de ataque y mantiene la consistencia del proyecto. (Fuente: docs/decisiones/README.md:115-123; docs/origin-plans/05-modulo-cuentas.md:8-14, 27-30)

## Risks / Trade-offs

- [Riesgo] La centralización de permisos puede romper el acceso del sistema si la función `puede(...)` no conserva la firma actual ni los alias de acción ya usados por ciclos y auditoría. → Mitigación: mantener la misma API pública de `puede`, los nombres de acción y el patrón de validación en la capa de servicios y en `PermissionDenied`.
- [Riesgo] El perfil de par evaluador y la caducidad temporal pueden dejar huecos si la vigencia no se evalúa justo antes del chequeo de permisos. → Mitigación: evaluar `vigente_desde`/`vigente_hasta` durante la comprobación de permisos y en la gestión de roles.
- [Riesgo] La decisión de no heredar `Usuario` de `ModeloBase` puede dejar un modelo de identidad distinto del resto del dominio. → Mitigación: documentar la separación intencional y revisarla explícitamente si el equipo define más adelante una estrategia de herencia para la autenticación.

## Migration Plan

1. Crear y migrar el modelo `Usuario` para incorporar el rol activo y la carrera asociada, manteniendo `AUTH_USER_MODEL` con `AbstractBaseUser` + `PermissionsMixin` y sin herencia de `ModeloBase`.
2. Añadir la lógica de pertenencia de rol con un único rol activo por usuario, validando que `Administrador Técnico` sea global y `Director de Carrera` está restringido a su `ForeignKey` de carrera.
3. Reemplazar el stub `puede(...)` de ciclos y la comprobación de auditoría por la lógica real, manteniendo la firma pública e integrando los permisos en la capa de servicios.
4. Exponer los endpoints de sesión, perfil, cambio de contraseña y administración de usuarios/roles para el administrador técnico.
5. Validar la navegación protegida, los accesos denegados y la auditoría final con pruebas del módulo y con la matriz de permisos del plan 05.
