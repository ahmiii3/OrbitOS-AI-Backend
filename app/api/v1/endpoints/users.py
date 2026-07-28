from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_user_service
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns the profile information of the currently authenticated user.",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    return await user_service.get_current_user_profile(current_user)


@router.put(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Updates basic profile fields (name, email). If email changes, requires email re-verification.",
)
async def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    return await user_service.update_profile(user=current_user, payload=payload)
