# Proposal

## Why

El módulo de ciclos requiere organizar la información de facultades, carreras y periodos de evaluación para poder abrir, cerrar y controlar la vigencia de los ciclos, además de asignar dimensiones a la comisión de acuerdo con la normativa vigente. El incremento 1 debe preparar esta base de dominio antes de conectar permisos y auditoría, porque la lógica de negocio de ciclos es la pieza central que permitirá que los siguientes módulos trabajen sobre una estructura estable y consistente.

## What Changes

- Se introduce la capacidad de registrar facultades y carreras dentro del sistema, con la separación de ámbito por facultad y la marca de activación de la carrera.
- Se añade la gestión de ciclos de evaluación con sus datos principales: tipo, año base, cursos, estado, ciclo anterior, categoría registrada, vigencia y fechas de apertura/cierre.
- Se incorpora la asignación de dimensiones a los miembros de la comisión, restringida a un ciclo abierto y con unicidad por ciclo, usuario y dimensión.
- Se establecen las reglas de negocio clave del módulo: un único ciclo abierto por carrera, validación de cinco cursos, cierre de ciclos, restricción de lectura sobre ciclos cerrados y validación de vigencia 5/7/9/nula.
- Se prepara la capa de servicios y API para que el módulo quede listo para conectar permisos y auditoría en incrementos posteriores.

## Capabilities

### New Capabilities
- `ciclos`: capacidad para gestionar facultades, carreras, ciclos de evaluación y asignaciones de dimensiones de la comisión, con reglas de negocio y restricciones de estado definidas en el plan 04.

### Modified Capabilities
- Ninguna. Este incremento introduce un nuevo comportamiento de dominio y no modifica una capacidad existente ya declarada en `openspec/specs/`.

## Impact

- Backend Django + DRF: modelos, servicios, validaciones y rutas de API del módulo `sistema/backend/ciclos/`.
- Frontend React + Vite: listados, formularios de apertura y cierre, y tabla de asignación de dimensiones.
- Dependencia de la versión normativa (`VersionNormativa`) y de la estructura de dimensiones (`Dimension`), ya definidas por el plan 03.
- Requiere coordinación futura con los planes 05 y 06 para permisos y auditoría, sin incluir esas decisiones dentro del alcance de este incremento.
