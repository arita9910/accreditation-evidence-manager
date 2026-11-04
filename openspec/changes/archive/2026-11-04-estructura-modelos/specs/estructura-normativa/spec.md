# Spec Delta

## Purpose

Define la persistencia versionada de la estructura normativa y de sus relaciones de consulta, de modo que los módulos posteriores puedan referirse a dimensiones, indicadores, criterios y modelos sin duplicar el catálogo.

## ADDED Requirements

### Requirement: Versiones normativas conservan sus datos de identificación
Una versión normativa SHALL almacenar nombre, fecha de aprobación, fuentes y estado activo, y SHALL poder ser referenciada por las dimensiones y definiciones de modelo que pertenecen a esa versión.

#### Scenario: Crear una versión normativa
- **WHEN** se registra una versión con nombre, fecha de aprobación, fuentes y estado activo
- **THEN** esos valores quedan persistidos y disponibles para las relaciones de la versión

### Requirement: La estructura normativa conserva su jerarquía
La estructura SHALL relacionar cada dimensión con una versión, cada indicador con una dimensión, y cada criterio con un indicador; las evidencias sugeridas y los requisitos de categoría SHALL relacionarse con criterios, y los tipos de evidencia SHALL relacionarse con dimensiones.

#### Scenario: Consultar entidades relacionadas
- **WHEN** se guarda una estructura con una versión, una dimensión, un indicador y un criterio
- **THEN** cada entidad relacionada conserva la referencia al nivel padre especificado

#### Scenario: Relacionar evidencia sugerida y requisitos
- **WHEN** se guardan evidencias sugeridas o requisitos de categoría de un criterio y tipos de evidencia de una dimensión
- **THEN** cada registro queda asociado a su criterio o dimensión correspondiente

### Requirement: Los códigos son únicos dentro de su nivel y padre
La estructura SHALL rechazar códigos duplicados bajo el mismo padre: dimensión dentro de su versión, indicador dentro de su dimensión y criterio dentro de su indicador.

#### Scenario: Rechazar código repetido en una dimensión de la misma versión
- **WHEN** se intenta guardar otra dimensión con el mismo código y versión
- **THEN** la persistencia rechaza la operación por la restricción de unicidad

#### Scenario: Permitir códigos iguales en versiones o padres distintos
- **WHEN** dos dimensiones, indicadores o criterios tienen el mismo código pero pertenecen a versiones o padres distintos de su nivel
- **THEN** la persistencia permite ambos registros

### Requirement: Los modelos resumen conservan su estructura y asociaciones
Cada definición de modelo SHALL pertenecer a una versión, sus campos SHALL pertenecer a una definición, y la asociación entre criterios y definiciones SHALL conservar ambas referencias.

#### Scenario: Guardar campo y asociación de modelo
- **WHEN** se guarda una definición con campos y se relaciona con un criterio
- **THEN** los campos y la asociación conservan sus referencias a la definición, versión y criterio correspondientes

### Requirement: Las entidades de estructura tienen representación legible
Cada entidad de estructura SHALL proporcionar una representación textual no vacía que permita reconocer el registro por sus datos identificativos.

#### Scenario: Mostrar una entidad de estructura
- **WHEN** se convierte en texto cualquiera de las diez entidades de estructura
- **THEN** el resultado es informativo y no es la representación genérica de una instancia de objeto
