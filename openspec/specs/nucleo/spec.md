# nucleo Specification

## Purpose

Define los servicios compartidos del módulo `nucleo` para metadatos de autoría, almacenamiento privado, API y estructura inicial del frontend.

## Requirements

### Requirement: Modelo abstracto de autoría
El backend SHALL ofrecer en `nucleo` un `ModeloBase` abstracto con `creado_en` y `modificado_en` automáticos, además de `creado_por` y `modificado_por` como referencias anulables y protegidas a `settings.AUTH_USER_MODEL`. SHALL reutilizar `cuentas.Usuario` como identidad configurada y SHALL NOT duplicar el modelo de usuario.

#### Scenario: Comprobar los campos heredados
- **WHEN** una prueba guarda y actualiza un modelo concreto de prueba que hereda de `ModeloBase`
- **THEN** existen los cuatro campos, las fechas se mantienen automáticamente y los campos de usuario aceptan valores nulos

### Requirement: Atribución del usuario de petición
Las escrituras efectuadas mediante serializadores de la API SHALL asignar el usuario autenticado de la petición a `creado_por` al crear y a `modificado_por` al crear o actualizar, sin exigir que los serializadores individuales reimplementen la misma lógica.

#### Scenario: Crear y actualizar con una petición autenticada
- **WHEN** un serializador guarda una instancia usando una petición autenticada
- **THEN** los campos de autoría correspondientes contienen el usuario de `cuentas.Usuario` asociado a esa petición

#### Scenario: Escritura sin usuario autenticado
- **WHEN** la escritura no tiene un usuario autenticado
- **THEN** las referencias de autoría pueden permanecer nulas y la operación no inventa una identidad

### Requirement: Almacenamiento privado de evidencias
El servicio de ficheros SHALL guardar bajo `EVIDENCIAS_ROOT` configurable, sin exponer los ficheros por rutas públicas ni utilizar `MEDIA_ROOT` como raíz de evidencias. SHALL proporcionar guardado con nombre interno UUID y extensión saneada, ruta relativa, tamaño y SHA-256 calculado por bloques; apertura, cálculo y verificación de huella; y borrado para pruebas o limpieza explícita.

#### Scenario: Guardar dos veces el mismo contenido
- **WHEN** se guarda dos veces el mismo fichero
- **THEN** cada operación produce un nombre interno único y la huella coincide con SHA-256 del contenido

#### Scenario: Rechazar una ruta insegura
- **WHEN** se solicita acceso a una ruta absoluta o que intenta salir de `EVIDENCIAS_ROOT`
- **THEN** el servicio rechaza la operación sin leer, escribir ni borrar fuera de la raíz

#### Scenario: Verificar integridad del fichero
- **WHEN** se verifica una huella correcta y luego cambia el contenido almacenado
- **THEN** la primera verificación tiene éxito y la posterior falla

### Requirement: Convenciones comunes de API
La API SHALL usar paginación `PageNumberPagination` con tamaño configurable y SHALL devolver los errores DRF con la forma `{"codigo": "...", "mensaje": "...", "detalle": ...}` en español.

#### Scenario: Paginar una colección
- **WHEN** una consulta de colección supera el tamaño de página configurado
- **THEN** la respuesta respeta la paginación por número de página e incluye la navegación estándar de DRF

#### Scenario: Responder a un error de API
- **WHEN** DRF produce una excepción gestionada
- **THEN** la respuesta mantiene las claves `codigo`, `mensaje` y `detalle` con mensajes en español

### Requirement: Comprobar la salud del servicio
El backend SHALL exponer `GET /api/salud/` sin autenticación, con la respuesta JSON `{"estado": "ok"}` cuando esté disponible.

#### Scenario: Consultar salud sin sesión
- **WHEN** un cliente anónimo solicita `/api/salud/`
- **THEN** recibe estado HTTP exitoso y `{"estado": "ok"}`

### Requirement: Esquema OpenAPI opcional en desarrollo
El backend SHALL poder ofrecer el esquema OpenAPI generado en `/api/esquema/` únicamente en desarrollo, usando `drf-spectacular`; la dependencia deberá quedar declarada para instalaciones reproducibles.

#### Scenario: Consultar el esquema en desarrollo
- **WHEN** se solicita `/api/esquema/` con la configuración de desarrollo
- **THEN** el backend devuelve el esquema OpenAPI generado

#### Scenario: No exponer el esquema en producción
- **WHEN** se usa la configuración de producción
- **THEN** la ruta de esquema no queda habilitada

### Requirement: Cliente API con protección CSRF
El frontend SHALL proporcionar un cliente basado en `fetch` que use `credentials: 'same-origin'`, lea la cookie `csrftoken`, envíe `X-CSRFToken` en las solicitudes que escriben y centralice el tratamiento de errores con el formato común del backend. Vite SHALL reenviar `/api` al servidor backend local durante el desarrollo.

#### Scenario: Enviar una solicitud que modifica datos
- **WHEN** el cliente envía una solicitud de escritura y existe la cookie `csrftoken`
- **THEN** envía esa cookie en la cabecera `X-CSRFToken` y conserva las credenciales del mismo origen

#### Scenario: Mostrar un error de API
- **WHEN** el backend devuelve un error con el formato común
- **THEN** el cliente hace disponible el mensaje para su presentación por el componente `Mensaje`

### Requirement: Plantilla compartida del frontend
El frontend SHALL proporcionar `Diseno`, `Mensaje` y `Cargando`, y una configuración de React Router con rutas protegidas preparadas. SHALL reutilizar React Router y Bootstrap local ya instalados, sin duplicar dependencias. La protección de sesión SHALL permanecer inactiva hasta que esté disponible `/api/cuentas/yo/`.

#### Scenario: Renderizar la estructura común
- **WHEN** se muestra una página de la aplicación
- **THEN** puede usar `Diseno` como contenedor y los componentes `Mensaje` y `Cargando` para avisos y estados de espera

#### Scenario: Preparar rutas antes de disponer de identidad de sesión
- **WHEN** todavía no existe `/api/cuentas/yo/`
- **THEN** el enrutador funciona sin activar una comprobación de autenticación inexistente
