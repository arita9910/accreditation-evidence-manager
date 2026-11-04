# Fichas de decisiones D-01 a D-18

Fuente: sección 5 de [`condiciones-incremento-0(seccion 5).md`](../condiciones-incremento-0(seccion%205).md).
Los campos se reproducen solo cuando están respaldados por esa fuente. La frase
«No especificado en la fuente» indica que la sección 5 no aporta ese dato.

## D-01 — Modelo de usuario propio desde la primera migración

- **Problema:** No especificado en la fuente.
- **Alternativas:** El de Django sin extender; cambiarlo después obliga a rehacer la base.
- **Decisión:** Modelo de usuario propio desde la primera migración.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta.

## D-02 — Entidades Indicador y Criterio

- **Problema:** No especificado en la fuente.
- **Alternativas:** Una entidad con nivel y padre.
- **Decisión:** Dos entidades, Indicador y Criterio; sustituye a la alternativa de una entidad con nivel y padre, considerada cuando la terminología estaba abierta.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta (revisada 1 nov).

## D-03 — Catálogo y modelos como datos versionados

- **Problema:** No especificado en la fuente.
- **Alternativas:** Datos escritos en el código.
- **Decisión:** Catálogo y definición de los modelos como ficheros de datos versionados, cargados con una orden repetible.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta.

## D-04 — Celdas genéricas para los modelos

- **Problema:** No especificado en la fuente.
- **Alternativas:** Una tabla por modelo.
- **Decisión:** Los 11 modelos como celdas genéricas con definición por modelo.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta.

## D-05 — Datos cuantitativos en modelos resumen

- **Problema:** No especificado en la fuente.
- **Alternativas:** Registros nominales (cada profesor, cada publicación).
- **Decisión:** Datos cuantitativos solo en modelos resumen y valor por criterio.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Confirmada (1 nov).

## D-06 — Autorización propia sobre roles con ámbito

- **Problema:** No especificado en la fuente.
- **Alternativas:** Librería de permisos por objeto.
- **Decisión:** Autorización con una función propia sobre roles con ámbito, invocada desde una clase de permisos de DRF.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta.

## D-07 — Auditoría en tabla propia

- **Problema:** No especificado en la fuente.
- **Alternativas:** Librería de historial automático.
- **Decisión:** Auditoría en tabla propia de solo inserción, llamada por un servicio.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta.

## D-08 — Búsqueda en metadatos

- **Problema:** No especificado en la fuente.
- **Alternativas:** Búsqueda en el contenido de los ficheros (exige OCR).
- **Decisión:** Búsqueda solo en metadatos, detrás de un servicio con dos implementaciones: PostgreSQL con búsqueda de texto completo y SQLite con coincidencia por texto.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Confirmada (1 nov) para la búsqueda solo en metadatos; el servicio con dos implementaciones está propuesto.

## D-09 — Entrega protegida de ficheros

- **Problema:** No especificado en la fuente.
- **Alternativas:** Servir siempre desde Django.
- **Decisión:** La API comprueba permisos y Nginx entrega el fichero en producción; Django lo entrega en desarrollo.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta.

## D-10 — Aviso por volumen de páginas

- **Problema:** No especificado en la fuente.
- **Alternativas:** Solo estimación.
- **Decisión:** Aviso de 50 páginas contando con LibreOffice si está en el servidor; si no, estimación declarada.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta; verificar con informática.

## D-11 — Versionado al reemplazar ficheros

- **Problema:** No especificado en la fuente.
- **Alternativas:** Sobrescribir.
- **Decisión:** Reemplazar un fichero crea versión nueva.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta.

## D-12 — Arquitectura cliente-servidor desacoplada

- **Problema:** No especificado en la fuente.
- **Alternativas:** Monolito con plantillas (plan anterior).
- **Decisión:** Django REST Framework y React 18; en producción Nginx sirve la aplicación React y reenvía `/api` a Gunicorn.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** En producción todo queda en el mismo origen y no hace falta CORS. El módulo estructura entrega endpoints de solo lectura (por ejemplo, `/api/catalogo/…`) y pantallas React que los consumen.
- **Estado:** Arquitectura confirmada (26 oct); detalle de despliegue propuesto.

## D-13 — Autenticación de API con sesión

- **Problema:** No especificado en la fuente.
- **Alternativas:** Tokens JWT guardados en el navegador (más superficie ante XSS y más piezas).
- **Decisión:** Autenticación de la API con sesión de Django y protección CSRF.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta.

## D-14 — SQLite en desarrollo y PostgreSQL en producción

- **Problema:** No especificado en la fuente.
- **Alternativas:** PostgreSQL desde el inicio.
- **Decisión:** Desarrollo con SQLite por ahora; PostgreSQL como gestor de producción, que se usa al instalar el sistema en el servidor del cliente.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No usar SQL propio de un gestor fuera del servicio de búsqueda; en desarrollo, probar restricciones y migraciones en SQLite; ejecutar las pruebas sobre PostgreSQL en el servidor del cliente, o en una instalación local de PostgreSQL cuando haya una disponible. Ya no se exige ejecutarlas antes de cerrar cada incremento.
- **Estado:** Confirmada (26 oct); consecuencia modificada el 2 nov.

## D-15 — Herramientas del frontend

- **Problema:** No especificado en la fuente.
- **Alternativas:** TypeScript (más curva de aprendizaje); Node en el servidor.
- **Decisión:** Vite, JavaScript, React Router, Bootstrap local y Vitest con Testing Library; Node.js solo en desarrollo.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta.

## D-16 — Paquetes sin conexión

- **Problema:** No especificado en la fuente.
- **Alternativas:** Instalar desde internet en cada equipo.
- **Decisión:** `pip download` y caché de npm con `package-lock.json`, guardados en `almacen/`.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta.

## D-17 — Repositorio y ramas por incremento

- **Problema:** No especificado en la fuente.
- **Alternativas:** Dos repositorios.
- **Decisión:** Repositorio único con `backend/` y `frontend/`; rama principal siempre funcional y una rama por incremento.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta.

## D-18 — Esquema OpenAPI

- **Problema:** No especificado en la fuente.
- **Alternativas:** Documentarla a mano.
- **Decisión:** Esquema de la API generado automáticamente (OpenAPI) para documentarla y probarla.
- **Justificación:** No especificado en la fuente.
- **Consecuencias:** No especificado en la fuente.
- **Estado:** Propuesta; opcional.
