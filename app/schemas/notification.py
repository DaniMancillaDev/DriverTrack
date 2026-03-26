"""Esquemas de validación para notificaciones.

Define los modelos Pydantic para creación, actualización
y respuestas de la API relacionadas a notificaciones.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    """Datos requeridos para crear una notificación.

    El user_id se recibe como parámetro de query o del token JWT.
    """

    user_id: int
    title: str
    message: str
    type: str = "info"  # info, warning, success, error


class NotificationUpdate(BaseModel):
    """Datos opcionales para actualizar una notificación."""

    title: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None
    is_read: Optional[bool] = None


class NotificationResponse(BaseModel):
    """Datos de la notificación devueltos por la API."""

    id: int
    user_id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedNotificationsResponse(BaseModel):
    """Respuesta paginada de notificaciones."""

    items: list[NotificationResponse]
    total: int
    has_more: bool
    unread_count: int
