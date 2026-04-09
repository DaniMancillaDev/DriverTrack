"""Router REST de notificaciones.

Todos los endpoints requieren autenticación JWT.
Las notificaciones siempre se filtran por el usuario autenticado.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
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
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Crea una nueva notificación para el usuario autenticado.

    El user_id de la notificación siempre se toma del token JWT.
    No se puede crear notificaciones para otros usuarios.
    """
    # Forzar que la notificación pertenezca al usuario autenticado
    notification_data.user_id = current_user.id

    notification = await notification_service.create_notification(
        db=db, notification_data=notification_data
    )

    # Broadcast por WebSocket al usuario conectado
    response = NotificationResponse.model_validate(notification)
    await manager.send_to_user(
        current_user.id,
        response.model_dump_json(),
    )

    return notification


@router.get(
    "",
    response_model=PaginatedNotificationsResponse,
    summary="Listar mis notificaciones",
)
async def get_notifications(
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene la lista paginada de notificaciones del usuario autenticado."""
    items = await notification_service.get_user_notifications(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    total = await notification_service.get_total_count(db=db, user_id=current_user.id)
    unread_count = await notification_service.get_unread_count(
        db=db, user_id=current_user.id
    )

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
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Marca una notificación específica como leída.

    Verifica que la notificación pertenece al usuario autenticado.
    """
    notification = await notification_service.get_notification_by_id(
        db=db, notification_id=notification_id
    )
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada",
        )
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para modificar esta notificación",
        )
    return await notification_service.mark_as_read(db=db, notification_id=notification_id)


@router.patch(
    "/read-all",
    summary="Marcar todas las notificaciones como leídas",
)
async def mark_all_as_read(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Marca todas las notificaciones del usuario autenticado como leídas."""
    count = await notification_service.mark_all_as_read(
        db=db, user_id=current_user.id
    )
    return {"message": f"{count} notificaciones marcadas como leídas"}


@router.get(
    "/unread-count",
    summary="Contador de notificaciones no leídas",
)
async def get_unread_count(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene la cantidad de notificaciones no leídas del usuario autenticado."""
    count = await notification_service.get_unread_count(
        db=db, user_id=current_user.id
    )
    return {"unread_count": count}


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una notificación",
)
async def delete_notification(
    notification_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Elimina una notificación verificando la propiedad."""
    notification = await notification_service.get_notification_by_id(
        db=db, notification_id=notification_id
    )
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada",
        )
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para eliminar esta notificación",
        )
    await notification_service.delete_notification(db=db, notification_id=notification_id)
