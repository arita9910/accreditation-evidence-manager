# Spec Delta

## Purpose

Define un prototipo aislado de generación DOCX para comprobar que la estructura y el formato iniciales pueden abrirse correctamente en procesadores de texto habituales.

## ADDED Requirements

### Requirement: Generar un documento DOCX de prueba
El prototipo SHALL generar un archivo DOCX que incluya texto, una tabla de un modelo resumen y un salto de sección.

#### Scenario: Generación del prototipo
- **WHEN** se ejecuta el prototipo DOCX
- **THEN** se produce un documento que contiene texto, una tabla de un modelo resumen y un salto de sección

### Requirement: Aplicar formato base al prototipo
El prototipo SHALL aplicar Arial de 12 puntos e interlineado sencillo al contenido del documento.

#### Scenario: Verificación del formato
- **WHEN** se inspecciona el DOCX generado
- **THEN** el texto usa Arial de 12 puntos y espaciado sencillo

### Requirement: Verificar apertura del documento
El resultado del prototipo SHALL poder abrirse en Word o LibreOffice y cualquier fallo observado SHALL quedar anotado en el avance del incremento.

#### Scenario: Apertura y registro del resultado
- **WHEN** se prueba el documento generado en Word o LibreOffice
- **THEN** el documento se abre correctamente o el fallo observado queda documentado en el avance del incremento
