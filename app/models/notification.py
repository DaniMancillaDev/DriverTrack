"""Modelo de notificación.

Define la tabla 'notifications' para almacenar
notificaciones internas de la aplicación por usuario.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

import enum


class NotificationType(str, enum.Enum):
    """Tipos de notificación soportados."""
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"
    ERROR = "error"


class Notification(Base):
    """Tabla de notificaciones persistentes por usuario."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType), default=NotificationType.INFO, nullable=False
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Relación con usuario
    user: Mapped["User"] = relationship(back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, title='{self.title}', type='{self.type}')>"
