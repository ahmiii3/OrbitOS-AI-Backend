from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

from app.models.user import User
from app.models.notification import Notification
from app.dependencies.auth import get_current_user

router = APIRouter()

class NotificationResponse(BaseModel):
    id: UUID
    title: str
    message: str
    is_read: bool
    created_at: datetime

@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """Fetch recent notifications for the logged-in user."""
    notifications = await Notification.filter(user_id=current_user.id).order_by("-created_at").limit(limit)
    return notifications

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Mark a specific notification as read."""
    notification = await Notification.get_or_none(id=notification_id, user_id=current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notification.is_read = True
    await notification.save()
    return notification
