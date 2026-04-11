"""Modelo para la sincronización de tareas programadas (Cron jobs).

Permite que múltiples instancias de la aplicación (workers) coordinen la
ejecución de tareas periódicas, evitando ejecuciones duplicadas o
conflictos de recursos en la base de datos.
"""

from sqlalchemy import Column, String, DateTime
from app.database import Base

class SchedulerLock(Base):
    """Mecanismo de bloqueo lógico para el planificador de tareas.

    Almacena el nombre de la tarea (task_name) y la marca de tiempo de su
    última ejecución exitosa, actuando como un semáforo distribuido simple.
    """
    __tablename__ = "scheduler_locks"

    # task_name e.g. "notification_check" or "notification_purge"
    task_name = Column(String, primary_key=True, index=True)
    # The last time it was run successfully
    last_run_at = Column(DateTime(timezone=True), nullable=True)
