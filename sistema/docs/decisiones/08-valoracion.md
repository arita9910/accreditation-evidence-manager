# Decisiones del Plan 08 (Valoración Cualitativa)

- Vinculación al Catálogo: Se decidió usar la versión viva del catálogo (vinculando la valoración al ID del Criterio). No se guarda una "instantánea" (snapshot) del texto del criterio en esta fase, para simplificar el modelo.
- Formato de Porcentaje: Se implementó un asistente que formatea los datos automáticamente al estándar del Manual SEA-CU: XX,X % (Numerador/Denominador). Ejemplo: 86,2 % (19/23).
- Validaciones del Asistente: 
  - El porcentaje se calcula automáticamente al ingresar el Numerador y el Denominador.
  - Se impide guardar si el Numerador es mayor que el Denominador (para evitar porcentajes mayores al 100%).
  - Se impide guardar si el Denominador es 0.
- Integración: Toda valoración exige que el ciclo esté abierto (exigir_ciclo_abierto), registra el evento en la auditoría (registrar) y respeta los permisos por rol (puede).