"""Modelo de mantenimiento.

Define la tabla 'maintenances' para registrar
el historial de mantenimientos de cada vehículo.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Maintenance(Base):
    """Tabla de registros de mantenimiento de vehículos."""

    __tablename__ = "maintenances"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    mileage: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Relación inversa con vehículo
    vehicle: Mapped["Vehicle"] = relationship(back_populates="maintenances")

    def __repr__(self) -> str:
        return f"<Maintenance(id={self.id}, date='{self.date}')>"
