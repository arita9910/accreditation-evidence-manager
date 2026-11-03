# Spec Delta

## Purpose

Precisar el contrato de configuración para mantener los ficheros privados de evidencias separados de las ubicaciones públicas de medios.

## ADDED Requirements

### Requirement: Separación de almacenamiento privado y medios públicos
La configuración de desarrollo y producción SHALL conservar `EVIDENCIAS_ROOT` como ubicación configurable y privada, independiente de `MEDIA_ROOT`. Las rutas públicas de medios y estáticos SHALL NOT servir el contenido de `EVIDENCIAS_ROOT`.

#### Scenario: Iniciar el servicio con raíces separadas
- **WHEN** se carga la configuración de desarrollo o producción
- **THEN** `EVIDENCIAS_ROOT` y `MEDIA_ROOT` resuelven a ubicaciones distintas y ninguna ruta pública de medios o estáticos expone las evidencias
