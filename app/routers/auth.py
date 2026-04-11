"""Router de autenticación.

Endpoints públicos para registro e inicio de sesión.
Los tokens generados siempre usan sub=str(user_id).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

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
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Crea una nueva cuenta y devuelve un JWT de acceso + refresh token.

    - El email debe ser único en la plataforma.
    - La contraseña se almacena hasheada con bcrypt.
    - sub del token = str(user.id)
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
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Valida las credenciales y devuelve un JWT de acceso + refresh token.

    - sub del token = str(user.id)
    - El access token expira según ACCESS_TOKEN_EXPIRE_MINUTES en settings.
    - El refresh token expira según REFRESH_TOKEN_EXPIRE_DAYS en settings.
    - Responde con 401 genérico para no revelar si el email existe.
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
