# Spec Delta

## Purpose

Definir la gestión de valoraciones cualitativas del ciclo de acreditación, asegurando que cada fortaleza o debilidad quede vinculada a criterios y evidencias válidas, con permisos por rol/dimensión, auditoría y bloqueo sobre ciclos cerrados.

## ADDED Requirements

### Requirement: Registro de valoraciones por dimensión
El sistema SHALL permitir registrar una valoración de tipo fortaleza o debilidad asociada a un ciclo y una dimensión, con texto redactado y con la relación de criterios y evidencias que la sustentan.

#### Scenario: Crear una valoración autorizada
- **WHEN** un miembro asignado a la dimensión o el director del ciclo crea una valoración válida
- **THEN** el sistema guarda la valoración y la vincula a la dimensión, el ciclo y los criterios/evidencias elegidos

#### Scenario: Rechazar una valoración sobre ciclo cerrado
- **WHEN** una operación de creación o edición intenta usarse sobre un ciclo que no está abierto
- **THEN** el sistema deniega la operación y devuelve un error claro

### Requirement: Validación de criterios y evidencias
El sistema SHALL validar que cada criterio de la valoración pertenezca a la misma dimensión y que cada evidencia esté asociada al mismo ciclo, rechazando combinaciones cruzadas.

#### Scenario: Rechazar criterio de otra dimensión
- **WHEN** una valoración incluye un criterio que no pertenece a la dimensión seleccionada
- **THEN** el sistema rechaza la valoración y no crea la relación

#### Scenario: Rechazar evidencia ajena al ciclo
- **WHEN** un usuario intenta asociar una evidencia de otro ciclo a una valoración
- **THEN** la operación queda rechazada y se conserva la trazabilidad del intento

### Requirement: Permisos, auditoría y eliminación segura
El sistema SHALL aplicar permisos por rol y carrera con `puede(...)`, registrar cada alta o cambio con `registrar(...)` y impedir la eliminación de una valoración cuando dependan de ella acciones de mejora.

#### Scenario: Permiso denegado por dimensión
- **WHEN** un usuario no asignado a la dimensión intenta crear o editar una valoración
- **THEN** el sistema rechaza la operación y no persiste cambios

#### Scenario: Eliminación bloqueada por dependencia
- **WHEN** una debilidad tiene acciones de mejora asociadas
- **THEN** el sistema evita la eliminación y devuelve un mensaje explicativo

### Requirement: Formato de porcentajes y API del módulo
El sistema SHALL ofrecer un formateador de porcentaje reutilizable en la forma `86,2 % (19/23)` con coma decimal y SHALL exponer la API del módulo para listar, crear, editar y eliminar valoraciones por dimensión y tipo.

#### Scenario: Formatear un porcentaje con coma decimal
- **WHEN** se calcula una relación de origen con numerador 19 y denominador 23
- **THEN** el sistema devuelve `86,2 % (19/23)` y mantiene el texto con la relación de origen en el formato acordado

#### Scenario: Consultar valoraciones por dimensión y tipo
- **WHEN** un cliente autenticado consulta `/api/ciclos/{id}/valoraciones/` con filtros de dimensión y tipo
- **THEN** el sistema devuelve solo las valoraciones visibles para ese ciclo y ese usuario
