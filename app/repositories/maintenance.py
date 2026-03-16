"""Repositorio específico para la entidad Maintenance."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance import Maintenance
from app.repositories.base import BaseRepository
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate


class MaintenanceRepository(
    BaseRepository[Maintenance, MaintenanceCreate, MaintenanceUpdate]
):
    """Repositorio para gestionar Registros de Mantenimiento asíncronamente."""

    async def get_by_vehicle(
        self, db: AsyncSession, *, vehicle_id: int, skip: int = 0, limit: int = 50
    ) -> list[Maintenance]:
        """Obtiene y ordena el historial asíncronamente con paginación."""
        result = await db.execute(
            select(Maintenance)
            .filter(Maintenance.vehicle_id == vehicle_id)
            .order_by(Maintenance.date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_with_vehicle(
        self, db: AsyncSession, *, obj_in: MaintenanceCreate, vehicle_id: int
    ) -> Maintenance:
        """Crea el mantenimiento asíncronamente."""
        db_obj = Maintenance(
            vehicle_id=vehicle_id,
            **obj_in.model_dump(),
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# Instancia única
maintenance_repo = MaintenanceRepository(Maintenance)
