# Planes de implementación para agente — Sistema SEA-CU 2025 (tesis de Arianne)

Cada fichero de esta carpeta es **autocontenido**: se le puede dar a un agente de programación por separado. Se derivan del documento «Condiciones para iniciar el incremento 0» (1 nov 2026) y del «Plan de implementación por módulos».

## Qué es el sistema (una línea)
Aplicación web para gestionar el expediente documental de la autoevaluación de una carrera en un ciclo SEA-CU 2025: catálogo normativo (6 dimensiones, 24 indicadores, 65 criterios), evidencias con huella SHA-256, datos cuantitativos (11 modelos resumen) vinculados a evidencias, valoración cualitativa, plan de mejora, comparación entre ciclos e informe de autoevaluación en .docx. Backend Django + DRF; frontend React 18; SQLite en desarrollo, PostgreSQL en producción.

## Orden de entrega

| Plan | Incremento | Depende de |
| :- | :- | :- |
| 00-base-repositorio-y-entorno | 0 | — |
| 01-modelo-de-datos | 0 a 4 (por oleadas) | 00 |
| 02-modulo-nucleo | 0 | 00 |
| 03-modulo-estructura | 0 | 01 (oleada A), 02 |
| 04-modulo-ciclos | 1 | 03 |
| 06-modulo-auditoria | 1 | 02 |
| 05-modulo-cuentas | 1 (el modelo Usuario, en el 0) | 02, 04, 06 |
| 07-modulo-evidencias | 2 | 04, 05, 06 |
| 08-modulo-valoracion | 2 | 07 |
| 09-modulo-cuantitativos | 3 | 07 |
| 10-modulo-mejora | 3 | 08, 07 |
| 11-modulo-analisis | 4 | 07 a 10 |
| 12-modulo-informes | 4 | 11 |

Dentro del incremento 1, el orden de trabajo es **ciclos → auditoría → cuentas** (cuentas necesita los ámbitos de ciclos y la auditoría para registrar).

## Reglas para el agente (valen en todos los planes)
1. Implementar solo lo que dice el plan. Si algo es ambiguo o contradice la realidad del repositorio, **no inventar**: anotarlo en `sistema/docs/decisiones/` como pregunta abierta y seguir con lo que no depende de ello.
2. No cambiar alcance, nombres de entidades ni terminología (indicador = 2.º nivel; criterio = 3.er nivel).
3. Cada plan termina con pruebas pasando. No se declaran resultados que no se hayan ejecutado.
4. Al terminar cada plan, dejar un párrafo de avance para el capítulo 2 de la tesis en `sistema/docs/avance/<plan>.md` (qué se hizo, decisiones, qué falta).

## Puntos abiertos que afectan a varios planes
- D-14: interpretación pendiente de confirmar (SQLite en desarrollo, PostgreSQL en producción). Se implementa con configuración por variables de entorno.
- Entorno del portátil de Arianne (Python, Node, npm, Git) por comprobar.
- Entrevistas: los planes 07 a 10 usan requisitos propuestos que se validan con ellas antes del incremento 2.
