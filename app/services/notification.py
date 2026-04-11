"""Servicios para la gestión y persistencia de notificaciones.

Este módulo encapsula las operaciones de base de datos para las alertas
del sistema, permitiendo su creación, consulta y actualización de estado (leído).
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.notification import notification_repo
from app.schemas.notification import NotificationCreate, NotificationUpdate


async def create_notification(
    db: AsyncSession, notification_data: NotificationCreate
) -> Notification:
    """Crea una nueva notificación asíncronamente."""
    return await notification_repo.create_for_user(db, obj_in=notification_data)


async def get_user_notifications(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20
) -> list[Notification]:
    """Obtiene las notificaciones de un usuario con paginación."""
    return await notification_repo.get_by_user(
        db, user_id=user_id, skip=skip, limit=limit
    )


async def get_total_count(db: AsyncSession, user_id: int) -> int:
    """Obtiene el total de notificaciones de un usuario."""
    return await notification_repo.count_by_user(db, user_id=user_id)


async def get_unread_count(db: AsyncSession, user_id: int) -> int:
    """Obtiene la cantidad de notificaciones no leídas."""
    return await notification_repo.get_unread_count(db, user_id=user_id)


async def mark_as_read(db: AsyncSession, notification_id: int) -> Notification:
    """Marca una notificación como leída."""
    notification = await notification_repo.mark_as_read(
        db, notification_id=notification_id
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada",
        )
    return notification


async def mark_all_as_read(db: AsyncSession, user_id: int) -> int:
    """Marca todas las notificaciones de un usuario como leídas."""
    return await notification_repo.mark_all_as_read(db, user_id=user_id)


async def delete_notification(db: AsyncSession, notification_id: int) -> None:
    """Elimina una notificación."""
    notification = await notification_repo.get(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada",
        )
    await notification_repo.remove(db, id=notification.id)


async def get_notification_by_id(
    db: AsyncSession, notification_id: int
) -> Notification:
    """Obtiene un registro de notificación por su identificador único."""
    notification = await notification_repo.get(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada",
        )
    return notification
