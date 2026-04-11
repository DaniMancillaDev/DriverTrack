"""Configuración de persistencia con SQLAlchemy Asíncrono.

Este módulo define la infraestructura de conexión a la base de datos,
configurando el motor de ejecución, la fábrica de sesiones y la clase base
para el mapeo objeto-relacional (ORM).
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Ajustar la URL para SQLite si es necesario (usar aiosqlite para asincronía)
db_url = settings.database_url
if db_url.startswith("sqlite"):
    db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")

# Argumentos de conexión
connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}

# Motor de conexión asíncrono
engine = create_async_engine(
    db_url, 
    echo=settings.debug,
    connect_args=connect_args
)

# Fábrica de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Mapeo base para la estructura declarativa de SQLAlchemy.

    Todos los modelos de la aplicación heredan de esta clase para ser
    reconocidos por el motor de migraciones y la sesión de base de datos.
    """
    pass


async def get_db():
    """Dependencia de FastAPI que provee una sesión de base de datos asíncrona.

    Abre una sesión al inicio de la petición y la cierra al finalizar.
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
