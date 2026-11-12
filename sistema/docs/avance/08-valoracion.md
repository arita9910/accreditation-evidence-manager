# Avance del plan 08: módulo de valoración

## Estado del bloque implementado

En esta iteración queda completado el cierre del plan 08: se corrigió la carga de catálogo para la pantalla de valoraciones y se ejecutó la batería de pruebas del módulo (tarea 5.1) en verde.

## Ajuste de usabilidad posterior al cierre

Se corrigió el asistente de porcentaje en la pantalla de valoraciones para que el campo **Porcentaje (%)** sea de solo lectura y se calcule automáticamente con base en **Numerador/Denominador**, redondeado a un decimal.

- El porcentaje ahora se vacía y muestra error cuando el denominador es `0`.
- El porcentaje ahora se vacía y muestra error cuando el numerador supera al denominador.
- Se mantuvo el flujo del botón **Insertar porcentaje**, conservando el formato `xx,x % (n/d)` en el texto principal.

## Verificaciones ejecutadas (SQLite)

- `Set-Location "D:\tesis-app\accreditation-evidence-manager\sistema\backend"; & "D:\tesis-app\accreditation-evidence-manager\.venv\Scripts\python.exe" manage.py test valoracion`
  - Resultado: **13 pruebas aprobadas** (modelo, servicios y API del módulo de valoración).
- `Set-Location 'D:\tesis-app\accreditation-evidence-manager\sistema\frontend'; npm run test:run -- --pool=vmThreads --maxWorkers=1 src/paginas/Valoraciones.test.jsx`
  - Resultado: **5 pruebas aprobadas** en Vitest para la pantalla de valoraciones (editor por tipo, asistente de porcentaje y validaciones de formulario).

## Implementación del cierre

- Se corrigió la obtención de dimensiones/criterios en `Valoraciones.jsx` para usar el endpoint del módulo de valoración por ciclo (`/api/ciclos/{id}/valoraciones/catalogo/`) en lugar de depender de `/api/catalogo/`.
- Se añadió el endpoint backend `GET /api/ciclos/{id}/valoraciones/catalogo/` y su prueba de API para asegurar la entrega de versión, dimensiones e indicadores/criterios del ciclo.
- Se ajustaron pruebas frontend de `Valoraciones` para la nueva ruta de catálogo y sincronización de carga.

## Revisión de artefactos y alineación

- **Backend valoración**: endpoint y enrutado en `sistema/backend/valoracion/`.
- **Frontend valoración**: consumo de endpoint corregido en `sistema/frontend/src/paginas/Valoraciones.jsx`.
- **Pruebas**: cobertura backend en `sistema/backend/valoracion/tests.py` y UI en `sistema/frontend/src/paginas/Valoraciones.test.jsx`.

## Pendientes

- PostgreSQL queda como validación pendiente documentada, tal y como establece la política del proyecto para producción.
