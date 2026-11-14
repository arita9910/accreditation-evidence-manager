# cuantitativos Specification

## Purpose
El módulo de cuantitativos debe permitir registrar los datos resumidos del Manual, mantener la trazabilidad con las evidencias que los respaldan y evitar inconsistencias en ciclos cerrados, permisos y vínculos entre registros. Esta capacidad está definida por el plan 09 y por las decisiones D-04 y D-05, que restringen el modelo a datos resumen y a valores de criterio sin modelo. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L1-L47), [docs/decisiones/README.md](../../../docs/decisiones/README.md#L30-L45).

## Requirements

### Requirement: Registro de valores de modelos resumen
El sistema SHALL permitir registrar los valores de los 11 modelos resumen del Manual con datos por ciclo, curso y campo, aplicando validaciones de tipo, rango, relación con el numerador/denominador y consistencia de totales según el modelo correspondiente. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L13-L27).

#### Scenario: Guardar valores válidos de un modelo
- **WHEN** un usuario con autorización válida registra celdas de un modelo resumen para un ciclo y curso con valores coherentes y no negativos
- **THEN** el sistema persiste cada valor y conserva la referencia al campo del modelo y al curso asociado

#### Scenario: Rechazar valor fuera del tipo permitido
- **WHEN** un valor de campo del modelo no coincide con el tipo esperado del campo o incluye un porcentaje o total incoherente
- **THEN** la operación falla y no persiste datos parcialmente válidos

#### Scenario: Copiar la acreditación anterior cuando exista
- **WHEN** el ciclo tiene un ciclo previo con información de acreditación anterior disponible
- **THEN** el servicio rellena el valor correspondiente a partir del ciclo anterior antes de validar y guardar la nueva información

### Requirement: Registro de valor por criterio cuantitativo sin modelo
El sistema SHALL permitir guardar el valor propio de un criterio cuantitativo solo cuando ese criterio no tiene modelo asociado, rechazando explícitamente la operación en los casos cualitativos o cuando el criterio ya depende de un modelo resumen. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L13-L27), [docs/origin-plans/01-modelo-de-datos.md](../../../docs/origin-plans/01-modelo-de-datos.md#L59-L67).

#### Scenario: Guardar valor de criterio sin modelo
- **WHEN** un usuario registra un valor por criterio en un criterio cuantitativo sin modelo
- **THEN** el sistema guarda el valor, el numerador, el denominador, la unidad y la observación asociada al ciclo y al criterio

#### Scenario: Rechazar valor de criterio cuando el criterio tiene modelo
- **WHEN** se intenta guardar un valor de criterio para un criterio que ya se alimenta desde un modelo resumen
- **THEN** la operación falla y el sistema informa que ese criterio no admite valor propio

### Requirement: Vinculación entre datos cuantitativos y evidencias
El sistema SHALL mantener un vínculo entre cada dato cuantitativo y una o varias evidencias, en ambos sentidos, garantizando que exactamente uno de los dos tipos de dato (`ValorModelo` o `ValorCriterio`) esté asociado a cada vínculo. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L17-L19), [docs/origin-plans/01-modelo-de-datos.md](../../../docs/origin-plans/01-modelo-de-datos.md#L59-L67).

#### Scenario: Vincular un dato con una evidencia
- **WHEN** un usuario asocia una evidencia a un dato cuantitativo válido
- **THEN** el sistema crea el vínculo y deja disponible la consulta del dato desde la evidencia y de la evidencia desde el dato

#### Scenario: Rechazar un vínculo ambiguo
- **WHEN** dos tipos de dato se enlazan simultáneamente en el mismo `VinculoDato`
- **THEN** la persistencia se rechaza y la operación queda sin efecto

#### Scenario: Consultar datos sin respaldo
- **WHEN** un dato cuantitativo no tiene ninguna evidencia asociada
- **THEN** el sistema lo incluye en la vista de datos sin respaldo para que pueda corregirse o vincularse

### Requirement: Restricciones de acceso y trazabilidad para cuantitativos
El sistema SHALL exigir que el ciclo esté abierto antes de escribir datos cuantitativos, aplicar las reglas de permisos centralizadas del módulo `cuentas` y registrar toda operación relevante del módulo en la auditoría del sistema. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L7-L27), [docs/decisiones/README.md](../../../docs/decisiones/README.md#L44-L55).

#### Scenario: Escritura bloqueada en ciclo cerrado
- **WHEN** un usuario intenta guardar un valor cuando el ciclo correspondiente no está abierto
- **THEN** la operación lanza la validación centralizada de ciclo abierto y se rechaza la escritura

#### Scenario: Miembro autorizado puede registrar datos de su ámbito
- **WHEN** un miembro asignado a una dimensión del ciclo intenta registrar datos de ese ámbito
- **THEN** la autorización permite la operación y la auditoría registra el detalle del negocio

#### Scenario: Usuario no autorizado es denegado
- **WHEN** un usuario sin permiso intenta registrar o consultar datos fuera del alcance autorizado
- **THEN** la solicitud queda denegada y se registra el acceso denegado correspondiente

### Requirement: API y pantalla previas a la implementación
La aplicación SHALL exponer los datos cuantitativos y sus vínculos mediante interfaces de consulta y escritura compatibles con la API REST del proyecto y con la interfaz React, sin definir la lógica interna de implementación en el contrato del sistema. Fuente: [docs/origin-plans/09-modulo-cuantitativos.md](../../../docs/origin-plans/09-modulo-cuantitativos.md#L27-L47).

#### Scenario: Consultar valores y vínculos por ciclo
- **WHEN** un usuario consulta los valores de un ciclo, un curso o una evidencia concreta
- **THEN** la API devuelve el conjunto de datos asociados y los vínculos activos con el mismo formato del resto del sistema

#### Scenario: Captura en interfaz por tabla y lista de sin respaldo
- **WHEN** la pantalla de cuantitativos se usa para editar los valores del modelo y mostrar los datos sin respaldo
- **THEN** la interfaz presenta los campos esperados, valida valores negativos y ofrece la lista de elementos que requieren evidencia
