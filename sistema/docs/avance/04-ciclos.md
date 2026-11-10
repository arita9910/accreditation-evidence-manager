# Avance del plan 04: módulo de ciclos

## Estado final del cambio

El cambio de ciclos queda consolidado en el modelo, en la capa de servicios y en la API. El dominio define un ciclo como una entidad asociada a una carrera y a una versión normativa, con un rango fijo de cinco cursos y una única ventana abierta por carrera. La validación de negocio está centralizada en el modelo y en el servicio de apertura/cierre, y la pantalla de React permite gestionar la apertura, el cierre y las asignaciones de dimensiones sin salir de una vista única.

## Modelo de dominio y reglas de negocio

En `ciclos/modelos.py` el modelo `Ciclo` incluye:

- `carrera`: relación con la carrera a la que pertenece el ciclo.
- `version_normativa`: vínculo con la normativa vigente del ciclo.
- `tipo`, `anio_base`, `curso_inicial`, `curso_final`: datos básicos del periodo académico.
- `estado`: `abierto` o `cerrado`.
- `ciclo_anterior`: relación recursiva con el ciclo precedente, útil para encadenar periodos académicos de la misma carrera.
- `categoria_obtenida`, `vigencia_anios`, `fecha_apertura`, `fecha_cierre`: metadatos del cierre y la acreditación.

La restricción principal es que sólo puede existir un ciclo abierto por carrera. Esta regla se materializa con una `UniqueConstraint` sobre `(carrera,)` cuando `estado = 'abierto'`, y se refuerza en el servicio de negocio para impedir la apertura de una segunda ventana antes de cerrar la actual.

La cadena `ciclo_anterior` tiene un doble propósito: documentar continuidad entre ciclos y asegurar que la transición se hace sobre un ciclo cerrado y de la misma carrera. El modelo rechaza el autovínculo, exige que el ciclo previo pertenezca a la misma carrera y que su estado sea `cerrado`. Esto evita encadenamientos entre carreras o ciclos todavía activos.

Además, la validación del rango exige que `curso_final = curso_inicial + 4`, de modo que cada ciclo cubre exactamente cinco cursos académicos. La vigencia también queda acotada a valores válidos (`5`, `7`, `9`) o `null`, que es la forma de representar ausencia de vigencia determinada.

## Validaciones de los cinco cursos y el cierre

La regla del rango de cinco cursos se aplica tanto en la base de datos como en la lógica del modelo:

- `CheckConstraint`: `curso_final = curso_inicial + 4`.
- El servicio `abrir_ciclo(...)` calcula el cierre automático del rango usando `curso_inicial + 4` y rechaza cualquier valor no coherente con la regla.
- Cuando un ciclo está cerrado, el modelo lo vuelve de solo lectura para campos clave (`carrera`, `version_normativa`, `tipo`, `anio_base`, `curso_inicial`, `curso_final`, `estado`, `ciclo_anterior`, `categoria_obtenida`, `vigencia_anios`, `fecha_apertura`, `fecha_cierre`).
- Un ciclo abierto no puede tener `fecha_cierre`; un ciclo cerrado debe tenerla.

Esto garantiza que la historia del ciclo no pueda alterarse retroactivamente una vez cerrada la ventana, preservando la trazabilidad del proceso de acreditación.

## API de ciclos

La capa REST expone los recursos del dominio en `ciclos/vistas.py` y `ciclos/serializadores.py`:

- `GET /api/ciclos/` y `POST /api/ciclos/`: listado y apertura de ciclos.
- `GET /api/ciclos/<pk>/`: detalle del ciclo.
- `POST /api/ciclos/<pk>/cerrar/`: cierre validado del ciclo, con `categoria_obtenida` y `vigencia_anios` opcionales.
- `GET /api/ciclos/<pk>/asignaciones/`, `POST /api/ciclos/<pk>/asignaciones/` y `DELETE /api/ciclos/<pk>/asignaciones/`: gestión de asignaciones de dimensiones a personas dentro del ciclo abierto.

La API no admite abrir un ciclo sin permisos ni con un ciclo anterior inexistente o incompatible; la validación se dispara antes de guardar, y el servicio registra la acción con `auditoria.registrar(...)` para dejar trazabilidad centralizada.

## Pantalla de React

La pantalla `sistema/frontend/src/paginas/Ciclos.jsx` incorpora la operativa completa del módulo:

- formulario de apertura con carrera, tipo, año base, curso inicial, versión normativa y posible ciclo anterior;
- cálculo del curso final sugerido (`curso_inicial + 4`);
- validación de errores de formulario antes de enviar la petición;
- listado de ciclos por carrera, con estado abierto/cerrado y detalle visible;
- formulario de cierre por ciclo, incluyendo `categoria_obtenida` y `vigencia_anios`;
- gestión de asignaciones de dimensiones a usuarios, restringida a un ciclo abierto seleccionado.

La cliente de la API (`src/api/cliente.js`) reenvía todas las llamadas a `/api`, mantiene `credentials: 'include'` para las sesiones y añade `X-CSRFToken` en operaciones mutables cuando existe un token CSRF. La capa visual usa mensajes de éxito y error reutilizables para una experiencia consistente.

## Verificaciones ejecutadas (SQLite)

- `python manage.py test ciclos --verbosity 2`
  - Resultado: **la suite de modelo y servicios de ciclos queda aprobada sobre SQLite**, cubriendo apertura, cierre, única ventana abierta, encadenamiento con `ciclo_anterior`, validación de rango y asignación de dimensiones.
- `npm run test:run -- --pool=vmThreads --maxWorkers=1`
  - Resultado: **la pantalla de ciclos se valida con Vitest** y la lógica de formulario/errores queda integrada en la UI.

## Revisión de artefactos y alineación

- **Modelo**: `Ciclo` en `ciclos/modelos.py` cubre la entidad, las relaciones y las restricciones de negocio.
- **Servicio**: `abrir_ciclo(...)`, `cerrar_ciclo(...)`, `asignar_dimension(...)` y `quitar_asignacion(...)` centralizan reglas y mantención de auditoría.
- **API**: los endpoints de ciclo y asignación quedan alineados con la lógica del dominio y con la política de permisos del sistema.
- **Frontend**: la vista React refleja exactamente el flujo funcional del dominio y aporta validación visual antes de la llamada al backend.

## Pendientes

- PostgreSQL queda como comprobación pendiente documentada conforme a D-14; en la validación del plan solo se ejecutó la verificación sobre SQLite.
- La revisión de la asignación de dimensiones por rol concreto de usuario puede ampliarse en un siguiente incremento, pero no bloquea el cierre del módulo de ciclos.
