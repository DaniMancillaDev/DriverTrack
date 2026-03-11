"""Repositorio específico para la entidad Vehicle."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.repositories.base import BaseRepository
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


class VehicleRepository(BaseRepository[Vehicle, VehicleCreate, VehicleUpdate]):
    """Repositorio para gestionar Vehículos."""

    def get_by_plate(
        self, db: Session, *, plate: str, exclude_id: Optional[int] = None
    ) -> Vehicle | None:
        """Busca un vehículo por su placa.
        
        Si exclude_id se provee, ignora ese ID (útil para validaciones al actualizar).
        """
        query = db.query(Vehicle).filter(Vehicle.plate == plate)
        if exclude_id is not None:
            query = query.filter(Vehicle.id != exclude_id)
        return query.first()

    def get_by_user(self, db: Session, *, user_id: int) -> list[Vehicle]:
        """Obtiene la lista de vehículos que pertenecen a un usuario específico."""
        return db.query(Vehicle).filter(Vehicle.user_id == user_id).all()


# Instancia única del repositorio para ser usada en los servicios
vehicle_repo = VehicleRepository(Vehicle)
