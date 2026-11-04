# Design

## Context

La app `estructura` está instalada y declara `BigAutoField`, pero hoy solo contiene su configuración; no tiene modelos ni migraciones. `nucleo` ya expone `ModeloBase` desde `modelos.py` a través de `models.py`; la clase base es abstracta e incluye marcas de tiempo y referencias anulables al usuario configurado. El Plan 01 enumera los campos y relaciones de las diez entidades y establece `PROTECT` por defecto. El backend usa Django 5.2 y SQLite en desarrollo; D-14 exige que migraciones y restricciones se prueben en SQLite, sin SQL específico del gestor.

## Goals / Non-Goals

**Goals:**
- Representar las diez entidades de la oleada A y las relaciones descritas en el Plan 01.
- Aplicar la unicidad acordada por padre para cada nivel de código, probarla en SQLite y dar a cada entidad una representación textual útil.
- Entregar una sola migración de estructura, sin alterar migraciones existentes.

**Non-Goals:**
- Cargar ni corregir los datos del catálogo o las definiciones de los once modelos.
- Añadir servicios de catálogo, API, permisos o pantallas.
- Modificar `ModeloBase`, el modelo de usuario o las entidades de otros planes.

## Decisions

1. **Mantener los modelos en la app `estructura` y reutilizar el patrón de `nucleo`.** Definir las clases en `estructura/modelos.py` y exponerlas desde `estructura/models.py` para que Django las descubra y genere migraciones. Alternativa descartada: poner todo en `apps.py` o crear otro módulo de dominio, porque no coincide con la convención ya presente.
2. **Usar `ModeloBase` y las relaciones padre-hijo del Plan 01.** Las entidades heredan de la clase abstracta compartida; las relaciones de la estructura apuntan a sus padres indicados por el plan. Las claves foráneas usan `PROTECT` salvo registros que no tienen sentido sin su padre, para los que se usa `CASCADE` (el plan cita `EvidenciaSugerida` como ejemplo). Alternativa descartada: duplicar campos de autoría o permitir borrados en cascada indiscriminados.
3. **Aplicar unicidad compuesta al padre de cada nivel.** Usar las parejas `(version, codigo)` para `Dimension`, `(dimension, codigo)` para `Indicador` y `(indicador, codigo)` para `Criterio`, tal como precisó la persona solicitante. Mantener las restricciones en el esquema ORM para que Django las exprese en SQLite y PostgreSQL. Alternativa descartada: validar solo en Python, que no protege frente a escrituras concurrentes.
4. **Mantener una migración inicial y pruebas de la app.** Incluir los diez modelos en una migración de `estructura`; Django gestionará la dependencia con el usuario configurado por los campos heredados. Las pruebas usarán el `TestCase` de Django y la configuración SQLite del proyecto. No se generará SQL manual ni se probará PostgreSQL en esta oleada.
5. **No fijar detalles de dominio no definidos por las fuentes.** Usar únicamente campos, valores enumerados, reglas y relaciones respaldados por el Plan 01 y documentos de origen; las convenciones del plan especifican `TextChoices` para opciones y `TextField` para texto largo. No añadir restricciones, valores de catálogo, límites o formato exacto de `__str__` no indicados allí.

## Risks / Trade-offs

- [Los planes no fijan todos los tipos, longitudes o formatos textuales de cada campo] → Aplicar solo las convenciones y datos fuente disponibles; si un detalle necesario para el esquema no puede derivarse de ellos, pedir decisión antes de introducirlo.
- [Las restricciones únicas se evalúan al escribir en la base de datos] → Aislar en transacción los casos negativos de prueba para que una violación no contamine el resto de la suite.
- [D-14 no requiere validar PostgreSQL en este incremento] → Mantener las restricciones estándar de Django y registrar la verificación de esta oleada como SQLite, sin afirmar que se ejecutó en PostgreSQL.

## Migration Plan

1. Crear la migración inicial de `estructura` con el esquema completo de las diez entidades.
2. Aplicarla con la configuración de desarrollo SQLite y comprobar que el estado de migraciones queda consistente.
3. Ejecutar las pruebas SQLite de la restricción 1 y de `__str__` para los diez modelos.
4. No cargar datos ni realizar backfill. Antes de que otros cambios dependan de estas tablas, se puede revertir la migración inicial; una vez aplicada y usada, los cambios de esquema se harán con migraciones posteriores, no editando la ya aplicada.
