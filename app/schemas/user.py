"""Esquemas de validación para usuarios.

Define los modelos Pydantic para registro, login
y respuestas de la API relacionadas a usuarios.
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─── Requests de autenticación ────────────────────────────────


class UserCreate(BaseModel):
    """Datos requeridos para registrar un nuevo usuario."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Valida que la contraseña tenga al menos una mayúscula y un número."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número")
        return v


class LoginRequest(BaseModel):
    """Datos requeridos para iniciar sesión."""

    email: EmailStr
    password: str


# ─── Requests de actualización ────────────────────────────────


class ProfileUpdateRequest(BaseModel):
    """Datos para actualizar el nombre del usuario autenticado.

    Solo permite cambiar el nombre — email y contraseña tienen
    endpoints dedicados con sus propias validaciones.
    """

    full_name: str = Field(..., min_length=2, max_length=255)


class ChangePasswordRequest(BaseModel):
    """Datos para cambiar la contraseña del usuario autenticado."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def new_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("La nueva contraseña debe contener al menos una mayúscula")
        if not re.search(r"\d", v):
            raise ValueError("La nueva contraseña debe contener al menos un número")
        return v


class PhotoConfirmRequest(BaseModel):
    """Body para confirmar la subida de una foto vía pre-signed URL.

    El object_key es validado por el router para verificar
    que pertenece al usuario autenticado.
    """

    object_key: str = Field(..., min_length=5, max_length=512)


class UserUpdate(BaseModel):
    """Datos opcionales para actualizar el perfil (uso interno/admin).

    Para actualizaciones de usuario autenticado, usar ProfileUpdateRequest.
    """

    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    is_active: Optional[bool] = None


# ─── Responses ────────────────────────────────────────────────


class UserResponse(BaseModel):
    """Datos del usuario devueltos por la API (sin contraseña ni hash)."""

    id: int
    email: str
    full_name: str
    is_active: bool
    photo_url: Optional[str] = None
    created_at: datetime
    password_changed_at: Optional[datetime] = None

    # Permite crear el esquema desde un objeto ORM de SQLAlchemy
    model_config = {"from_attributes": True}


class RefreshTokenRequest(BaseModel):
    """Body para solicitar un nuevo access token vía refresh token."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Respuesta de autenticación con JWT."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenResponse(BaseModel):
    """Respuesta del endpoint /auth/refresh."""

    access_token: str
    token_type: str = "bearer"


class PresignedUrlResponse(BaseModel):
    """URLs pre-firmadas para subir/acceder a la foto de perfil."""

    upload_url: str
    photo_url: str
    object_key: str
