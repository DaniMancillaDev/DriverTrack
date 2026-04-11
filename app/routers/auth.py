"""Router de autenticación.

Este módulo gestiona los puntos de entrada para el registro de nuevos usuarios,
el inicio de sesión y la gestión de tokens JWT (acceso y renovación).
También incluye funcionalidades para la recuperación de contraseña mediante OTP.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

from app.core.security import create_access_token, create_refresh_token, decode_refresh_token
from app.core.deps import CurrentUser
from app.database import get_db
from app.schemas.user import (
    LoginRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    UserCreate,
    UserResponse,
    TokenResponse,
    ForgotPasswordRequest,
    VerifyOTPRequest,
    ResetPasswordRequest,
)
from app.services import auth as auth_service
from app.services import users as users_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Crea una nueva cuenta de usuario y devuelve el primer par de tokens JWT.

    Proceso:
    1. Valida que el email no esté registrado previamente.
    2. Hashea la contraseña de forma segura.
    3. Crea el registro en la base de datos.
    4. Genera un Access Token (corto plazo) y un Refresh Token (largo plazo).
    
    El campo 'sub' (subject) del token contiene el ID del usuario como cadena.
    """
    user = await auth_service.create_user(db=db, user_data=user_data)
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
)
@limiter.limit("10/minute")
async def login(request: Request, credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Valida credenciales y emite tokens de sesión.

    Verificaciones:
    - Existencia del usuario por email.
    - Coincidencia de contraseña (hashing).
    - Estado activo de la cuenta.

    En caso de fallo, se devuelve un error 401 genérico para mitigar ataques de enumeración.
    """
    user = await auth_service.authenticate_user(db=db, credentials=credentials)
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Solicitar código OTP para restablecer contraseña",
)
@limiter.limit("3/minute")
async def forgot_password(request: Request, body_request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Inicia el flujo de recuperación de contraseña.

    Genera un código OTP de 6 dígitos con expiración y lo vincula al email.
    Por seguridad, la respuesta es siempre positiva para no confirmar la existencia del email.
    """
    await auth_service.create_otp_for_user(db, body_request.email)
    return {"message": "Si el correo está registrado, recibirás un código OTP de 6 dígitos."}


@router.post(
    "/verify-otp",
    status_code=status.HTTP_200_OK,
    summary="Verificar código OTP",
)
@limiter.limit("10/minute")
async def verify_otp(request: Request, body_request: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """Verifica si el OTP proporcionado es válido y no ha expirado."""
    await auth_service.verify_otp(db, body_request.email, body_request.otp_code)
    return {"message": "Código válido"}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Restablecer la contraseña con OTP",
)
@limiter.limit("5/minute")
async def reset_password(request: Request, body_request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Valida el OTP y establece una nueva contraseña."""
    await auth_service.reset_password_with_otp(
        db, body_request.email, body_request.otp_code, body_request.new_password
    )
    return {"message": "Contraseña actualizada exitosamente"}


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Renovar access token",
)
async def refresh_access_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Emite un nuevo access token a partir de un refresh token válido.

    - No requiere credenciales (email/password).
    - El refresh token debe ser de tipo 'refresh' y no estar expirado.
    - Si el refresh token es inválido o expirado, devuelve 401.
    - El usuario debe estar activo.
    """
    payload = decode_refresh_token(body.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub: str | None = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
        )

    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
        )

    user = await users_service.get_user(db, user_id=user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    new_access_token = create_access_token(data={"sub": str(user.id)})
    return RefreshTokenResponse(access_token=new_access_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Verificar token y obtener usuario actual",
)
async def verify_token(current_user: CurrentUser):
    """Endpoint para validar que el token sigue siendo válido.

    Útil para que Flutter verifique si el token local es aún válido
    al arrancar la app sin redirigir al login innecesariamente.
    """
    return current_user


@router.post(
    "/token",
    include_in_schema=False,  # No mostrar en docs — es solo para Swagger Authorize
)
async def oauth2_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint OAuth2 exclusivo para el botón Authorize de Swagger UI.

    ⚠️ NO usar desde Flutter — usar /auth/login con JSON.
    """
    credentials = LoginRequest(email=form_data.username, password=form_data.password)
    user = await auth_service.authenticate_user(db=db, credentials=credentials)
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
