from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import uuid
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlparse

import jwt
import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.services.mysql_service import MySQLService, get_mysql, get_mysql_health
from app.services import email_service

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_password(password: str, *, salt: Optional[str] = None) -> str:
    raw_salt = salt or secrets.token_hex(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=raw_salt.encode("utf-8"),
        n=16384,
        r=8,
        p=1,
    )
    return f"{raw_salt}${derived.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, hashed = stored_hash.split("$", 1)
    except ValueError:
        return False
    candidate = _hash_password(password, salt=salt)
    return hmac.compare_digest(candidate, f"{salt}${hashed}")


def _serialize_user(user_doc) -> dict:
    base = {
        "id": str(user_doc.id),
        "email": getattr(user_doc, 'email', ""),
        "full_name": getattr(user_doc, 'full_name', ""),
        "auth_provider": getattr(user_doc, 'auth_provider', "email"),
        "created_at": getattr(user_doc, 'created_at', None),
        "updated_at": getattr(user_doc, 'updated_at', None),
    }
    return base


def _issue_session(db: MySQLService, user_id: uuid.UUID) -> str:
    now = _utcnow()
    expires_at = now + timedelta(days=settings.JWT_EXPIRATION_DAYS)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
        "jti": secrets.token_urlsafe(16),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    session_c = db.get_session()
    session_c.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (%s, %s, %s, %s)",
        (token, user_id, now, expires_at)
    )
    return token


def _frontend_url(path: str) -> str:
    """Build a frontend URL including the SPA's public base path.

    Avoids double-appending when FRONTEND_BASE_URL already ends with the path.
    """
    base = settings.FRONTEND_BASE_URL.rstrip("/")
    base_path = settings.FRONTEND_BASE_PATH.strip("/")
    if base_path and not base.endswith(f"/{base_path}"):
        base = f"{base}/{base_path}"
    return f"{base}{path}"


def _should_use_secure_cookie() -> bool:
    if settings.DEBUG:
        return False

    candidate_urls = [settings.FRONTEND_BASE_URL, *settings.ALLOWED_ORIGINS]
    for raw_url in candidate_urls:
        parsed = urlparse(raw_url)
        hostname = (parsed.hostname or "").lower()
        if hostname in {"localhost", "127.0.0.1"} or parsed.scheme == "http":
            return False
    return True


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.JWT_EXPIRATION_DAYS * 24 * 3600,
        samesite="lax",
        secure=_should_use_secure_cookie(),
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie("access_token", samesite="lax", secure=_should_use_secure_cookie())


def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    db: MySQLService = Depends(get_mysql),
):
    token = request.cookies.get("access_token")
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = uuid.UUID(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    s = db.get_session()
    session_row = s.execute("SELECT user_id, expires_at FROM sessions WHERE token=%s", (token,)).one()
    
    if not session_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session"
        )

    user = s.execute("SELECT * FROM users WHERE id=%s", (user_id,)).one()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return {"token": token, "user": user}


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ForgotPasswordResponse(BaseModel):
    success: bool
    message: str
    reset_token: Optional[str] = None
    reset_url: Optional[str] = None


@auth_router.get("/health")
def auth_health():
    db_health = get_mysql_health()
    return {
        "status": "healthy" if db_health["status"] == "healthy" else "degraded",
        "auth": "ready",
        "mysql": db_health,
    }


@auth_router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpRequest, response: Response, db: MySQLService = Depends(get_mysql)):
    now = _utcnow()
    email = payload.email.lower()
    
    s = db.get_session()
    existing = s.execute("SELECT id FROM users WHERE email=%s", (email,)).one()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists"
        )

    user_id = uuid.uuid4()
    s.execute(
        """
        INSERT INTO users (id, email, full_name, password_hash, auth_provider, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, email, payload.full_name.strip(), _hash_password(payload.password), "email", now, now)
    )

    profile_json = json.dumps({"email": email, "full_name": payload.full_name.strip()})
    s.execute(
        "INSERT INTO user_data (user_id, profile, session_snapshot, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
        (user_id, profile_json, None, now, now)
    )

    token = _issue_session(db, user_id)
    _set_auth_cookie(response, token)
    
    user_row = s.execute("SELECT * FROM users WHERE id=%s", (user_id,)).one()
    return AuthResponse(access_token=token, user=_serialize_user(user_row))


@auth_router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: MySQLService = Depends(get_mysql)):
    s = db.get_session()
    email = payload.email.lower()
    user = s.execute("SELECT * FROM users WHERE email=%s", (email,)).one()
    
    if not user or not _verify_password(payload.password, getattr(user, 'password_hash', "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    now = _utcnow()
    s.execute("UPDATE users SET updated_at=%s WHERE id=%s", (now, user.id))
    
    token = _issue_session(db, user.id)
    _set_auth_cookie(response, token)
    
    # refreshing object
    user = s.execute("SELECT * FROM users WHERE id=%s", (user.id,)).one()
    return AuthResponse(access_token=token, user=_serialize_user(user))


@auth_router.get("/me")
def me(current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    return {"user": _serialize_user(current["user"])}


@auth_router.patch("/profile", response_model=AuthResponse)
def update_profile(
    payload: UpdateProfileRequest,
    response: Response,
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
):
    user = current["user"]
    s = db.get_session()
    now = _utcnow()
    
    next_email = payload.email.lower() if payload.email else None
    if next_email and next_email != user.email:
        existing = s.execute("SELECT id FROM users WHERE email=%s", (next_email,)).one()
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with that email already exists",
            )

    new_full_name = payload.full_name.strip() if payload.full_name is not None else None
    if new_full_name is not None and len(new_full_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name must be at least 2 characters long",
        )

    new_pass = None
    if payload.new_password:
        if not payload.current_password or not _verify_password(payload.current_password, getattr(user, 'password_hash', "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect"
            )
        if len(payload.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long",
            )
        new_pass = _hash_password(payload.new_password)

    # Building dynamic update CQL
    set_clauses = ["updated_at=%s"]
    values = [now]
    
    if next_email:
        set_clauses.append("email=%s")
        values.append(next_email)
    if new_full_name is not None:
        set_clauses.append("full_name=%s")
        values.append(new_full_name)
    if new_pass:
        set_clauses.append("password_hash=%s")
        values.append(new_pass)
        
    values.append(user.id)
    
    s.execute(f"UPDATE users SET {', '.join(set_clauses)} WHERE id=%s", values)

    # Sync User Data Profile
    ud = s.execute("SELECT profile FROM user_data WHERE user_id=%s", (user.id,)).one()
    profile_dict = {}
    if ud and ud.profile:
        profile_dict = json.loads(ud.profile)
    
    if next_email:
        profile_dict["email"] = next_email
    if new_full_name is not None:
        profile_dict["full_name"] = new_full_name
        
    s.execute(
        "UPDATE user_data SET profile=%s, updated_at=%s WHERE user_id=%s",
        (json.dumps(profile_dict), now, user.id)
    )

    refreshed_user = s.execute("SELECT * FROM users WHERE id=%s", (user.id,)).one()
    _set_auth_cookie(response, current["token"])
    return AuthResponse(access_token=current["token"], user=_serialize_user(refreshed_user))


@auth_router.post("/logout")
def logout(
    response: Response, current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)
):
    s = db.get_session()
    s.execute("DELETE FROM sessions WHERE token=%s", (current["token"],))
    _clear_auth_cookie(response)
    return {"success": True}


@auth_router.delete("/account")
def delete_account(
    response: Response, current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)
):
    user_id = current["user"].id
    s = db.get_session()

    # Sessions: delete individually by querying first since token is PK
    sessions = s.execute("SELECT token FROM sessions WHERE user_id=%s", (user_id,))
    for sess in sessions:
        s.execute("DELETE FROM sessions WHERE token=%s", (sess.token,))

    s.execute("DELETE FROM history WHERE user_id=%s", (user_id,))
    s.execute("DELETE FROM user_data WHERE user_id=%s", (user_id,))
    s.execute("DELETE FROM users WHERE id=%s", (user_id,))
    
    _clear_auth_cookie(response)
    return {"success": True}


@auth_router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: MySQLService = Depends(get_mysql)):
    s = db.get_session()
    email = payload.email.lower()
    user = s.execute("SELECT id FROM users WHERE email=%s", (email,)).one()
    
    reset_token: Optional[str] = None
    if user:
        reset_token = secrets.token_urlsafe(32)
        s.execute(
            "UPDATE users SET reset_token=%s, reset_token_expires_at=%s, updated_at=%s WHERE id=%s",
            (reset_token, _utcnow() + timedelta(hours=1), _utcnow(), user.id)
        )

    response = ForgotPasswordResponse(
        success=True,
        message="If an account exists, a password reset link has been sent to that email.",
    )

    if reset_token:
        reset_url = _frontend_url(f"/auth?mode=reset&token={reset_token}")
        if email_service.is_configured():
            try:
                email_service.send_password_reset(email, reset_url)
            except Exception:
                logger.exception("Failed to send password reset email to %s", email)
        else:
            logger.warning("SMTP not configured; password reset email not sent to %s", email)

        if settings.DEBUG:
            response.reset_token = reset_token
            response.reset_url = reset_url

    return response


@auth_router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: MySQLService = Depends(get_mysql)):
    s = db.get_session()
    user = s.execute("SELECT id, reset_token_expires_at FROM users WHERE reset_token=%s", (payload.token,)).one()
    
    if not user or user.reset_token_expires_at < _utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token is invalid or expired"
        )

    # MySQL: setting a column to NULL directly in an UPDATE works fine.
    s.execute(
        "UPDATE users SET password_hash=%s, updated_at=%s, reset_token=null, reset_token_expires_at=null WHERE id=%s",
        (_hash_password(payload.new_password), _utcnow(), user.id)
    )
    return {"success": True, "message": "Password has been reset"}


def _oauth_redirect_uri(provider: str) -> str:
    return f"{settings.BACKEND_BASE_URL.rstrip('/')}/auth/oauth/{provider}/callback"


@auth_router.get("/oauth/{provider}")
def oauth_redirect(provider: str):
    provider = provider.lower()
    if provider not in {"google", "github"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )

    client_id = getattr(settings, f"{provider.upper()}_CLIENT_ID", "")
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth client ID for {provider} not configured"
        )

    state = secrets.token_urlsafe(16)
    redirect_uri = _oauth_redirect_uri(provider)

    if provider == "google":
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"response_type=code&"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=openid%20email%20profile&"
            f"state={state}"
        )
    else:  # github
        auth_url = (
            f"https://github.com/login/oauth/authorize?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=user:email&"
            f"state={state}"
        )

    response = RedirectResponse(auth_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        max_age=600,
        samesite="lax",
        secure=_should_use_secure_cookie(),
    )
    return response


@auth_router.get("/oauth/{provider}/callback")
async def oauth_callback(
    request: Request,
    provider: str,
    code: str,
    state: Optional[str] = None,
    db: MySQLService = Depends(get_mysql)
):
    provider = provider.lower()
    if provider not in {"google", "github"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )

    expected_state = request.cookies.get("oauth_state")
    if not state or not expected_state or not hmac.compare_digest(state, expected_state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing OAuth state"
        )

    client_id = getattr(settings, f"{provider.upper()}_CLIENT_ID", "")
    client_secret = getattr(settings, f"{provider.upper()}_CLIENT_SECRET", "")
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth credentials for {provider} not configured"
        )
        
    email = None
    full_name = None
    
    async with httpx.AsyncClient() as client:
        try:
            if provider == "google":
                redirect_uri = _oauth_redirect_uri(provider)
                token_res = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    }
                )
                token_data = token_res.json()
                if "error" in token_data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Google token exchange failed: {token_data}"
                    )
                
                access_token = token_data.get("access_token")
                user_res = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                user_info = user_res.json()
                email = user_info.get("email")
                full_name = user_info.get("name") or email.split("@")[0]
                
            else:  # github
                redirect_uri = _oauth_redirect_uri(provider)
                token_res = await client.post(
                    "https://github.com/login/oauth/access_token",
                    headers={"Accept": "application/json"},
                    data={
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri,
                    }
                )
                token_data = token_res.json()
                if "error" in token_data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"GitHub token exchange failed: {token_data}"
                    )
                
                access_token = token_data.get("access_token")
                user_res = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                        "User-Agent": "AI-Interview-Coach"
                    }
                )
                user_info = user_res.json()
                
                email_res = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                        "User-Agent": "AI-Interview-Coach"
                    }
                )
                emails = email_res.json()
                if isinstance(emails, list):
                    for email_obj in emails:
                        if email_obj.get("primary"):
                            email = email_obj.get("email")
                            break
                    if not email and emails:
                        email = emails[0].get("email")
                if not email:
                    email = user_info.get("email") or f"{user_info.get('login')}@github.com"
                full_name = user_info.get("name") or user_info.get("login") or email.split("@")[0]
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth authentication failed: {str(e)}"
            )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve email from OAuth provider"
        )

    # Get or create user in database
    s = db.get_session()
    user = s.execute("SELECT * FROM users WHERE email=%s", (email,)).one()
    now = _utcnow()
    
    if not user:
        user_id = uuid.uuid4()
        s.execute(
            """
            INSERT INTO users (id, email, full_name, password_hash, auth_provider, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, email, full_name, _hash_password(secrets.token_hex(16)), provider, now, now)
        )
        profile_json = json.dumps({"email": email, "full_name": full_name})
        s.execute(
            "INSERT INTO user_data (user_id, profile, session_snapshot, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
            (user_id, profile_json, None, now, now)
        )
        user = s.execute("SELECT * FROM users WHERE id=%s", (user_id,)).one()
    else:
        s.execute("UPDATE users SET updated_at=%s WHERE id=%s", (now, user.id))
        user = s.execute("SELECT * FROM users WHERE id=%s", (user.id,)).one()

    # Issue session
    token = _issue_session(db, user.id)

    # Redirect back to frontend dashboard
    response = RedirectResponse(url=_frontend_url("/app"))
    _set_auth_cookie(response, token)
    response.delete_cookie("oauth_state", samesite="lax", secure=_should_use_secure_cookie())
    return response


@auth_router.post("/oauth/{provider}")
def oauth_post_fallback(provider: str):
    return {"url": f"{settings.BACKEND_BASE_URL.rstrip('/')}/auth/oauth/{provider}"}
