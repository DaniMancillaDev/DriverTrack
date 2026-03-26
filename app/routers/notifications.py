"""Router REST de notificaciones."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    PaginatedNotificationsResponse,
)
from app.services import notification as notification_service
from app.routers.notifications_ws import manager

router = APIRouter(prefix="/notifications", tags=["Notificaciones"])


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una notificación",
)
async def create_notification(
    notification_data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crea una nueva notificación y la envía por WebSocket si el usuario está conectado."""
    notification = await notification_service.create_notification(
        db=db, notification_data=notification_data
    )
    
    # Broadcast por WebSocket al usuario conectado
    response = NotificationResponse.model_validate(notification)
    await manager.send_to_user(
        notification_data.user_id,
        response.model_dump_json(),
    )
    
    return notification


@router.get(
    "",
    response_model=PaginatedNotificationsResponse,
    summary="Listar notificaciones de un usuario",
)
async def get_notifications(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene la lista paginada de notificaciones de un usuario."""
    items = await notification_service.get_user_notifications(
        db=db, user_id=user_id, skip=skip, limit=limit
    )
    total = await notification_service.get_total_count(db=db, user_id=user_id)
    unread_count = await notification_service.get_unread_count(db=db, user_id=user_id)
    
    return PaginatedNotificationsResponse(
        items=items,
        total=total,
        has_more=(skip + limit) < total,
        unread_count=unread_count,
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Marcar notificación como leída",
)
async def mark_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Marca una notificación específica como leída."""
    return await notification_service.mark_as_read(
        db=db, notification_id=notification_id
    )


@router.patch(
    "/read-all",
    summary="Marcar todas como leídas",
)
async def mark_all_as_read(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Marca todas las notificaciones de un usuario como leídas."""
    count = await notification_service.mark_all_as_read(db=db, user_id=user_id)
    return {"message": f"{count} notificaciones marcadas como leídas"}


@router.get(
    "/unread-count",
    summary="Obtener contador de no leídas",
)
async def get_unread_count(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene la cantidad de notificaciones no leídas de un usuario."""
    count = await notification_service.get_unread_count(db=db, user_id=user_id)
    return {"unread_count": count}


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una notificación",
)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Elimina una notificación."""
    await notification_service.delete_notification(
        db=db, notification_id=notification_id
    )
