# docx-generation Specification

## Purpose

Define un prototipo aislado de generación DOCX para comprobar que la estructura y el formato iniciales pueden abrirse correctamente en procesadores de texto habituales.

## Requirements

### Requirement: Generar un documento DOCX de prueba
El sistema SHALL generar el informe real de autoevaluación como archivo DOCX editable y SHALL incluir el contenido de portada, caracterización, análisis por dimensión, plan de mejora, sostenibilidad y los 11 modelos anexos con datos del ciclo.

#### Scenario: Generación del informe real
- **WHEN** se solicita la versión DOCX de un ciclo
- **THEN** el archivo contiene las secciones obligatorias y los 11 modelos anexos con referencias legibles

#### Scenario: Revisión manual del resultado
- **WHEN** el responsable abre el informe generado en Word o LibreOffice
- **THEN** las secciones y tablas son visualmente utilizables y cualquier hallazgo queda anotado en el avance del incremento

#### Scenario: Generación del prototipo
- **WHEN** se ejecuta el prototipo DOCX original
- **THEN** el archivo generado sigue pudiendo contener texto, una tabla de modelo resumen y un salto de sección

### Requirement: Aplicar formato base al prototipo
El informe SHALL aplicar Arial de 12 puntos e interlineado sencillo al cuerpo y SHALL conservar tablas legibles y el formato de porcentajes con su relación de origen.

#### Scenario: Formato del informe real
- **WHEN** se inspecciona el DOCX generado
- **THEN** el cuerpo usa Arial de 12 puntos, interlineado sencillo y tablas legibles

#### Scenario: Porcentajes referenciados
- **WHEN** el informe contiene porcentajes calculados
- **THEN** cada porcentaje muestra su relación numérica de origen

#### Scenario: Verificación del formato
- **WHEN** se inspecciona el prototipo DOCX base
- **THEN** el contenido conserva Arial de 12 puntos y espaciado sencillo

### Requirement: Verificar apertura del documento
El resultado del informe SHALL poder abrirse en Word o LibreOffice y SHALL conservarse como documento editable sin requerir PDF, firma electrónica o edición interna.

#### Scenario: Apertura y registro del resultado
- **WHEN** se prueba el documento generado en Word o LibreOffice
- **THEN** el documento se abre correctamente como DOCX editable o el hallazgo observado queda documentado en el avance
