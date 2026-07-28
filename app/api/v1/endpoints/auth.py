from typing import Optional
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer
from app.dependencies.services import get_auth_service
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
)
from app.schemas.token import TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter()
optional_security_scheme = HTTPBearer(auto_error=False)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with name, email, and password.",
)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    return await auth_service.register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and get token",
    description="Verifies user credentials and returns an access token.",
)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth_service.login(payload)
