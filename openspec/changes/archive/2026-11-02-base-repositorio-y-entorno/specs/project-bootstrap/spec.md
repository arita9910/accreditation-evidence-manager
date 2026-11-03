# Spec Delta

## Purpose

Define un proceso reproducible para preparar y arrancar el proyecto desde un checkout limpio, tanto con conexión de red como usando un almacén local de dependencias.

## ADDED Requirements

### Requirement: Instalación y arranque desde un checkout limpio
El proyecto SHALL documentar los requisitos previos y los pasos necesarios para instalar y arrancar backend y frontend desde un checkout limpio en el entorno de desarrollo objetivo.

#### Scenario: Desarrollo en el entorno Windows objetivo
- **WHEN** una persona sigue la documentación en un equipo Windows 10 sin Docker ni WSL2 y con las herramientas previas requeridas
- **THEN** puede preparar Python 3.12.16, Node v24.22.1, npm 11.19.1 y Git 2.56.0, crear `.venv` con `uv venv --python 3.12`, instalar las dependencias e iniciar backend y frontend por separado con sus servidores de desarrollo

### Requirement: Instalación sin conexión con dependencias preparadas
El proyecto SHALL proporcionar un procedimiento para preparar dependencias locales y otro para instalarlas sin conexión cuando el almacén local esté completo.

#### Scenario: Instalación sin acceso a red
- **WHEN** el almacén local contiene las dependencias requeridas y el equipo no tiene conexión a internet
- **THEN** los procedimientos permiten instalar las dependencias de backend y frontend sin descargarlas de la red

### Requirement: Exclusión de artefactos locales
El control de versiones SHALL excluir el almacén local de paquetes y los archivos generados o sensibles de desarrollo, incluidos bases de datos locales, archivos de evidencia y logs.

#### Scenario: Revisión de archivos ignorados
- **WHEN** se crean paquetes descargados, datos locales de desarrollo, evidencias o logs dentro de sus ubicaciones configuradas
- **THEN** esos artefactos no aparecen como archivos pendientes de seguimiento en Git

### Requirement: Datos normativos versionados
El repositorio SHALL mantener el catálogo SEA-CU 2025 v3 y las definiciones de los once modelos resumen como archivos de datos, conservando el contenido de las fuentes verificadas y marcando como pendientes los datos que aún no estén disponibles.

#### Scenario: Validar los datos iniciales
- **WHEN** se validan los archivos de datos versionados y la codificación de la fuente CSV
- **THEN** el catálogo contiene 6 dimensiones, 24 indicadores y 65 criterios sin caracteres acentuados corrompidos; si no se puede determinar la codificación original con certeza, la discrepancia queda documentada y no se corrige por conjetura, y las definiciones contienen once modelos sin inventar celdas fuente no disponibles
