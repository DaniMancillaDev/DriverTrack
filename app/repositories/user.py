"""Repositorio específico para la entidad User."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserCreate


class UserRepository(BaseRepository[User, UserCreate, UserCreate]):
    """Repositorio para gestionar Usuarios.
    
    Hereda el CRUD básico y añade operaciones específicas del negocio.
    """

    def get_by_email(self, db: Session, *, email: str) -> User | None:
        """Busca un usuario por su dirección de email."""
        return db.query(User).filter(User.email == email).first()

    def create_with_hashed_password(
        self, db: Session, *, obj_in: UserCreate, hashed_password: str
    ) -> User:
        """Crea un usuario inyectando la contraseña ya hasheada."""
        db_obj = User(
            email=obj_in.email,
            hashed_password=hashed_password,
            full_name=obj_in.full_name,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


# Instancia única a ser inyectada/usada por los servicios
user_repo = UserRepository(User)
