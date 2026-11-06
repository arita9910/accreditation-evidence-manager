# estructura-normativa Specification

## Purpose

Define la persistencia versionada de la estructura normativa y de sus relaciones de consulta, de modo que los módulos posteriores puedan referirse a dimensiones, indicadores, criterios y modelos sin duplicar el catálogo.

## Requirements

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

### Requirement: El catálogo normativo se carga de forma validada y repetible
La carga del catálogo SEA-CU 2025 SHALL crear o actualizar los registros de la versión y sus entidades por claves naturales, sin duplicarlos al repetirse, y SHALL verificar los totales esperados antes de informar éxito.

#### Scenario: Carga correcta del catálogo
- **WHEN** se carga el catálogo disponible con 6 dimensiones, 24 indicadores y 65 criterios
- **THEN** quedan registrados esos totales, las evidencias y requisitos presentes en los datos, y el criterio 3.2.4 queda identificado como solo de la Guía

#### Scenario: Repetición de una carga
- **WHEN** se vuelve a cargar la misma versión
- **THEN** se actualizan sus registros correspondientes sin crear duplicados ni cambiar la versión normativa referenciada por ciclos existentes

#### Scenario: Totales de entrada incorrectos
- **WHEN** el archivo de entrada no permite validar la estructura esperada o sus totales no son 6/24/65
- **THEN** la carga falla explícitamente y no informa éxito parcial

#### Scenario: Faltan valores obligatorios sin fuente
- **WHEN** faltan valores fuente requeridos por los modelos existentes
- **THEN** la carga informa cuáles faltan y se detiene antes de crear o actualizar registros

### Requirement: El catálogo ofrece consultas de solo lectura
La API SHALL exponer el árbol de la versión activa, la ficha de un criterio, los modelos con sus campos y las versiones disponibles, sin permitir escrituras por esos recursos.

#### Scenario: Consultar el árbol
- **WHEN** se solicita el árbol del catálogo
- **THEN** la respuesta organiza dimensiones, indicadores y criterios e incluye el código, texto resumido, tipo de dato y marca de solo en la Guía de cada criterio

#### Scenario: Consultar una ficha de criterio
- **WHEN** se solicita la ficha de un código existente
- **THEN** la respuesta incluye texto completo, códigos normativos disponibles, tipo de dato, evidencias, requisitos por categoría como referencia, nota normativa y modelos relacionados

#### Scenario: Consultar código inexistente o usar escritura
- **WHEN** se consulta un código inexistente o se intenta escribir en cualquiera de los recursos del catálogo
- **THEN** la API responde respectivamente con el error estándar de recurso inexistente o método no permitido

#### Scenario: Habilitación del catálogo en desarrollo
- **WHEN** el catálogo se consulta con la habilitación de desarrollo apagada, o se configura esa habilitación en producción
- **THEN** la API no expone el catálogo y la configuración de producción rechaza esa habilitación

### Requirement: El catálogo se puede explorar desde la interfaz
La interfaz SHALL permitir explorar la jerarquía normativa y consultar la ficha de cada criterio sin editar el catálogo ni calcular una categoría de acreditación.

#### Scenario: Buscar y abrir un criterio
- **WHEN** se busca por código o texto y se selecciona un criterio
- **THEN** se muestra el árbol jerárquico y la ficha con sus evidencias, nota normativa y modelos relacionados

#### Scenario: Mostrar particularidades del catálogo
- **WHEN** se visualiza un criterio que solo aparece en la Guía o que tiene requisito por categoría
- **THEN** la interfaz lo identifica claramente, presenta el requisito como referencia y advierte que el sistema no calcula la categoría
