"""Modelo de cooldown para notificaciones automáticas.

Tabla auxiliar que registra cuándo se envió la última notificación
de cada regla para cada vehículo. Previene el spam de notificaciones
duplicadas al verificar si ya se envió recientemente.
"""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotificationCooldown(Base):
    """Registro de cooldown para evitar notificaciones duplicadas.

    Cada fila dice: "Para el vehículo X, la regla Y se disparó
    por última vez en Z". El scheduler consulta esta tabla con
    LEFT JOIN para filtrar vehículos que ya recibieron la alerta.
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
