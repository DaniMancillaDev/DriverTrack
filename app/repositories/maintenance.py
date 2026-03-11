"""Repositorio específico para la entidad Maintenance."""

from sqlalchemy.orm import Session

from app.models.maintenance import Maintenance
from app.repositories.base import BaseRepository
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate


class MaintenanceRepository(
    BaseRepository[Maintenance, MaintenanceCreate, MaintenanceUpdate]
):
    """Repositorio para gestionar Registros de Mantenimiento."""

    def get_by_vehicle(self, db: Session, *, vehicle_id: int) -> list[Maintenance]:
        """Obtiene y ordena el historial de mantenimientos de un vehículo."""
        return (
            db.query(Maintenance)
            .filter(Maintenance.vehicle_id == vehicle_id)
            .order_by(Maintenance.date.desc())
            .all()
        )

    def create_with_vehicle(
        self, db: Session, *, obj_in: MaintenanceCreate, vehicle_id: int
    ) -> Maintenance:
        """Crea el mantenimiento asignándole explícitamente el vehicle_id."""
        db_obj = Maintenance(
            vehicle_id=vehicle_id,
            **obj_in.model_dump(),
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


# Instancia única
maintenance_repo = MaintenanceRepository(Maintenance)
