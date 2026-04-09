"""Router de autenticación.

Endpoints públicos para registro e inicio de sesión.
Los tokens generados siempre usan sub=str(user_id).
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.core.deps import CurrentUser, get_current_user
from app.database import get_db
from app.schemas.user import LoginRequest, UserCreate, UserResponse, TokenResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Crea una nueva cuenta y devuelve un JWT de acceso.

    - El email debe ser único en la plataforma.
    - La contraseña se almacena hasheada con bcrypt.
    - sub del token = str(user.id)
    """
    user = await auth_service.create_user(db=db, user_data=user_data)
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Valida las credenciales y devuelve un JWT de acceso.

    - sub del token = str(user.id)
    - El token expira según ACCESS_TOKEN_EXPIRE_MINUTES en settings.
    - Responde con 401 genérico para no revelar si el email existe.
    """
    user = await auth_service.authenticate_user(db=db, credentials=credentials)
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


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
