"""Modelo de datos para Vehículos.

Define la estructura de la tabla 'vehicles' y el catálogo de tipos
de vehículos (vehicle_types). Almacena información crítica como el
kilometraje actual y el límite configurado para alertas preventivas.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VehicleType(Base):
    """Catálogo maestro de categorías de vehículos.

    Define los tipos disponibles (Slug, Etiqueta, Icono) que se muestran
    en la interfaz de usuario para categorizar los vehículos.
    """

    __tablename__ = "vehicle_types"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(String(100), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Relaciones
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="vehicle_type")


class Vehicle(Base):
    """Representa un vehículo individual perteneciente a un usuario.

    Contiene los datos técnicos (marca, modelo, placa) y el estado de
    uso actual (kilometraje). Es la entidad central para el sistema de alertas.
    """

    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    type_id: Mapped[int] = mapped_column(
        ForeignKey("vehicle_types.id"), nullable=False, index=True
    )
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    plate: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    mileage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_mileage: Mapped[int] = mapped_column(Integer, nullable=False, default=50000)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    next_service: Mapped[str] = mapped_column(
        String(100), nullable=True, default="Pending Service Config"
    )
    is_favorite: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Relaciones
    owner: Mapped["User"] = relationship(back_populates="vehicles")
    vehicle_type: Mapped["VehicleType"] = relationship(back_populates="vehicles")
    maintenances: Mapped[list["Maintenance"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Vehicle(id={self.id}, plate='{self.plate}')>"
