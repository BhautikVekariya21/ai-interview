from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.auth_routes import get_current_user
from app.services.mysql_service import MySQLService, get_mysql
from app.services.notification_service import NotificationService

notification_router = APIRouter(prefix="/notifications", tags=["Notifications"])


class ReadRequest(BaseModel):
    ids: Optional[List[str]] = Field(default=None, max_length=200)


class PreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    reminders_enabled: Optional[bool] = None
    weekly_digest_enabled: Optional[bool] = None
    quiet_hours_start: Optional[int] = Field(default=None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(default=None, ge=0, le=23)
    timezone: Optional[str] = Field(default=None, max_length=64)


def _uid(current) -> str:
    return str(current["user"].id)


@notification_router.get("")
def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(30, ge=1, le=100),
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
):
    return NotificationService(db).list(_uid(current), limit=limit, unread_only=unread_only)


@notification_router.post("/read")
def mark_notifications_read(
    payload: ReadRequest,
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
):
    return {"marked": NotificationService(db).mark_read(_uid(current), payload.ids)}


@notification_router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
):
    return {"deleted": NotificationService(db).delete(_uid(current), notification_id)}


@notification_router.get("/preferences")
def get_preferences(current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    return NotificationService(db).get_preferences(_uid(current))


@notification_router.put("/preferences")
def update_preferences(
    payload: PreferenceUpdate,
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
):
    return NotificationService(db).update_preferences(_uid(current), payload.model_dump(exclude_none=True))
