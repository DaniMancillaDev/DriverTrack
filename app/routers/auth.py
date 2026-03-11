"""Router de autenticación."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import LoginRequest, UserCreate, UserResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Crea una nueva cuenta de usuario."""
    return auth_service.create_user(db=db, user_data=user_data)


@router.post(
    "/login",
    summary="Iniciar sesión",
)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Valida las credenciales del usuario."""
    user = auth_service.authenticate_user(db=db, credentials=credentials)
    return {
        "message": "Login exitoso",
        "user": UserResponse.model_validate(user),
    }
