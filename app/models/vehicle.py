"""Modelo de vehículo.

Define la tabla 'vehicles' y el enum VehicleType
para los tipos de vehículo permitidos (car/moto).
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VehicleType(str, enum.Enum):
    """Tipos de vehículo permitidos en el sistema."""

    CAR = "car"
    MOTO = "moto"


class Vehicle(Base):
    """Tabla de vehículos asociados a un usuario."""

    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    type: Mapped[VehicleType] = mapped_column(Enum(VehicleType), nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    plate: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Relaciones
    owner: Mapped["User"] = relationship(back_populates="vehicles")
    maintenances: Mapped[list["Maintenance"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Vehicle(id={self.id}, plate='{self.plate}')>"
