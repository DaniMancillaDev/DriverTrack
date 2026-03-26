"""Repositorio específico para la entidad Notification."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.base import BaseRepository
from app.schemas.notification import NotificationCreate, NotificationUpdate


class NotificationRepository(
    BaseRepository[Notification, NotificationCreate, NotificationUpdate]
):
    """Repositorio para gestionar Notificaciones asíncronamente."""

    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Notification]:
        """Obtiene las notificaciones de un usuario, ordenadas por más recientes."""
        result = await db.execute(
            select(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, db: AsyncSession, *, user_id: int) -> int:
        """Cuenta el total de notificaciones de un usuario."""
        result = await db.execute(
            select(func.count(Notification.id))
            .filter(Notification.user_id == user_id)
        )
        return result.scalar_one()

    async def get_unread_count(self, db: AsyncSession, *, user_id: int) -> int:
        """Cuenta las notificaciones no leídas de un usuario."""
        result = await db.execute(
            select(func.count(Notification.id))
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        return result.scalar_one()

    async def mark_as_read(self, db: AsyncSession, *, notification_id: int) -> Notification | None:
        """Marca una notificación como leída."""
        notification = await self.get(db, notification_id)
        if notification:
            notification.is_read = True
            await db.commit()
            await db.refresh(notification)
        return notification

    async def mark_all_as_read(self, db: AsyncSession, *, user_id: int) -> int:
        """Marca todas las notificaciones de un usuario como leídas.
        
        Retorna el número de notificaciones actualizadas.
        """
        result = await db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .values(is_read=True)
        )
        await db.commit()
        return result.rowcount

    async def create_for_user(
        self,
        db: AsyncSession,
        *,
        obj_in: NotificationCreate,
    ) -> Notification:
        """Crea una notificación para un usuario."""
        db_obj = Notification(
            user_id=obj_in.user_id,
            title=obj_in.title,
            message=obj_in.message,
            type=obj_in.type,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# Instancia única
notification_repo = NotificationRepository(Notification)
