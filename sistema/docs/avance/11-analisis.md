# Avance 11 — Módulo de análisis

## Estado

Se corrigió la presentación de la pestaña **Completitud** en `Analisis` sin cambiar lógica de negocio:

- **Modelos incompletos** ahora se muestran en formato amigable:
  `Modelo {numero_modelo} - Curso {curso}: Faltan {campos_esperados - campos_presentes} campos`.
- **Criterios sin evidencia** y **criterios cuantitativos sin dato** ahora muestran
  `codigo_manual` (o fallback `codigo`) y `nombre` del criterio.
- **Dimensiones sin valoración** ahora muestran el `nombre` de la dimensión.
- Backend de análisis ahora expone `codigo_manual` en el payload de estado y
  `numero_modelo`/`nombre_modelo` en elementos de `modelos_incompletos`.

## Verificación ejecutada

Desde `sistema/backend`:

```powershell
& ..\..\.venv\Scripts\python.exe manage.py test analisis
```

Resultado: 14 pruebas aprobadas sobre SQLite.

Desde `sistema/frontend`:

```powershell
npm run test:run -- --pool=vmThreads --maxWorkers=1 src/paginas/Analisis.test.jsx
```

Resultado: 4 pruebas aprobadas.

Desde la raíz del repositorio:

```powershell
openspec validate modulo-analisis
```

Resultado: `Change 'modulo-analisis' is valid`.

## Pendientes

- Validación manual en navegador de estado, completitud y comparación (tarea 5.5).
- PostgreSQL se mantiene como pendiente documentado (D-14), sin declararlo como realizado.
