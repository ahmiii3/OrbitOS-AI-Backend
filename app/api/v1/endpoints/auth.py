from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.security import OAuth2PasswordBearer
from app.dependencies.auth import get_current_user, oauth2_scheme
from app.dependencies.services import get_auth_service, get_user_service
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from app.schemas.token import TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter()
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Registers a new account, hashes password with bcrypt, and sends a 6-digit verification code to the user's email.",
)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    return await auth_service.register(payload)


@router.post(
    "/verify-email",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Verify email with 6-digit code",
    description="Validates the 6-digit verification code sent to the user's email and marks the account as verified.",
)
async def verify_email(
    payload: VerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    return await auth_service.verify_email(payload.code)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and return JWT tokens",
    description="Logs in a verified, active user and issues rotated access and refresh tokens.",
)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth_service.login(payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and get new access token",
    description="Validates active refresh token, invalidates it, and returns a new access/refresh token pair.",
)
async def refresh(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth_service.refresh_tokens(payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Log out user session",
    description="Revokes the refresh token and blacklists the current access token in Redis.",
)
async def logout(
    payload: RefreshTokenRequest,
    access_token: Optional[str] = Depends(optional_oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    return await auth_service.logout(refresh_token=payload.refresh_token, access_token=access_token)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset email",
    description="Generates a secure reset token (valid for 30 mins) and sends it via email if the account exists.",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    return await auth_service.forgot_password(payload)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete password reset",
    description="Validates token, updates hashed password in database, and revokes active user sessions.",
)
async def reset_password(
    payload: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    return await auth_service.reset_password(payload)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change password for authenticated user",
    description="Requires active authentication. Verifies current password and updates to new password.",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> MessageResponse:
    return await user_service.change_password(user=current_user, payload=payload)
