"""Modelos de SQLAlchemy para la base de datos.

Importa todos los modelos aquí para que SQLAlchemy los registre
y Alembic pueda detectarlos automáticamente.
"""

from app.models.user import User
from app.models.vehicle import Vehicle, VehicleType
from app.models.maintenance import Maintenance
from app.models.notification import Notification, NotificationType

__all__ = ["User", "Vehicle", "VehicleType", "Maintenance", "Notification", "NotificationType"]
