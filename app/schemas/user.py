"""Esquemas de validación para usuarios.

Define los modelos Pydantic para registro, login
y respuestas de la API relacionadas a usuarios.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Datos requeridos para registrar un nuevo usuario."""

    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    """Datos requeridos para iniciar sesión."""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Datos opcionales para actualizar el perfil de un usuario."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Datos del usuario devueltos por la API (sin contraseña)."""

    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    # Permite crear el esquema desde un objeto ORM de SQLAlchemy
    model_config = {"from_attributes": True}
