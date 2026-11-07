# Design

## Context

Este incremento aborda la base de dominio del módulo de ciclos para la organización y evaluación de acreditación. El alcance exige modelar la estructura de facultades, carreras y ciclos, así como la asignación de dimensiones a los miembros de la comisión, integrando las restricciones establecidas en el plan 04 y dejando la validación de categoría-vigencia como dato registrado y no calculado.

## Goals / Non-Goals

**Goals:**
- Definir las entidades y reglas del dominio del módulo ciclos.
- Asegurar que cada ciclo cumpla la lógica de apertura, cierre y estado.
- Reutilizar las entidades normativas existentes y preparar la conexión con permisos y auditoría.

**Non-Goals:**
- No se calcula la categoría de acreditación ni la vigencia a partir del contenido del ciclo.
- No se implementan roles y login ni auditoría en este incremento.
- No se incluyen planes posteriores del contenido de los ciclos ni otros módulos.

## Decisions

### 1. Entidades del dominio

Se modelarán las siguientes entidades siguiendo las convenciones del plan 04:

- **Facultad**: nombre. La crea el administrador técnico.
- **Carrera**: facultad, nombre, activa.
- **Ciclo**: carrera, version_normativa, tipo, anio_base, curso_inicial, curso_final, estado, ciclo_anterior, categoria_obtenida, vigencia_anios, fecha_apertura, fecha_cierre.
- **AsignacionDimension**: ciclo, usuario, dimension; restricción de unicidad por `(ciclo, usuario, dimension)`.

La relación con `VersionNormativa` y `Dimension` se mantiene por referencia directa, respetando el enfoque del plan 03 y evitando deduplicaciones en la estructura normativa.

### 2. Reglas de negocio del ciclo

Las reglas se mantienen estrictamente dentro del alcance del plan 04:

- Un solo ciclo abierto por carrera.
- Cinco cursos entre `curso_inicial` y `curso_final`.
- El claustro se cuenta sobre el último curso concluido y el año base.
- Un ciclo cerrado es solo lectura.
- La vigencia es de 5, 7 o 9 años y se registra, sin cálculo automático.
- El ciclo anterior debe pertenecer a la misma carrera y estar cerrado.

### 3. Validación en servicios

La lógica de negocio se centraliza en servicios para evitar reglas dispersas en vistas o serializadores. En particular:

- `crear_facultad` y `crear_carrera` gestionan la alta del dominio.
- `abrir_ciclo(...)` valida la carrera, el ciclo anterior, la disponibilidad de apertura y la regla de cinco cursos.
- `cerrar_ciclo(...)` fija el cierre y valida la vigencia con los valores permitidos.
- `asignar_dimension(...)` y `quitar_asignacion(...)` controlan la operación sobre ciclos abiertos y la restricción de identidad del usuario. 
- `exigir_ciclo_abierto(ciclo)` ofrece una validación reutilizable para los demás módulos.

### 4. Estado y acceso

Como indica el plan 04, la API debe servir consultas de ciclos y asignaciones, pero el ciclo cerrado queda en modo de solo lectura. Esta decisión se refleja en los servicios y en la capa API para evitar que una operación de escritura modifique registros cerrados.

### 5. Pregunta Abierta

Se documenta explícitamente esta incompletitud normativa como pregunta abierta:

- **Pregunta Abierta**: la correspondencia exacta entre la `categoria_obtenida` y los años de vigencia (`5`, `7` o `9`) debe confirmarse con el artículo 13 de la RM 160/2023 y con la orientación del tutor. El plan 04 indica que esa relación no está resuelta en los documentos de referencia del proyecto y por ello se deja como dato registrado y no calculado. Hasta obtener la confirmación normativa, `vigencia_anios` solo acepta `5`, `7`, `9` o `nulo`, sin asumir una regla automática de categoría → años.

## Risks / Trade-offs

- [Risk] Si la relación categoría-vigencia no se confirma con la normativa, la lógica de negocio puede quedar incompleta para validación automática. Mitigation: registrar el valor y dejar la validación de equivalencia como pregunta abierta y pendiente de tutoría.
- [Risk] Si la restricción de ciclo abierto se valida solo en la vista, se duplicará la lógica de negocio. Mitigation: centralizar la validación en servicios.
- [Risk] Al cerrar un ciclo, la ausencia de política definida para categoría-vigencia puede causar ambigüedad en la UI. Mitigation: reflejar la decisión en la pantalla como dato opcional con validación de valores permitidos.

## Tareas del módulo (T1 a T5)

### T1 — Modelos y migraciones

- Definir los modelos `Facultad`, `Carrera`, `Ciclo` y `AsignacionDimension` con los campos y restricciones planificados.
- Añadir las migraciones, claves foráneas y restricciones de unicidad.
- Incluir pruebas de integridad para ciclo abierto, ciclo anterior, cierre y validación de vigencia.

### T2 — Servicios

- Implementar `crear_facultad`, `crear_carrera`, `abrir_ciclo`, `cerrar_ciclo`, `asignar_dimension`, `quitar_asignacion` y `exigir_ciclo_abierto`.
- Validar que no exista otro ciclo abierto por carrera.
- Validar `ciclo_anterior` y la regla de cinco cursos.
- Garantizar que un ciclo cerrado sea de solo lectura.
- Rechazar asignaciones duplicadas y vigencias fuera de 5/7/9/nula.

### T3 — API

- Exponer endpoints para facultades, carreras, ciclos y asignaciones de dimensiones.
- Añadir filtros por carrera y estado para los ciclos.
- Dar soporte a la apertura, cierre y consulta de detalle de un ciclo.
- Aplicar paginación y errores estándar en español siguiendo el plan 02.
- Cubrir pruebas del API con los códigos de error esperados.

### T4 — Pantallas React

- Crear la vista de carreras con estado de sus ciclos.
- Implementar el formulario de apertura con aviso de los cinco cursos.
- Crear el cierre con categoría y vigencia opcionales.
- Presentar la tabla de asignación dimensión × usuario para miembros de la comisión.
- Validar formularios y reflejar la API en la interfaz.

### T5 — Conexión con cuentas y auditoría

- Conectar permisos a partir de `cuentas.permisos.puede(...)` cuando estén disponibles.
- Requerir que el director de carrera pueda abrir, cerrar y asignar; crear facultad y carrera solo lo haga el administrador técnico.
- Llamar a `auditoria.servicios.registrar(...)` en cada operación relevante.
- Añadir las pruebas negativas de permisos y auditoría en la integración con los planes 05 y 06.

## Open Questions

- La relación exacta entre categoría obtenida y vigencia (5, 7 o 9) debe ser corroborada con la normativa y el tutor antes de cerrar la validación funcional.
- La implementación definitiva de permisos y auditoría queda pendiente hasta la disponibilidad de los planes 05 y 06.
