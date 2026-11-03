# Plan 10 — Módulo mejora: plan de mejora y seguimiento (incremento 3)

## Objetivo
Gestionar el plan de mejora del ciclo: acciones originadas en debilidades, con responsable y plazo, y su seguimiento hasta el cumplimiento, con evidencias que lo acreditan.

## Convenciones comunes
- Django 5.2 + DRF; React 18 + Vite (JS); SQLite en desarrollo y PostgreSQL en producción.
- Nombres en español. App `sistema/backend/mejora/` con `modelos.py`, `servicios.py`, `serializadores.py`, `vistas.py`, `urls.py`, `tests/`. Lógica en servicios; vistas delgadas.
- API bajo `/api/`, JSON, sesión + CSRF. Permisos con `cuentas.permisos.puede(...)`; auditoría con `registrar(...)`; escrituras exigen ciclo abierto.
- Indicador = 2.º nivel; criterio = 3.er nivel. Ambigüedad → `docs/decisiones/`.

## Contexto
CU-15 (gestionar el plan de mejora) y CU-16 (dar seguimiento). Depende de planes 08 (debilidades), 07 (evidencias), 04. El informe debe valorar cómo se resolvió el plan del ciclo anterior, por eso el plan del ciclo anterior debe ser visible desde el nuevo.

## Entidades (plan 01, oleada D)
- **PlanMejora:** ciclo (FK), estado, aprobado_por. Uno por ciclo.
- **AccionMejora:** plan (FK), debilidad (FK a Valoracion con tipo debilidad), descripcion, responsable (FK Usuario), fecha_limite, estado (propuesta, aprobada, en curso, cumplida, no cumplida), valoracion_resultado. **No existe acción sin debilidad de origen.**
- **SeguimientoAccion:** accion (FK), fecha, avance, nota, registrado_por. Solo inserción.
- **AccionEvidencia:** accion (FK), evidencia (FK).

## Tareas

### T1 — Modelos, migraciones y pruebas (debilidad obligatoria y de tipo debilidad; SeguimientoAccion de solo inserción, igual que la auditoría).

### T2 — Servicios
- `proponer_accion(plan, debilidad, descripcion, responsable, fecha_limite, usuario)` (miembro o director); `aprobar_accion` (director); transiciones de estado válidas: propuesta → aprobada → en curso → cumplida | no cumplida; cualquier otra transición se rechaza.
- `registrar_seguimiento(accion, avance, nota, usuario)`: el responsable o el director; cada cambio de estado deja un seguimiento y un registro de auditoría.
- `vincular_evidencia(accion, evidencia)`.
- `acciones_vencidas(plan)`: fecha límite pasada y estado no final.
- `plan_ciclo_anterior(ciclo)`: devuelve el plan y el estado final de sus acciones.
- **Aceptación (pruebas):** no hay acción sin debilidad; transiciones inválidas rechazadas; los cambios de estado quedan en el historial y en la auditoría; el miembro solo da seguimiento a sus acciones; decano y rector solo consultan; vencidas calculadas bien.

### T3 — API
`GET/POST /api/ciclos/{id}/plan/`, `GET/POST /api/planes/{id}/acciones/`, `PATCH /api/acciones/{id}/` (incluye cambio de estado vía `POST /api/acciones/{id}/estado/`), `GET/POST /api/acciones/{id}/seguimientos/`, `POST /api/acciones/{id}/evidencias/`, `GET /api/ciclos/{id}/plan-anterior/`. **Aceptación:** pruebas de API con permisos positivos y negativos.

### T4 — Pantallas React
Plan del ciclo con las acciones y las vencidas resaltadas; proponer acción desde una debilidad; aprobación; registro de seguimiento con historial; vista del plan del ciclo anterior junto al nuevo. **Aceptación (Vitest):** las vencidas se resaltan; no se puede crear una acción sin elegir debilidad.

## Fuera de alcance
Notificaciones por correo, diagramas de Gantt, indicadores de impacto de las acciones.

## Definición de terminado
Pruebas en verde; flujo debilidad → acción → seguimiento → cumplimiento funcionando; avance en `docs/avance/10-mejora.md`.
