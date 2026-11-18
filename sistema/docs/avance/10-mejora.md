# Avance: módulo de mejora

## Estado

- Bloques 1 a 5 implementados para plan por ciclo, acciones, seguimiento, evidencias y comparación con el ciclo anterior.
- La creación del plan toma el ciclo desde la URL y devuelve errores de validación en JSON.
- La tabla de acciones muestra el nombre del responsable (`responsable_nombre`) y conserva el id para operaciones.
- La API y la UI permiten editar y eliminar acciones con validación de ciclo abierto y registro en auditoría.
- La API y la UI permiten editar el estado del plan con validación de ciclo abierto y registro en auditoría.
- El registro de acciones permanece deshabilitado hasta completar debilidad, descripción, responsable y fecha límite.
- La validación se ejecuta únicamente con SQLite. La verificación en PostgreSQL queda pendiente (D-14).

## Comandos de verificación

Desde `sistema/backend`:

```powershell
& "D:\tesis-app\accreditation-evidence-manager\.venv-nucleo-validation\Scripts\python.exe" manage.py test mejora
# Resultado: 12 pruebas aprobadas sobre SQLite.
```

Desde `sistema\frontend`:

```powershell
npm run test:run -- --pool=vmThreads --maxWorkers=1 src/paginas/Mejora.test.jsx
# Resultado: 6 pruebas aprobadas.
```
