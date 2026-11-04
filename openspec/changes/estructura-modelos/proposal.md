# Proposal

## Why

La app Django `estructura` está registrada en `INSTALLED_APPS`, pero aún no tiene los modelos que el Plan 01 asigna a la oleada A. Añadirlos habilita la persistencia de la estructura normativa reutilizando `ModeloBase` y deja verificadas las claves de unicidad antes de implementar el catálogo en un cambio posterior.

## What Changes

- Añadir a `estructura` los diez modelos de oleada A: `VersionNormativa`, `Dimension`, `Indicador`, `Criterio`, `EvidenciaSugerida`, `RequisitoCategoria`, `TipoEvidencia`, `ModeloDefinicion`, `ModeloCampo` y `CriterioModelo`, heredando de `nucleo.ModeloBase`.
- Crear una sola migración de estructura, con restricciones de unicidad de la restricción 1 y claves foráneas protegidas por defecto; usar `CASCADE` solo para hijos sin sentido sin su padre.
- Añadir pruebas SQLite para la restricción 1 y para las representaciones `__str__` útiles de los modelos.
- Excluir la carga de datos del catálogo, API y pantallas del Plan 03.

## Capabilities

### New Capabilities

- `estructura-normativa`: persistencia de versiones normativas y de sus dimensiones, indicadores, criterios, evidencias/requisitos relacionados y modelos de datos asociados.

### Modified Capabilities

Ninguna.

## Impact

- Afecta a `sistema/backend/estructura/` (modelos, pruebas y una migración inicial).
- Reutiliza `nucleo.ModeloBase` y el usuario configurado en Django; no modifica `nucleo` ni `cuentas`.
- No añade dependencias ni cambia API, interfaz o carga de catálogo. La validación de migración y pruebas de esta oleada se limita a SQLite, conforme a D-14.
