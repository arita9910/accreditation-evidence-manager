# Plan 04 — Módulo ciclos: organización y ciclos de evaluación (incremento 1)

## Objetivo
Gestionar facultades, carreras y ciclos de evaluación (apertura, cierre, ciclo anterior, categoría y vigencia) y la asignación de dimensiones a los miembros de la comisión.

## Convenciones comunes
- Django 5.2 + DRF; React 18 + Vite (JS); SQLite en desarrollo y PostgreSQL en producción, sin SQL propio de un gestor.
- Nombres en español. App `sistema/backend/ciclos/` con `modelos.py`, `servicios.py`, `serializadores.py`, `vistas.py`, `urls.py`, `tests/`. Lógica en servicios; vistas delgadas.
- API bajo `/api/`, JSON, sesión + CSRF. Permisos solo mediante `cuentas.permisos.puede(...)` (plan 05); registro con `auditoria.servicios.registrar(...)` (plan 06).
- Indicador = 2.º nivel; criterio = 3.er nivel. Ambigüedad → `docs/decisiones/`, no inventar.

## Contexto
Casos de uso CU-04 (gestionar carreras y ciclos) y CU-05 (asignar dimensiones). Depende de: plan 03 (VersionNormativa, Dimension). **Orden dentro del incremento 1:** ciclos → auditoría → cuentas. Como cuentas y auditoría aún no existen al empezar, implementar primero los modelos y servicios; los permisos y el registro se conectan al terminar los planes 06 y 05 (tarea T5).

## Entidades (plan 01, oleada B)
- **Facultad:** nombre. La crea el administrador técnico.
- **Carrera:** facultad (FK), nombre, activa.
- **Ciclo:** carrera (FK), version_normativa (FK), tipo (autoevaluación, acreditación, reacreditación), anio_base, curso_inicial, curso_final, estado (abierto/cerrado), ciclo_anterior (FK nula), categoria_obtenida (nula; **dato que se registra, no se calcula**), vigencia_anios (5, 7, 9 o nula), fecha_apertura, fecha_cierre.
- **AsignacionDimension:** ciclo (FK), usuario (FK), dimension (FK); único (ciclo, usuario, dimension).
Reglas: **un solo ciclo abierto por carrera** (restricción condicional); cinco cursos entre `curso_inicial` y `curso_final` (RM 160/2023, art. 70); el claustro se cuenta sobre el último curso concluido, el año base (art. 79); **un ciclo cerrado es solo lectura**; la vigencia es de 5, 7 o 9 años según la categoría (art. 13 de la RM 160/2023). **La correspondencia exacta categoría–años no está en estos documentos: consultarla en el artículo 13 del Reglamento (carpeta `normativa/`) antes de validarla**; hasta entonces, `vigencia_anios` solo admite 5, 7, 9 o nulo y se registra, no se calcula.

## Tareas

### T1 — Modelos y migraciones (oleada B parcial)
Entidades de arriba con sus restricciones y pruebas (ver `01-modelo-de-datos.md`).

### T2 — Servicios
- `crear_facultad`, `crear_carrera`, `abrir_ciclo(carrera, tipo, anio_base, curso_inicial, version_normativa, ciclo_anterior=None)`: comprueba que no hay otro abierto, que `ciclo_anterior` es de la misma carrera y está cerrado, que hay cinco cursos.
- `cerrar_ciclo(ciclo, categoria_obtenida=None, vigencia_anios=None)`: pasa a cerrado, fija `fecha_cierre`; valida que la vigencia sea 5, 7 o 9 y, una vez comprobada en el art. 13, su correspondencia con la categoría.
- `asignar_dimension(ciclo, usuario, dimension)` y `quitar_asignacion`; exige ciclo abierto y que el usuario sea miembro de la carrera del ciclo (cuando exista cuentas).
- Función reutilizable `exigir_ciclo_abierto(ciclo)` que lanzan los servicios de los demás módulos al escribir.
- **Aceptación (pruebas):** no se abren dos ciclos por carrera; ciclo anterior de otra carrera rechazado; cerrar fija fecha; un ciclo cerrado rechaza cambios y asignaciones; vigencia solo 5/7/9/nula; asignación duplicada rechazada.

### T3 — API
- `GET/POST /api/facultades/`, `GET/POST/PATCH /api/carreras/` (administrador técnico escribe; otros leen según ámbito).
- `GET /api/ciclos/` (filtrable por carrera y estado), `POST /api/ciclos/` (abrir), `GET /api/ciclos/{id}/`, `POST /api/ciclos/{id}/cerrar/`.
- `GET/POST/DELETE /api/ciclos/{id}/asignaciones/`.
- Paginación y errores estándar (plan 02).
- **Aceptación:** pruebas de la API, incluidos los códigos de error en español.

### T4 — Pantallas React
- Lista de carreras y sus ciclos con estado; formulario de apertura con aviso de los cinco cursos; cierre con categoría y vigencia opcionales; asignación de dimensiones a los miembros (tabla dimensión × usuario).
- **Aceptación (Vitest):** el formulario de apertura valida los campos; la tabla de asignación refleja la API.

### T5 — Conexión con cuentas y auditoría
Al terminar los planes 06 y 05: aplicar `puede(...)` en todas las vistas (abrir/cerrar/asignar solo el director de su carrera; crear facultad y carrera solo el administrador técnico) y llamar a `registrar(...)` en cada operación. Añadir las pruebas negativas de la matriz de permisos correspondientes (ver plan 05).

## Fuera de alcance
Roles y login (plan 05), auditoría (plan 06), contenido de los ciclos (planes 07 a 12).

## Definición de terminado
Modelos, servicios, API y pantallas probados; permisos y auditoría conectados; avance en `docs/avance/04-ciclos.md`.
