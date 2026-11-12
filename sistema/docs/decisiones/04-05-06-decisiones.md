# Decisiones de los Planes 04, 05 y 06

## Plan 04 (Ciclos)
- Restricción de un solo ciclo abierto por carrera y cadena ciclo_anterior.
- El ciclo abarca 5 cursos consecutivos (validación estricta); el curso final se calcula automáticamente.
- Tipos de ciclo válidos: autoevaluación, acreditación, reacreditación.
- exigir_ciclo_abierto es la función común para rechazar operaciones sobre ciclos cerrados.

## Plan 05 (Cuentas)
- Roles definidos: Administrador Técnico (ve todo) y Director de Carrera (ligado a una carrera, solo ve su carrera).
- cuentas.Usuario NO hereda de ModeloBase (decisión confirmada).
- puede(...) real implementado para la validación de permisos.

## Plan 06 (Auditoría)
- La auditoría es inmutable: solo permite inserción, no modificación ni borrado.
- registrar() es real, transaccional y tiene la misma firma que el stub original.
- Accesos denegados (403) se registran mediante middleware.
- CATALOGO_API_DESARROLLO = False por defecto (para evitar regresiones en pruebas).