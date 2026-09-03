from __future__ import annotations

from datetime import datetime, timezone
import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.auth_routes import get_current_user
from app.services.mysql_service import MySQLService, get_mysql, get_mysql_health

user_data_router = APIRouter(prefix="/user-data", tags=["User Data"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SessionSnapshotRequest(BaseModel):
    session: dict


@user_data_router.get("/health")
def user_data_health():
    db = get_mysql_health()
    return {
        "status": "healthy" if db["status"] == "healthy" else "degraded",
        "service": "user-data",
        "mysql": db,
    }


@user_data_router.get("/session")
def get_session_snapshot(current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    user_id = current["user"].id
    s = db.get_session()
    row = s.execute("SELECT session_snapshot FROM user_data WHERE user_id=%s", (user_id,)).one()
    
    snapshot = None
    if row and row.session_snapshot:
        snapshot = json.loads(row.session_snapshot)
        
    return {"session": snapshot}


@user_data_router.put("/session")
def save_session_snapshot(
    payload: SessionSnapshotRequest,
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
):
    user_id = current["user"].id
    s = db.get_session()

    # Upsert profile via ON DUPLICATE KEY UPDATE below.
    row = s.execute("SELECT profile, created_at FROM user_data WHERE user_id=%s", (user_id,)).one()
    
    profile_dict = {
        "email": getattr(current["user"], "email", ""),
        "full_name": getattr(current["user"], "full_name", ""),
    }
    
    created_at = _utcnow()
    if row:
        if row.profile:
            profile_dict = json.loads(row.profile)
        if row.created_at:
            created_at = row.created_at
            
    # We enforce profile fields alignment though it's typically set during signup/profile updates.
    profile_dict["email"] = getattr(current["user"], "email", "")
    profile_dict["full_name"] = getattr(current["user"], "full_name", "")

    if row:
        s.execute(
            """
            UPDATE user_data 
            SET profile=%s, session_snapshot=%s, updated_at=%s 
            WHERE user_id=%s
            """,
            (json.dumps(profile_dict), json.dumps(payload.session), _utcnow(), user_id)
        )
    else:
        s.execute(
            """
            INSERT INTO user_data (user_id, profile, session_snapshot, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, json.dumps(profile_dict), json.dumps(payload.session), created_at, _utcnow())
        )
    return {"success": True}
