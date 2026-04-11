# Referencia de la API de DriverTrack

Bienvenido a la documentación técnica de la API de DriveTrack. Esta API permite la gestión integral de vehículos, historial de mantenimientos, notificaciones en tiempo real y datos meteorológicos.

## Información General

- **Versión**: 0.2.0
- **Base URL**: `http://localhost:8000` (Desarrollo)
- **Formato**: JSON (UTF-8)

---

## Seguridad y Autenticación

La API utiliza **JSON Web Tokens (JWT)** para la autenticación y el control de acceso.

### Flujo de Tokens

1.  **Login**: El cliente envía credenciales a `/auth/login` y recibe un `access_token` y un `refresh_token`.
2.  **Autorización**: Se debe incluir el access token en la cabecera HTTP de todas las peticiones protegidas:
    `Authorization: Bearer <JWT_TOKEN>`
3.  **Renovación**: Cuando el access token expira, se utiliza el refresh token en `/auth/refresh` para obtener uno nuevo sin pedir credenciales al usuario.

### Consideraciones
- **Identidad**: El campo `sub` de los tokens siempre contiene el ID del usuario como `string`.
- **Expiración**: Los tiempos de expiración se configuran en el servidor (por defecto: 60 min para acceso, 30 días para refresh).
- **Protección BOLA/IDOR**: La API verifica en cada petición que el recurso solicitado pertenece al usuario autenticado.

---

## Módulo: Autenticación (`/auth`)

Endpoints públicos para la gestión de cuentas y sesiones.

### 1. Registrar Usuario
Crea una nueva cuenta y autentica automáticamente.

- **Método**: `POST`
- **URL**: `/auth/register`
- **Cuerpo (JSON)**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "Nombre Apellido"
  }
  ```
- **Respuesta (201 Created)**:
  ```json
  {
    "access_token": "...",
    "refresh_token": "...",
    "user": { "id": 1, "email": "...", "full_name": "..." }
  }
  ```

### 2. Iniciar Sesión
- **Método**: `POST /auth/login`
- **Cuerpo**: `{ "email": "...", "password": "..." }`
- **Respuesta (200 OK)**: Devuelve tokens y datos del usuario.

### 3. Recuperación de Contraseña (OTP)
Flujo de 3 pasos:
1.  **Solicitar OTP** (`POST /auth/forgot-password`): Envía un código de 6 dígitos al correo.
2.  **Verificar OTP** (`POST /auth/verify-otp`): Valida que el código es correcto.
3.  **Restablecer** (`POST /auth/reset-password`): Establece la nueva contraseña usando el código verificado.

---

## Módulo: Usuarios (`/users`)

### Gestión de Perfil
- `GET /users/me`: Obtiene el perfil actual.
- `PUT /users/me`: Actualiza el nombre completo.
- `PATCH /users/me/preferences`: Actualiza booleanos de notificaciones (`push_notifications`, `service_reminders`, `critical_alerts`).
- `POST /users/me/change-password`: Cambia la contraseña (requiere la actual).

### Fotos de Perfil (Flujo MinIO)
1.  **Obtener URL**: `POST /users/me/photo/presigned-url` devuelve una URL pre-firmada de S3.
2.  **Subida**: El cliente sube el archivo binario directamente a esa URL (PUT).
3.  **Confirmación**: `PUT /users/me/photo/confirm` con el `object_key` para actualizar la BD.

---

## Módulo: Vehículos (`/vehicles`)

Gestión del garaje virtual del usuario.

### 1. Catálogo de Tipos
- **Método**: `GET /vehicles/types` (Público)
- **Descripción**: Obtiene la lista de tipos de vehículos soportados (Coche, Moto, etc.).

### 2. Mis Vehículos (CRUD)
- `GET /vehicles/`: Lista todos los vehículos del usuario autenticado.
- `POST /vehicles/`: Registra un nuevo vehículo.
- `GET /vehicles/{id}`: Detalle de un vehículo específico.
- `PUT /vehicles/{id}`: Actualiza datos del vehículo (marca, modelo, año, placa, kilometraje).
- `DELETE /vehicles/{id}`: Elimina el vehículo (solo el propietario).

### 3. Fotos de Vehículos
Sigue el mismo flujo de URLs pre-firmadas que el perfil de usuario:
- `POST /vehicles/{id}/photo/presigned-url`
- `PUT /vehicles/{id}/photo/confirm`

---

## Módulo: Mantenimientos (`/maintenance`)

Registro histórico de servicios y reparaciones.

### 1. Registrar Mantenimiento
- **Método**: `POST /vehicles/{vehicle_id}/maintenance`
- **Cuerpo**:
  ```json
  {
    "description": "Cambio de aceite y filtro",
    "mileage": 55000,
    "cost": 120.50,
    "date": "2024-03-15",
    "service_type": "Mecánica"
  }
  ```

### 2. Consultar Historial
- `GET /vehicles/{vehicle_id}/maintenance`: Historial filtrado por vehículo.
- `GET /maintenance`: Historial global de todos los vehículos del usuario.
- `GET /maintenance/{id}`: Detalle de un registro específico.

---

## Módulo: Notificaciones (`/notifications`)

Gestión de alertas y avisos del sistema (mantenimientos próximos, alertas críticas).

### 1. REST API
- `GET /notifications`: Lista paginada de notificaciones del usuario.
- `GET /notifications/unread-count`: Contador de avisos pendientes.
- `PATCH /notifications/{id}/read`: Marca una notificación como leída.
- `PATCH /notifications/read-all`: Marca todas como leídas.
- `DELETE /notifications/{id}`: Elimina una notificación.

### 2. Real-Time (WebSockets)
La API soporta notificaciones instantáneas mediante WebSockets.

- **URL**: `ws://host/ws/notifications`
- **Protocolo de Autenticación**:
  El cliente debe enviar un mensaje de autenticación como primer frame:
  ```json
  { "type": "auth", "token": "<JWT_ACCESS_TOKEN>" }
  ```
- **Eventos del Servidor**: El servidor enviará objetos JSON de tipo `NotificationResponse` cada vez que ocurra un evento relevante.

---

## Módulo: Clima (`/weather`)

Proxy seguro para obtener datos meteorológicos sin exponer la API Key de OpenWeatherMap en el cliente.

### 1. Por Coordenadas
- **Método**: `GET /weather/current?lat={lat}&lon={lon}`
- **Descripción**: Devuelve el JSON crudo de OWM para la ubicación dada.

### 2. Por Ciudad
- **Método**: `GET /weather/city/{city_name}`
- **Descripción**: Búsqueda por nombre de ciudad.

---

## Códigos de Respuesta y Errores

La API utiliza códigos de estado HTTP estándar:

- `200 OK`: Operación exitosa.
- `201 Created`: Recurso creado con éxito.
- `204 No Content`: Eliminación exitosa (sin cuerpo de respuesta).
- `400 Bad Request`: Datos de entrada inválidos o error de lógica de negocio.
- `401 Unauthorized`: Token faltante, inválido o expirado.
- `403 Forbidden`: El usuario no tiene permisos para acceder al recurso (IDOR/BOLA protection).
- `404 Not Found`: El recurso solicitado no existe.
- `429 Too Many Requests`: Se ha excedido el límite de peticiones (Rate Limiting).
- `500 Internal Server Error`: Error inesperado en el servidor.

---

## Limitación de Tasa (Rate Limiting)

Para proteger la infraestructura, se aplican límites de peticiones:
- **Autenticación**: Límites estrictos (5-10 peticiones/min) para prevenir ataques de fuerza bruta.
- **API General**: Límites estándar según la carga del endpoint.

---
