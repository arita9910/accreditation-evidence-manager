# Spec Delta

## ADDED Requirements

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
