# Tasks

## 1. Crear la base abstracta y la atribución

- [x] 1.1 Implementar `ModeloBase` en `sistema/backend/nucleo/modelos.py` con `creado_en`, `modificado_en`, `creado_por` y `modificado_por`; usar timestamps automáticos y referencias anulables con `on_delete=PROTECT` a `settings.AUTH_USER_MODEL`.
- [x] 1.2 Añadir el puente de importación requerido por Django en `sistema/backend/nucleo/models.py` para que las clases definidas en `modelos.py` se registren al cargar la app.
- [x] 1.3 Crear un helper o mixin reutilizable para que los serializadores asignen `creado_por` en altas y `modificado_por` en altas y cambios desde `request.user`, manteniendo referencias nulas cuando no hay usuario autenticado.
- [x] 1.4 Probar con un modelo concreto temporal los cuatro campos, la actualización automática de fechas, la nulabilidad y la protección de las referencias; probar también la asignación y preservación de los campos de autoría en altas y cambios.
- [x] 1.5 No modificar `cuentas.Usuario` ni añadir modelos de estructura o dominio; mantener abierta la decisión de herencia descrita en `design.md`.

## 2. Implementar el almacenamiento privado de ficheros

- [x] 2.1 Implementar en `sistema/backend/nucleo/almacenamiento.py` `guardar_fichero(archivo, subcarpeta)` para crear un nombre UUID con extensión saneada, guardar bajo `EVIDENCIAS_ROOT` y devolver `nombre_interno`, `ruta_relativa`, `tamano` y `sha256`, calculando la huella por bloques.
- [x] 2.2 Implementar `abrir_fichero`, `calcular_sha256`, `verificar_huella` y `borrar_fichero`; limitar el borrado a pruebas y limpieza explícita de huérfanos.
- [x] 2.3 Separar `MEDIA_ROOT` de `EVIDENCIAS_ROOT` en los ajustes sin cambiar el contrato de configuración de `EVIDENCIAS_ROOT`; asegurar que las rutas de archivos públicos no exponen el almacenamiento privado.
- [x] 2.4 Probar nombres únicos para cargas repetidas, hash contra `hashlib.sha256`, tamaño, contención de la ruta resuelta, separación frente a `STATIC_ROOT` y `MEDIA_ROOT`, rechazo de rutas absolutas y traversal, y detección de contenido alterado.

## 3. Añadir las utilidades backend de API

- [x] 3.1 Configurar paginación `PageNumberPagination` con tamaño de página configurable y añadir pruebas de la forma y navegación de la respuesta.
- [x] 3.2 Implementar el manejador común de excepciones DRF con `codigo`, `mensaje` y `detalle` en español; cubrirlo con pruebas para errores gestionados.
- [x] 3.3 Añadir `GET /api/salud/` sin autenticación que responda `{"estado": "ok"}` y probar la respuesta anónima.
- [x] 3.4 Instalar y fijar `drf-spectacular` en `sistema/backend/requirements.txt`, actualizar el almacén/procedimiento offline si corresponde, configurar el esquema OpenAPI y habilitar `/api/esquema/` solo en desarrollo; probar que no se registra en producción.

## 4. Crear el cliente y la plantilla frontend

- [x] 4.1 Crear `sistema/frontend/src/api/cliente.js` con `fetch`, `credentials: 'same-origin'`, lectura de `csrftoken`, cabecera `X-CSRFToken` en solicitudes de escritura y manejo central de errores del formato común.
- [x] 4.2 Configurar el proxy de Vite para reenviar `/api` a `http://localhost:8000`.
- [x] 4.3 Crear `Diseno`, `Mensaje` y `Cargando` bajo `sistema/frontend/src/componentes/`, y reemplazar la plantilla inicial por un enrutador React Router con rutas protegidas preparadas pero sin activar la comprobación de sesión hasta que exista `/api/cuentas/yo/`.
- [x] 4.4 Usar `react-router-dom` y Bootstrap local ya declarados en `package.json`; no volver a agregar React Router ni Bootstrap como dependencias.
- [x] 4.5 Añadir pruebas Vitest para el envío de CSRF en POST y la presentación de errores mediante `Mensaje`; ejecutar build y lint del frontend.

## 5. Documentar la decisión pendiente y el avance

- [x] 5.1 Crear `sistema/docs/decisiones/nucleo.md` con la pregunta abierta: ¿debe `cuentas.Usuario` heredar de `ModeloBase`? Registrar que no se decide ni implementa esa herencia en este cambio.
- [x] 5.2 Crear `sistema/docs/avance/02-nucleo.md` con las comprobaciones backend y frontend realmente ejecutadas, incidencias y decisiones pendientes; no afirmar resultados no verificados.

## 6. Verificar el núcleo integrado

- [x] 6.1 Ejecutar migraciones y pruebas backend en SQLite; comprobar la salud, el formato de errores, la paginación, el esquema en desarrollo y su ausencia en producción.
- [x] 6.2 Ejecutar Vitest y el build frontend; confirmar que el proxy `/api` y el comportamiento CSRF cumplen las pruebas.
- [x] 6.3 Revisar que no se crearon modelos de estructura, que se reutiliza `cuentas.Usuario` y `EVIDENCIAS_ROOT`, y que las raíces privadas y públicas permanecen separadas; registrar los resultados en el avance.
