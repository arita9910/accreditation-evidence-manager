## 5\. Registro de decisiones inicial

Formato de cada ficha en docs/decisiones: problema, alternativas, decisión, justificación y consecuencias. Estado: **Confirmada** (Arianne la decidió) o **Propuesta** (de Claude, vigente salvo objeción de Arianne al revisar este documento).

| N.º | Decisión | Alternativa descartada | Estado |
| :---- | :---- | :---- | :---- |
| D-01 | Modelo de usuario propio desde la primera migración | El de Django sin extender: cambiarlo después obliga a rehacer la base | Propuesta |
| D-02 | Dos entidades, Indicador y Criterio (sustituye a «una entidad con nivel y padre», que se pensó cuando la terminología estaba abierta) | Una entidad con nivel | Propuesta (revisada 1 nov) |
| D-03 | Catálogo y definición de los modelos como ficheros de datos versionados, cargados con una orden repetible | Datos escritos en el código | Propuesta |
| D-04 | Los 11 modelos como celdas genéricas con definición por modelo | Una tabla por modelo | Propuesta |
| D-05 | Datos cuantitativos solo en modelos resumen y valor por criterio | Registros nominales (cada profesor, cada publicación) | **Confirmada** (1 nov) |
| D-06 | Autorización con una función propia sobre roles con ámbito, invocada desde una clase de permisos de DRF | Librería de permisos por objeto | Propuesta |
| D-07 | Auditoría en tabla propia de solo inserción, llamada por un servicio | Librería de historial automático | Propuesta |
| D-08 | Búsqueda solo en metadatos, detrás de un servicio de búsqueda con dos implementaciones (PostgreSQL: búsqueda de texto completo; SQLite: coincidencia por texto) | Búsqueda en el contenido de los ficheros (exige OCR) | **Confirmada** (1 nov); servicio de dos implementaciones, propuesta |
| D-09 | Entrega de ficheros protegidos: la API comprueba permisos y Nginx entrega el fichero en producción; Django lo entrega en desarrollo | Servir siempre desde Django | Propuesta |
| D-10 | Aviso de 50 páginas contando con LibreOffice si está en el servidor; si no, estimación declarada | Solo estimación | Propuesta; verificar con informática |
| D-11 | Reemplazar un fichero crea versión nueva | Sobrescribir | Propuesta |
| D-12 | Arquitectura cliente-servidor desacoplada: Django REST Framework y React 18; en producción Nginx sirve la aplicación React y reenvía /api a Gunicorn, de modo que todo está en el mismo origen y no hace falta CORS | Monolito con plantillas (plan anterior) | **Confirmada** (26 oct); detalle de despliegue, propuesta |
| D-13 | Autenticación de la API con sesión de Django y protección CSRF | Tokens JWT guardados en el navegador (más superficie ante XSS y más piezas) | Propuesta |
| D-14 | Desarrollo con SQLite por ahora; PostgreSQL como gestor de producción, que se usa al instalar el sistema en el servidor del cliente. Consecuencias: sin SQL propio de un gestor fuera del servicio de búsqueda; en desarrollo, las restricciones y migraciones se prueban en SQLite; las pruebas sobre PostgreSQL se ejecutan en el servidor del cliente, o en una instalación local de PostgreSQL cuando haya una disponible | PostgreSQL desde el inicio | **Confirmada** (26 oct); consecuencia modificada el 2 nov: ya no se exige ejecutar las pruebas sobre PostgreSQL antes de cerrar cada incremento |
| D-15 | Frontend con Vite, JavaScript, React Router, Bootstrap local y Vitest con Testing Library; Node.js solo en desarrollo | TypeScript (más curva de aprendizaje); Node en el servidor | Propuesta |
| D-16 | Paquetes sin conexión: pip download y caché de npm con package-lock.json, guardados en almacen/ | Instalar desde internet en cada equipo | Propuesta |
| D-17 | Repositorio único con backend/ y frontend/; rama principal siempre funcional y una rama por incremento | Dos repositorios | Propuesta |
| D-18 | Esquema de la API generado automáticamente (OpenAPI) para documentarla y probarla | Documentarla a mano | Propuesta; opcional |

Efecto de D-12 en el plan: el módulo estructura, por ejemplo, ya no entrega plantillas, sino endpoints de solo lectura (`/api/catalogo/…`) y pantallas React que los consumen; las fichas de cada módulo lo recogen.  
