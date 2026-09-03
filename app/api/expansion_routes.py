from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.api.auth_routes import get_current_user
from app.services.llm_service import get_llm_service
from app.services.mysql_service import MySQLService, get_mysql
from app.services.notification_service import NotificationService, app_url
from app.services.rate_limit_service import check_sliding, client_ip

expansion_router = APIRouter(prefix="/v1", tags=["Product services"])


def uid(current: Any) -> str:
    return str(current["user"].id)


def now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class JDRequest(BaseModel):
    job_title: str = Field(default="", max_length=300)
    company: str = Field(default="", max_length=200)
    job_description: str = Field(min_length=80, max_length=30000)
    resume: str = Field(min_length=30, max_length=30000)


@expansion_router.post("/job-matches")
def match_job(payload: JDRequest, current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    user_id = uid(current)
    resume_hash = hashlib.sha256(payload.resume.encode()).hexdigest()
    prompt = f"""Compare this resume to the job description. Return JSON with keys match_score (0-100 integer), strengths (array strings), skill_gaps (array strings), tailored_questions (array strings), summary (string). Resume:\n{payload.resume}\nJob description:\n{payload.job_description}"""
    result = get_llm_service().generate_json(prompt, system_prompt="You are a precise ATS and interview coach. Return only valid JSON.") or {}
    score = max(0, min(100, int(result.get("match_score", 0) or 0)))
    match_id = str(uuid.uuid4())
    db.get_session().execute("INSERT INTO jd_matches (id,user_id,job_title,company,jd_text,resume_hash,match_score,result_json,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (match_id,user_id,payload.job_title,payload.company,payload.job_description,resume_hash,score,json.dumps(result),now()))
    return {"id": match_id, "match_score": score, **result}


@expansion_router.get("/analytics")
def analytics(current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    user_id = uid(current); s = db.get_session()
    rows = s.execute("SELECT mode, score, created_at FROM history WHERE user_id=%s ORDER BY created_at DESC LIMIT 100", (user_id,)).all()
    scores = [float(r.get("score") or 0) for r in rows]
    by_mode: dict[str, list[float]] = {}
    for r in rows: by_mode.setdefault(r.get("mode") or "general", []).append(float(r.get("score") or 0))
    return {"total_interviews": len(rows), "average_score": round(sum(scores)/len(scores),1) if scores else 0, "best_score": max(scores) if scores else 0, "trend": [{"date": r.get("created_at"), "score": r.get("score")} for r in reversed(rows)], "by_mode": {k: round(sum(v)/len(v),1) for k,v in by_mode.items()}, "weak_topics": []}


class ScheduleRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    mode: str = Field(default="technical", max_length=48)
    starts_at: datetime
    duration_minutes: int = Field(default=45, ge=10, le=240)
    timezone: str = Field(default="UTC", max_length=64)
    recurrence: str = Field(default="none", pattern="^(none|daily|weekly)$")
    reminder_minutes_before: int = Field(default=30, ge=0, le=10080)


def ics_event(row: dict[str, Any]) -> str:
    start = row["starts_at"].strftime("%Y%m%dT%H%M%SZ")
    end = (row["starts_at"] + timedelta(minutes=int(row["duration_minutes"]))).strftime("%Y%m%dT%H%M%SZ")
    return "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//AI Interview//Scheduler//EN\nBEGIN:VEVENT\nUID:%s\nDTSTART:%s\nDTEND:%s\nSUMMARY:%s\nEND:VEVENT\nEND:VCALENDAR\n" % (row["id"], start, end, row["title"].replace("\n", " "))


@expansion_router.post("/scheduled-sessions")
def create_schedule(payload: ScheduleRequest, current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    sid = str(uuid.uuid4()); data = payload.model_dump(); data["starts_at"] = payload.starts_at.replace(tzinfo=None)
    db.get_session().execute("INSERT INTO scheduled_sessions (id,user_id,title,mode,config_json,starts_at,duration_minutes,timezone,recurrence,reminder_minutes_before,status,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'scheduled',%s,%s)", (sid,uid(current),payload.title,payload.mode,json.dumps({}),data["starts_at"],payload.duration_minutes,payload.timezone,payload.recurrence,payload.reminder_minutes_before,now(),now()))
    return {"id": sid, **data, "ics_url": f"/v1/scheduled-sessions/{sid}.ics"}


@expansion_router.get("/scheduled-sessions")
def list_schedules(current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    return {"items": db.get_session().execute("SELECT * FROM scheduled_sessions WHERE user_id=%s ORDER BY starts_at DESC LIMIT 100", (uid(current),)).all()}


@expansion_router.get("/scheduled-sessions/{session_id}.ics")
def download_ics(session_id: str, current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    row = db.get_session().execute("SELECT * FROM scheduled_sessions WHERE id=%s AND user_id=%s", (session_id,uid(current))).one()
    if not row: raise HTTPException(404, "Session not found")
    return Response(ics_event(row), media_type="text/calendar", headers={"Content-Disposition": f'attachment; filename="interview-{session_id}.ics"'})


class NegotiationRequest(BaseModel):
    role: str = Field(min_length=1, max_length=200)
    level: str = Field(default="", max_length=80)
    location: str = Field(default="", max_length=160)
    offer: dict[str, Any]
    target: dict[str, Any]
    message: str = Field(default="", max_length=6000)


@expansion_router.post("/negotiation/sessions")
def negotiate(payload: NegotiationRequest, current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    prompt = f"Estimate an uncertain market compensation range and respond as a supportive hiring manager. Role {payload.role}, level {payload.level}, location {payload.location}. Offer {payload.offer}; target {payload.target}; candidate message {payload.message}. Return JSON with market_estimate (object), reply (string), next_move (string)."
    result = get_llm_service().generate_json(prompt, system_prompt="Return only valid JSON and clearly label estimates as uncertain.") or {}
    sid = str(uuid.uuid4()); s = db.get_session(); s.execute("INSERT INTO negotiation_sessions (id,user_id,role,level,location,initial_offer_json,target_json,market_estimate_json,transcript_json,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (sid,uid(current),payload.role,payload.level,payload.location,json.dumps(payload.offer),json.dumps(payload.target),json.dumps(result.get("market_estimate",{})),json.dumps([{"role":"user","content":payload.message},{"role":"coach","content":result.get("reply","")}]),now(),now()))
    return {"id": sid, **result}


class KeyRequest(BaseModel): name: str = Field(min_length=1, max_length=120); scopes: list[str] = Field(default_factory=lambda: ["interviews:read"])


@expansion_router.post("/api-keys")
def create_key(payload: KeyRequest, current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    raw = "aik_" + secrets.token_urlsafe(32); kid = str(uuid.uuid4()); digest = hashlib.sha256(raw.encode()).hexdigest()
    db.get_session().execute("INSERT INTO api_keys (id,user_id,name,key_prefix,key_hash,scopes,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)", (kid,uid(current),payload.name,raw[:12],digest,json.dumps(payload.scopes),now()))
    return {"id": kid, "name": payload.name, "key": raw, "warning": "Copy this key now; it will not be shown again."}


@expansion_router.get("/api-keys")
def list_keys(current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    return {"items": db.get_session().execute("SELECT id,name,key_prefix,scopes,last_used_at,revoked_at,created_at FROM api_keys WHERE user_id=%s ORDER BY created_at DESC", (uid(current),)).all()}


@expansion_router.delete("/api-keys/{key_id}")
def revoke_key(key_id: str, current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    r = db.get_session().execute("UPDATE api_keys SET revoked_at=%s WHERE id=%s AND user_id=%s", (now(),key_id,uid(current))); return {"revoked": bool(getattr(r,"rowcount",0))}


class WebhookRequest(BaseModel): url: str = Field(min_length=10, max_length=1000); description: str = Field(default="", max_length=300); events: list[str] = Field(default_factory=lambda: ["interview.completed"])


@expansion_router.post("/webhooks")
def create_webhook(payload: WebhookRequest, current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    if not payload.url.startswith("https://"): raise HTTPException(400, "Webhook URL must use HTTPS")
    secret = secrets.token_urlsafe(32); wid = str(uuid.uuid4())
    db.get_session().execute("INSERT INTO webhook_endpoints (id,user_id,url,description,secret_hash,secret_hint,events,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (wid,uid(current),payload.url,payload.description,hashlib.sha256(secret.encode()).hexdigest(),secret[:6],json.dumps(payload.events),now(),now()))
    return {"id": wid, "url": payload.url, "secret": secret, "warning": "Copy this secret now; it will not be shown again."}


@expansion_router.get("/webhooks")
def list_webhooks(current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    return {"items": db.get_session().execute("SELECT id,url,description,events,active,created_at,updated_at FROM webhook_endpoints WHERE user_id=%s", (uid(current),)).all()}
