"""WebSocket endpoint para notificaciones en tiempo real.

Este módulo implementa la comunicación bidireccional mediante WebSockets,
permitiendo que el servidor envíe notificaciones instantáneas a los clientes
conectados. Gestiona la autenticación inicial, el mantenimiento de las
conexiones activas y la limpieza de recursos al desconectar.
"""

import json
import logging
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import AsyncSessionLocal
from app.services import users as users_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket Notificaciones"])


class ConnectionManager:
    """Gestor de conexiones WebSocket por usuario.

    Mantiene un diccionario de user_id → lista de WebSockets activos.
    Soporta múltiples conexiones por usuario (ej: múltiples dispositivos).
    """

    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Acepta una nueva conexión WebSocket y la registra."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(
            f"WebSocket conectado para user_id={user_id}. "
            f"Total conexiones: {len(self.active_connections[user_id])}"
        )

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Elimina una conexión WebSocket del registro."""
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                ws for ws in self.active_connections[user_id] if ws != websocket
            ]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket desconectado para user_id={user_id}.")

    async def send_to_user(self, user_id: int, message: str):
        """Envía un mensaje a todas las conexiones activas de un usuario."""
        if user_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(message)
                except Exception:
                    disconnected.append(websocket)

            # Limpiar conexiones muertas
            for ws in disconnected:
                self.disconnect(ws, user_id)

    async def broadcast_all(self, message: str):
        """Envía un mensaje a todos los usuarios conectados."""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)


# Instancia global del manager (importada por el router REST)
manager = ConnectionManager()


async def _authenticate_ws_token(token: str) -> int | None:
    """Valida el JWT de un WebSocket y retorna el user_id o None si inválido.

    Args:
        token: JWT de acceso pasado como query parameter.

    Returns:
        user_id (int) si el token es válido y el usuario activo, None si no.
    """
    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        return None

    # Verificar que el usuario existe y está activo
    async with AsyncSessionLocal() as db:
        user = await users_service.get_user(db, user_id=user_id)
        if user is None or not user.is_active:
            return None

    return user_id


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
):
    """Endpoint WebSocket para recibir notificaciones en tiempo real.

    Autenticación se hace en el primer mensaje ENVIADO POR EL CLIENTE:
        {"type": "auth", "token": "<JWT>"}

    Protocolo de mensajes del servidor:
        - {"type": "connection_established", "user_id": int}
        - {"type": "pong"} (respuesta a ping)
        - <NotificationResponse JSON> (nueva notificación)

    Protocolo de mensajes del cliente:
        - {"type": "auth", "token": "<JWT>"} (obligatorio como primer mensaje)
        - {"type": "ping"} → recibe {"type": "pong"}
        - {"type": "acknowledge", "notification_id": int}
    """
    await websocket.accept()

    try:
        # Esperar auth frame como primer mensaje (timeout de 5 segundos)
        import asyncio
        data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
        auth_msg = json.loads(data)
        
        if auth_msg.get("type") != "auth" or not auth_msg.get("token"):
            await websocket.close(code=4001, reason="Primer mensaje debe ser tipo 'auth'")
            return
            
        token = auth_msg.get("token")
    except (asyncio.TimeoutError, json.JSONDecodeError):
        await websocket.close(code=4001, reason="Timeout esperando auth o formato inválido")
        return

    # ── Autenticación token obtenida ──
    user_id = await _authenticate_ws_token(token)
    if user_id is None:
        # Cerrar con código 4001 (application-level Unauthorized)
        await websocket.close(code=4001, reason="Token inválido o expirado")
        logger.warning("WebSocket rechazado: token inválido")
        return

    # Registrar conexión
    manager.active_connections.setdefault(user_id, []).append(websocket)
    logger.info(f"WebSocket conectado para user_id={user_id}. Total: {len(manager.active_connections[user_id])}")
    
    try:
        # Enviar confirmación de conexión
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "user_id": user_id,
            "message": "Conectado al servicio de notificaciones en tiempo real",
        }))

        # Mantener la conexión abierta escuchando mensajes del cliente
        while True:
            data = await websocket.receive_text()

            # Procesar mensajes del cliente (ping/pong, acknowledge, etc.)
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif msg.get("type") == "acknowledge":
                    logger.debug(
                        f"Notification acknowledged by user {user_id}: "
                        f"{msg.get('notification_id')}"
                    )
            except json.JSONDecodeError:
                pass  # Ignorar mensajes malformados silenciosamente

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket cliente desconectado: user_id={user_id}")
    except Exception as e:
        manager.disconnect(websocket, user_id)
        logger.error(f"Error en WebSocket para user_id={user_id}: {e}")
