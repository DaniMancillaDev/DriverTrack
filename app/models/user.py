"""Modelo de usuario.

Define la tabla 'users' con los campos necesarios
para autenticación y perfil del usuario.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Tabla de usuarios registrados en la plataforma."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    photo_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, default=None
    )
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Preferencias de notificaciones
    pref_push_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pref_service_reminders: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pref_critical_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Un usuario puede tener varios vehículos
    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    # Un usuario puede tener varias notificaciones
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
