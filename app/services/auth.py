"""Servicios de lógica de negocio para autenticación y gestión de usuarios.

Contiene funciones para el registro seguro, validación de credenciales
y el flujo de recuperación de contraseña mediante OTP (One-Time Password).
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import string
from datetime import datetime, timezone, timedelta

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.repositories.user import user_repo
from app.schemas.user import LoginRequest, UserCreate


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Registra un nuevo usuario en el sistema.

    Realiza validaciones de reglas de negocio, como la unicidad del email,
    y persiste al usuario con su contraseña hasheada de forma segura.
    """
    existing_user = await user_repo.get_by_email(db, email=user_data.email)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    return await user_repo.create_with_hashed_password(
        db, 
        obj_in=user_data, 
        hashed_password=get_password_hash(user_data.password)
    )


async def authenticate_user(db: AsyncSession, credentials: LoginRequest) -> User:
    """Verifica las credenciales asíncronamente."""
    user = await user_repo.get_by_email(db, email=credentials.email)

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    return user


async def create_otp_for_user(db: AsyncSession, email: str) -> None:
    """Genera y almacena un código de recuperación (OTP) para un usuario.

    Si el usuario existe:
    1. Invalida códigos anteriores no usados.
    2. Crea un nuevo código de 6 dígitos con 15 min de validez.
    3. Simula el envío por correo (mock).
    """
    user = await user_repo.get_by_email(db, email=email)
    if not user:
        # Prevenimos enumeración devolviendo OK en el router, pero no hacemos nada aquí
        return

    # Invalidar OTPs anteriores
    query = select(PasswordResetToken).where(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.is_used == False
    )
    result = await db.execute(query)
    old_tokens = result.scalars().all()
    for t in old_tokens:
        t.is_used = True

    # Generar nuevo de 6 dígitos seguro
    otp_code = ''.join(secrets.choice(string.digits) for _ in range(6))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    new_token = PasswordResetToken(
        user_id=user.id,
        otp_code=otp_code,
        expires_at=expires_at,
        is_used=False
    )
    db.add(new_token)
    await db.commit()

    # MOCK Email Service (AQUÍ DEBE IR SENDGRID / SMTP)
    print(f"\n==================================================")
    print(f"[MOCK EMAIL] Para: {email}")
    print(f"[MOCK EMAIL] Asunto: Restablece tu contraseña")
    print(f"[MOCK EMAIL] Tu código OTP de seguridad es: {otp_code}")
    print(f"==================================================\n")


async def verify_otp(db: AsyncSession, email: str, otp_code: str) -> PasswordResetToken:
    """Verifica si el OTP es válido para el email y no ha expirado."""
    user = await user_repo.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=400, detail="Código inválido o expirado")
        
    query = select(PasswordResetToken).where(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.otp_code == otp_code,
        PasswordResetToken.is_used == False
    )
    result = await db.execute(query)
    token = result.scalars().first()

    if not token:
        raise HTTPException(status_code=400, detail="Código inválido o expirado")
        
    # SQLite puede devolver un datetime "naive". Lo normalizamos a UTC para comparar:
    token_expiry = token.expires_at.replace(tzinfo=timezone.utc) if token.expires_at.tzinfo is None else token.expires_at
    
    if token_expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="El código ha expirado (15 minutos)")
        
    return token

async def reset_password_with_otp(db: AsyncSession, email: str, otp_code: str, new_password: str) -> None:
    """Valida el OTP y cambia la contraseña."""
    token = await verify_otp(db, email, otp_code)
    
    # Obtener usario para cambiar pass
    user = await user_repo.get_by_email(db, email=email)
    
    # Cambiar
    user.hashed_password = get_password_hash(new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    
    # Quemar token
    token.is_used = True
    
    await db.commit()
