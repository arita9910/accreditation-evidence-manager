# Tasks

## 1. Modelos y representación

- [ ] 1.1 Crear los diez modelos de estructura con los campos y relaciones del Plan 01, heredando de `nucleo.ModeloBase` y exponiéndolos para el descubrimiento de Django; verificar con `python manage.py check` desde `sistema/backend`.
- [ ] 1.2 Implementar una representación `__str__` informativa para cada modelo y añadir pruebas de los diez casos; verificar con `python manage.py test estructura` usando SQLite.

## 2. Integridad de códigos

- [ ] 2.1 Aplicar las restricciones compuestas para dimensión `(version, codigo)`, indicador `(dimension, codigo)` y criterio `(indicador, codigo)`; probar que cada duplicado bajo el mismo padre falla y que el mismo código bajo otro padre se admite; verificar con `python manage.py test estructura` usando SQLite.

## 3. Migración e integración SQLite

- [ ] 3.1 Generar una única migración inicial que incluya los diez modelos, aplicarla en SQLite y comprobar que el esquema está al día; verificar con `python manage.py migrate`, `python manage.py makemigrations --check --dry-run` y `python manage.py test estructura`, todos desde `sistema/backend`.

## Workflow follow-up

- TODO (fuera de este cambio): generar/actualizar los diagramas del modelo de datos a partir de los Anexos A/B de Condiciones cuando estén disponibles; no inventarlos ni generarlos en este cambio.
