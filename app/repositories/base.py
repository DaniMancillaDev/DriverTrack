"""Repositorio base para acceso a datos genérico.

Proporciona operaciones CRUD estándar usando SQLAlchemy.
De este modo, los servicios no necesitan conocer SQLAlchemy.
"""

from typing import Any, Generic, Type, TypeVar

from pydantic import BaseModel
from typing import Any, Generic, List, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

# Tipos genéricos para Modelos (SQLAlchemy) y Esquemas (Pydantic)
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Clase base genérica (CRUD) para operaciones de base de datos asíncronas.
    
    Implementa el Patrón Repositorio con soporte para AsyncSession.
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        """Obtiene un registro por su ID primario."""
        result = await db.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Obtiene una lista paginada de registros."""
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """Crea un nuevo registro en la base de datos a partir de un esquema."""
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """Actualiza un registro existente aplicando solo los campos modificados."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> ModelType | None:
        """Elimina un registro de la base de datos por su ID."""
        # Primero buscamos el objeto
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
