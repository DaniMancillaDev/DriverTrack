"""Modelo de control de frecuencia (Cooldown) para notificaciones automáticas.

Esta tabla actúa como un registro de auditoría temporal para evitar que el sistema
envíe múltiples avisos duplicados sobre el mismo evento en un periodo corto
de tiempo (anti-spam).
"""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotificationCooldown(Base):
    """Registro de control de tiempo para una regla específica y un vehículo.

    El planificador consulta esta tabla mediante un LEFT JOIN para identificar
    qué vehículos están 'en periodo de enfriamiento' y saltarlos en el ciclo
    actual de notificaciones.
    """

    __tablename__ = "notification_cooldowns"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False
    )
    rule_key: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Identificador de la regla: mileage_warning, mileage_critical, etc."
    )
    last_sent_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Índice compuesto para la query de lookup del scheduler.
    # Permite filtrar rápidamente por (vehicle_id, rule_key) con
    # cobertura de last_sent_at para la condición temporal.
    __table_args__ = (
        Index(
            "ix_cooldown_lookup",
            "vehicle_id",
            "rule_key",
            "last_sent_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<NotificationCooldown(vehicle_id={self.vehicle_id}, "
            f"rule={self.rule_key}, sent={self.last_sent_at})>"
        )
