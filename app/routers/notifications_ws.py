"""WebSocket endpoint para notificaciones en tiempo real.

Implementa un ConnectionManager que mantiene conexiones
activas por user_id y permite broadcast selectivo.
"""

import json
import logging
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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
        logger.info(f"WebSocket conectado para user_id={user_id}. "
                     f"Total conexiones: {len(self.active_connections[user_id])}")

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


@router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: int):
    """Endpoint WebSocket para recibir notificaciones en tiempo real.
    
    El cliente se conecta y recibe notificaciones push cuando
    se crean nuevas notificaciones para su user_id.
    También acepta mensajes del cliente como heartbeats/pings.
    """
    await manager.connect(websocket, user_id)
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
                    logger.debug(f"Notification acknowledged by user {user_id}: {msg.get('notification_id')}")
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket cliente desconectado: user_id={user_id}")
    except Exception as e:
        manager.disconnect(websocket, user_id)
        logger.error(f"Error en WebSocket para user_id={user_id}: {e}")
