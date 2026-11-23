# Decisiones del Plan 11 - Módulo de Análisis

- Cálculo de "Sin valoración": Se evalúa a nivel de criterio. Si al menos un criterio de una dimensión tiene una valoración registrada en ValoracionCriterio, la dimensión NO se considera "sin valorar". A nivel de reporte, se mantiene la clave dimensiones_sin_valoracion para agrupar las que estén completamente vacías.
- Modelo incompleto: Un modelo se marca como incompleto si falta al menos una celda esperada (definida en ModeloCampo) para un curso evaluado, basándose en la comparación de campos esperados vs. presentes.
- Criterios sin dato (con modelo): Si un criterio cuantitativo depende de un modelo, se considera "sin dato" si no existe ningún valor guardado en ValorModelo para el curso evaluado.
- Roles del sistema: Se aplican estrictamente los roles existentes (Administrador Técnico y Director de Carrera). Los roles adicionales de la matriz original (Decano, Rector, etc.) se dejan como *pendiente funcional* para futuras ampliaciones.
- Comparación entre ciclos: Se empareja por posición relativa del curso (ej. Curso 1 del ciclo A vs. Curso 1 del ciclo B), ya que los años absolutos no coinciden entre ciclos.
- Auditoría: El servicio registrar(...) se invoca únicamente en las comparaciones autorizadas. Los accesos denegados (403) siguen siendo manejados por el middleware del Plan 06.
- Interfaz de usuario: Se corrigió el renderizado de los datos crudos (JSON) a texto legible para el usuario, mostrando nombres de modelos, años y cantidades de campos faltantes.
- Verificación: Pruebas ejecutadas en SQLite y Vitest. La verificación en PostgreSQL queda pendiente y documentada según D-14.