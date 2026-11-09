# ciclos Specification

## Purpose

Definir la gestión de facultades, carreras, ciclos de evaluación y asignación de dimensiones para la organización de la acreditación, manteniendo las reglas de negocio del plan 04 y dejando preparada la integración posterior con permisos y auditoría.

## ADDED Requirements

### Requirement: Gestión de facultades y carreras
La aplicación SHALL permitir registrar facultades con nombre y carreras vinculadas a una facultad, con un campo `activa` que indique el estado operativo de la carrera.

#### Scenario: Crear una facultad y una carrera
- **WHEN** un administrador técnico crea una facultad y después registra una carrera asociada a ella
- **THEN** ambos registros quedan persistidos con su relación de pertenencia y la carrera conserva su estado activo o no activo

### Requirement: Apertura y cierre de ciclos de evaluación
El sistema SHALL permitir abrir ciclos vinculados a una carrera y a una versión normativa, con tipo, año base, curso inicial, curso final, estado, ciclo anterior opcional, categoría registrada, vigencia y fechas de apertura y cierre.

#### Scenario: Abrir un ciclo válido
- **WHEN** se abre un ciclo con una carrera válida, cinco cursos consecutivos y un ciclo anterior cerrado de la misma carrera
- **THEN** el ciclo queda en estado abierto con la información de fecha de apertura y la referencia a la versión normativa y carrera correspondientes

#### Scenario: Rechazar apertura cuando ya existe otro ciclo abierto
- **WHEN** una carrera ya tiene un ciclo abierto
- **THEN** la apertura de otro ciclo para la misma carrera falla y no crea un segundo ciclo abierto simultáneamente

### Requirement: Restricciones de integridad del ciclo
La lógica de negocio SHALL impedir que un ciclo anterior pertenezca a otra carrera, exigir cinco cursos entre `curso_inicial` y `curso_final` y reservar la edición de un ciclo cerrado como solo lectura.

#### Scenario: Ciclo anterior de otra carrera
- **WHEN** se intenta utilizar un ciclo anterior asociado a una carrera distinta
- **THEN** la validación rechaza la operación y mantiene la consistencia de la relación

#### Scenario: Curso inicial y final no cumplen la regla de cinco cursos
- **WHEN** la diferencia entre curso inicial y final no alcanza el mínimo requerido
- **THEN** el servicio indicador de apertura no acepta la creación del ciclo

#### Scenario: Intentar modificar un ciclo cerrado
- **WHEN** un ciclo ya está cerrado
- **THEN** las operaciones de escritura se rechazan y la entidad queda en modo de solo lectura

### Requirement: Registro de categoría y vigencia
El sistema SHALL almacenar `categoria_obtenida` como dato registrado y `vigencia_anios` como valor nulo o 5, 7 o 9 años, sin calcular la vigencia a partir de la categoría en este incremento.

#### Scenario: Cerrar con vigencia y categoría
- **WHEN** se cierra un ciclo con una categoría registrada y una vigencia válida
- **THEN** el cierre actualiza `fecha_cierre`, guarda `categoria_obtenida` y conserva `vigencia_anios` con uno de los valores permitidos

#### Scenario: Vigencia no permitida
- **WHEN** se intenta cerrar con una vigencia distinta de 5, 7, 9 o nula
- **THEN** la operación rechaza la entrada con validación explícita

#### Scenario: Relación categoría-vigencia pendiente de confirmación normativa
- **WHEN** el equipo necesita validar la correspondencia exacta entre categoría y años de vigencia
- **THEN** el sistema no calcula esa relación automáticamente y deja la pregunta abierta hasta consultar la normativa y consolidarla con el tutor

### Requirement: Asignación de dimensiones
El módulo SHALL permitir asociar una dimensión a un usuario dentro de un ciclo concreto, con unicidad por pareja `(ciclo, usuario, dimensión)` y sin permitir duplicados.

#### Scenario: Asignar una dimensión válida
- **WHEN** se asigna a un usuario una dimensión dentro de un ciclo abierto y con la relación correcta
- **THEN** la asociación queda registrada y puede consultarse por ciclo y usuario

#### Scenario: Duplicar una asignación
- **WHEN** se intenta asignar la misma dimensión al mismo usuario dentro del mismo ciclo dos veces
- **THEN** la operación falla y evita la duplicación

#### Scenario: Asignación en ciclo cerrado
- **WHEN** se intenta asignar una dimensión a una comisión cuando el ciclo ya está cerrado
- **THEN** el sistema rechaza la operación por la regla de solo lectura

### Requirement: Reutilización de validación para módulos dependientes
La capa de servicios SHALL exponer una validación reutilizable para exigir que un ciclo esté abierto antes de escribir datos dependientes del módulo.

#### Scenario: Invocar la validación en otro módulo
- **WHEN** un servicio de otro módulo intenta escribir sobre un ciclo no abierto
- **THEN** la validación centralizada lanza el error correspondiente en lugar de duplicar la lógica local

### Requirement: API y pantalla del módulo
La API y la interfaz SHALL exponer las operaciones esenciales de consulta y escritura del módulo: facultades, carreras, ciclos y asignaciones de dimensiones, con errores y paginación compatibles con los estándares del proyecto.

#### Scenario: Consultar catálogo y ciclos
- **WHEN** un usuario consulta facultades, carreras o ciclos con filtros de carrera y estado
- **THEN** recibe los resultados paginados y con los mensajes de error en español del proyecto

#### Scenario: Abrir y cerrar desde la UI
- **WHEN** el formulario de apertura y cierre se usa en la interfaz
- **THEN** la aplicación valida los campos requeridos, comunica los avisos de cinco cursos y refleja la respuesta de la API en la pantalla
