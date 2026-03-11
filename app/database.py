"""Configuración de la base de datos con SQLAlchemy.

Define el motor de conexión, la fábrica de sesiones
y la clase base para los modelos ORM.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Argumentos de conexión (SQLite requiere check_same_thread en False para FastAPI)
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

# Motor de conexión
engine = create_engine(
    settings.database_url, 
    echo=settings.debug,
    connect_args=connect_args
)

# Fábrica de sesiones (cada petición HTTP usa una sesión independiente)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos SQLAlchemy."""
    pass


def get_db():
    """Dependencia de FastAPI que provee una sesión de base de datos.

    Abre una sesión al inicio de la petición y la cierra al finalizar,
    garantizando que los recursos se liberen correctamente.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
