"""Repositorio específico para la entidad Vehicle."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from app.repositories.base import BaseRepository
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


class VehicleRepository(BaseRepository[Vehicle, VehicleCreate, VehicleUpdate]):
    """Repositorio para gestionar Vehículos asíncronamente."""

    async def create(self, db: AsyncSession, *, obj_in: VehicleCreate) -> Vehicle:
        """Crea un vehículo y carga su tipo para la respuesta."""
        db_obj = await super().create(db, obj_in=obj_in)
        # Re-buscamos para cargar la relación vehicle_type y evitar error de lazy loading
        return await self.get(db, db_obj.id) # type: ignore

    async def get(self, db: AsyncSession, id: int) -> Vehicle | None:
        """Obtiene un vehículo por ID con su tipo cargado."""
        query = select(Vehicle).filter(Vehicle.id == id).options(selectinload(Vehicle.vehicle_type))
        result = await db.execute(query)
        return result.scalars().first()

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Vehicle]:
        """Obtiene todos los vehículos con su tipo cargado."""
        query = select(Vehicle).options(selectinload(Vehicle.vehicle_type)).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_plate(
        self, db: AsyncSession, *, plate: str, exclude_id: Optional[int] = None
    ) -> Vehicle | None:
        """Busca un vehículo por su placa asíncronamente."""
        query = select(Vehicle).filter(Vehicle.plate == plate).options(selectinload(Vehicle.vehicle_type))
        if exclude_id is not None:
            query = query.filter(Vehicle.id != exclude_id)
        
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_user(self, db: AsyncSession, *, user_id: int) -> list[Vehicle]:
        """Obtiene la lista de vehículos de un usuario asíncronamente."""
        query = select(Vehicle).filter(Vehicle.user_id == user_id).options(selectinload(Vehicle.vehicle_type))
        result = await db.execute(query)
        return list(result.scalars().all())


# Instancia única del repositorio para ser usada en los servicios
vehicle_repo = VehicleRepository(Vehicle)
