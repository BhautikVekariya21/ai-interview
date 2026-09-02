from __future__ import annotations

import hashlib
import hmac
import logging
import re
import secrets
import uuid
import json
import base64
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Optional
from urllib.parse import urlencode, urlparse

import jwt
import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.config import settings
from app.services.mysql_service import MySQLService, get_mysql, get_mysql_health
from app.services import email_service
from app.services import rate_limit_service

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

MIN_PASSWORD_LENGTH = 8

# Precomputed hash of a random string, used to spend the same KDF cost on login
# attempts for non-existent accounts so response timing can't reveal whether an
# email is registered.
_DUMMY_PASSWORD_HASH = None

# Generic, enumeration-safe messages reused across endpoints.
GENERIC_SIGNUP_MESSAGE = "If that email can be registered, a verification link has been sent."
GENERIC_RESET_MESSAGE = "If an account exists, a password reset link has been sent to that email."
GENERIC_INVALID_CREDENTIALS = "Invalid email or password"

PASSWORD_POLICY_MESSAGE = (
    f"Password must be at least {MIN_PASSWORD_LENGTH} characters long and contain "
    "at least one uppercase letter, one lowercase letter, one number, and one special character"
)


def _validate_password_strength(password: str) -> str:
    """Enforce the shared password policy. Returns the password or raises ValueError."""
    if (
        len(password) < MIN_PASSWORD_LENGTH
        or not re.search(r"[A-Z]", password)
        or not re.search(r"[a-z]", password)
        or not re.search(r"[0-9]", password)
        or not re.search(r"[^A-Za-z0-9]", password)
    ):
        raise ValueError(PASSWORD_POLICY_MESSAGE)
    return password


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


def _dummy_hash() -> str:
    global _DUMMY_PASSWORD_HASH
    if _DUMMY_PASSWORD_HASH is None:
        _DUMMY_PASSWORD_HASH = _hash_password(secrets.token_hex(16))
    return _DUMMY_PASSWORD_HASH


def _hash_token(raw_token: str) -> str:
    """SHA-256 hex digest used to store reset/verification tokens at rest.

    Tokens are already high-entropy random values, so a fast hash is sufficient
    to keep the plaintext out of the database while allowing O(1) lookup.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _client_ip(request: Request) -> str:
    return rate_limit_service.client_ip(request)


def _enforce_rate_limit(request: Request, scope: str, identifier: str, captcha_token: Optional[str]) -> None:
    """Apply sliding-window rate limiting with a CAPTCHA fallback.

    Raises 429 on hard trip, or 400 when a CAPTCHA is required but missing/invalid.
    Uses only the (scope, identifier) counter — never reveals account existence.
    """
    decision = rate_limit_service.check_rate(scope, identifier)
    if decision.captcha_required:
        if not rate_limit_service.verify_captcha(captcha_token, _client_ip(request)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CAPTCHA verification required",
                headers={"X-Captcha-Required": "1"},
            )
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
            headers={"Retry-After": str(decision.retry_after)},
        )


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

    # Store a SHA-256 hash of the token — not the token itself — so a leaked
    # database does not hand an attacker every active session.
    token_hash = _hash_token(token)

    session_c = db.get_session()
    session_c.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (%s, %s, %s, %s)",
        (token_hash, user_id, now, expires_at)
    )
    return token


def _clerk_issuer_from_publishable_key() -> Optional[str]:
    """Derive Clerk's Frontend API origin from its public publishable key."""
    key = settings.VITE_CLERK_PUBLISHABLE_KEY
    if not key or not key.startswith("pk_"):
        return None
    try:
        encoded = key.split("_", 2)[2]
        encoded += "=" * (-len(encoded) % 4)
        hostname = base64.urlsafe_b64decode(encoded).decode("utf-8").rstrip("$").lower()
    except (IndexError, UnicodeDecodeError, ValueError):
        return None
    if not re.fullmatch(r"[a-z0-9.-]+\.clerk\.accounts(?:\.dev)?", hostname):
        return None
    return f"https://{hostname}"


def _clerk_config() -> tuple[str, str]:
    issuer = settings.CLERK_JWT_ISSUER or _clerk_issuer_from_publishable_key()
    jwks_url = settings.CLERK_JWKS_URL or (f"{issuer}/.well-known/jwks.json" if issuer else None)
    if not issuer or not jwks_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk backend authentication is not configured",
        )
    return issuer.rstrip("/"), jwks_url


@lru_cache(maxsize=4)
def _clerk_jwk_client(jwks_url: str):
    return jwt.PyJWKClient(jwks_url)


def _clerk_subject(token: str) -> str:
    """Verify a Clerk token and return its stable user subject."""
    try:
        issuer, jwks_url = _clerk_config()
        signing_key = _clerk_jwk_client(jwks_url).get_signing_key_from_jwt(token)
        options = {"verify_aud": False}
        kwargs: dict[str, Any] = {
            "algorithms": ["RS256"],
            "options": options,
            "issuer": issuer,
        }
        claims = jwt.decode(token, signing_key.key, **kwargs)
        subject = str(claims.get("sub", ""))
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Clerk session")
    except Exception:
        logger.exception("Unable to verify Clerk session")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Clerk verification unavailable")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Clerk session")
    return subject


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
    token_hash = _hash_token(token)
    session_row = s.execute("SELECT user_id, expires_at FROM sessions WHERE token=%s", (token_hash,)).one()
    
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
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=256)
    full_name: str
    captcha_token: Optional[str] = None

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=256)
    captcha_token: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    captcha_token: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=256)
    captcha_token: Optional[str] = None

    @field_validator("new_password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr
    captcha_token: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ClerkSessionExchangeRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)


class ForgotPasswordResponse(BaseModel):
    success: bool
    message: str
    # Present only when EXPOSE_RESET_TOKEN_IN_DEBUG is explicitly enabled (local dev).
    reset_token: Optional[str] = None
    reset_url: Optional[str] = None


class SimpleMessageResponse(BaseModel):
    success: bool
    message: str


@auth_router.get("/health")
def auth_health():
    db_health = get_mysql_health()
    return {
        "status": "healthy" if db_health["status"] == "healthy" else "degraded",
        "auth": "ready",
        "mysql": db_health,
    }


@auth_router.post("/clerk/session", response_model=AuthResponse)
def exchange_clerk_session(
    response: Response,
    payload: ClerkSessionExchangeRequest,
    authorization: Optional[str] = Header(default=None),
    db: MySQLService = Depends(get_mysql),
):
    """Verify a Clerk session and issue the app session used by API services."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Clerk session required")

    subject = _clerk_subject(authorization.split(" ", 1)[1].strip())
    provider = f"clerk:{subject}"
    if len(provider) > 50:
        provider = f"clerk:{hashlib.sha256(subject.encode('utf-8')).hexdigest()}"

    s = db.get_session()
    now = _utcnow()
    user = s.execute("SELECT * FROM users WHERE auth_provider=%s", (provider,)).one()
    if not user:
        email_owner = s.execute("SELECT * FROM users WHERE email=%s", (payload.email.lower(),)).one()
        if email_owner:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account already exists for this email. Sign in with that account to link it.",
            )
        user_id = uuid.uuid4()
        s.execute(
            """
            INSERT INTO users (id, email, full_name, password_hash, auth_provider, created_at, updated_at, email_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, payload.email.lower(), payload.full_name, _hash_password(secrets.token_hex(16)), provider, now, now, 1),
        )
        profile_json = json.dumps({"email": payload.email.lower(), "full_name": payload.full_name})
        s.execute(
            "INSERT INTO user_data (user_id, profile, session_snapshot, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
            (user_id, profile_json, None, now, now),
        )
        user = s.execute("SELECT * FROM users WHERE id=%s", (user_id,)).one()
    else:
        s.execute(
            "UPDATE users SET full_name=%s, updated_at=%s WHERE id=%s",
            (payload.full_name, now, user.id),
        )
        user = s.execute("SELECT * FROM users WHERE id=%s", (user.id,)).one()

    token = _issue_session(db, user.id)
    _set_auth_cookie(response, token)
    return AuthResponse(access_token=token, user=_serialize_user(user))


@auth_router.get("/config")
def auth_config():
    """Public auth config for the frontend (no secrets)."""
    return {
        "turnstile_site_key": settings.TURNSTILE_SITE_KEY or None,
        "email_verification_required": settings.REQUIRE_EMAIL_VERIFICATION,
    }


@auth_router.post("/signup", response_model=SimpleMessageResponse, status_code=status.HTTP_202_ACCEPTED)
def signup(payload: SignUpRequest, request: Request, background: BackgroundTasks, db: MySQLService = Depends(get_mysql)):
    email = payload.email.lower()
    _enforce_rate_limit(request, "signup", _client_ip(request), payload.captcha_token)

    now = _utcnow()
    s = db.get_session()
    existing = s.execute("SELECT id, email_verified FROM users WHERE email=%s", (email,)).one()

    verify_required = settings.REQUIRE_EMAIL_VERIFICATION
    raw_token: Optional[str] = None

    # Always spend the KDF cost regardless of branch so response timing can't
    # reveal whether the email is new, existing-unverified, or existing-verified.
    password_hash = _hash_password(payload.password)

    if existing:
        # Enumeration-safe: do not reveal the account exists. If it's still
        # unverified, refresh its verification token so the email is actionable.
        if verify_required and not getattr(existing, "email_verified", 0):
            raw_token = secrets.token_urlsafe(32)
            s.execute(
                "UPDATE users SET verification_token_hash=%s, verification_expires_at=%s, updated_at=%s WHERE id=%s",
                (_hash_token(raw_token), now + timedelta(hours=settings.EMAIL_VERIFICATION_TTL_HOURS), now, existing.id),
            )
    else:
        user_id = uuid.uuid4()
        email_verified = 0 if verify_required else 1
        if verify_required:
            raw_token = secrets.token_urlsafe(32)
            v_hash = _hash_token(raw_token)
            v_exp = now + timedelta(hours=settings.EMAIL_VERIFICATION_TTL_HOURS)
        else:
            v_hash, v_exp = None, None

        s.execute(
            """
            INSERT INTO users (id, email, full_name, password_hash, auth_provider, created_at, updated_at,
                               email_verified, verification_token_hash, verification_expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, email, payload.full_name.strip(), password_hash, "email", now, now,
             email_verified, v_hash, v_exp),
        )
        profile_json = json.dumps({"email": email, "full_name": payload.full_name.strip()})
        s.execute(
            "INSERT INTO user_data (user_id, profile, session_snapshot, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
            (user_id, profile_json, None, now, now),
        )

    # Dispatch email off the request path so response time doesn't depend on
    # whether a verification email was actually sent.
    if raw_token:
        background.add_task(_dispatch_verification_email, email, raw_token)

    return SimpleMessageResponse(success=True, message=GENERIC_SIGNUP_MESSAGE)


def _dispatch_verification_email(email: str, raw_token: str) -> None:
    verify_url = _frontend_url(f"/auth?mode=verify&token={raw_token}")
    if email_service.is_configured():
        try:
            email_service.send_verification_email(email, verify_url)
        except Exception:
            logger.exception("Failed to send verification email")
    else:
        # Link only (no email/token correlation logged at info level).
        logger.warning("SMTP not configured; verification link generated but not emailed")


@auth_router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: MySQLService = Depends(get_mysql)):
    email = payload.email.lower()
    _enforce_rate_limit(request, "login", _client_ip(request), payload.captcha_token)

    # Per-account lockout — generic response, never reveals whether the email exists.
    if rate_limit_service.is_locked_out(email):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_INVALID_CREDENTIALS
        )

    s = db.get_session()
    user = s.execute("SELECT * FROM users WHERE email=%s", (email,)).one()

    # Always run a KDF verification (dummy hash for unknown users) so timing is
    # constant regardless of whether the account exists.
    stored_hash = getattr(user, "password_hash", "") if user else _dummy_hash()
    password_ok = _verify_password(payload.password, stored_hash or _dummy_hash())

    verified = bool(user) and (
        not settings.REQUIRE_EMAIL_VERIFICATION or bool(getattr(user, "email_verified", 0))
    )

    if not user or not password_ok or not verified:
        # Only count a true credential failure toward lockout.
        if user and password_ok is False:
            rate_limit_service.record_login_failure(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_INVALID_CREDENTIALS
        )

    rate_limit_service.clear_login_failures(email)
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
            # Non-enumerating: same generic 400 used for any invalid email change.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That email address can't be used.",
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
        try:
            _validate_password_strength(payload.new_password)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )
        new_pass = _hash_password(payload.new_password)

    # Building the dynamic UPDATE from a fixed, allow-listed set of columns.
    # Column names are never derived from user input — only these constant,
    # hardcoded SQL fragments are selected — so no untrusted data reaches the
    # query text itself (values are always passed as bound %s parameters).
    _COLUMN_SQL = {
        "email": "email=%s",
        "full_name": "full_name=%s",
        "password_hash": "password_hash=%s",  # nosec B105 - SQL column fragment, not a credential
    }
    updates: dict[str, Any] = {}
    if next_email:
        updates["email"] = next_email
    if new_full_name is not None:
        updates["full_name"] = new_full_name
    if new_pass:
        updates["password_hash"] = new_pass

    set_sql = ["updated_at=%s"] + [_COLUMN_SQL[col] for col in updates]
    values = [now, *updates.values(), user.id]

    # nosec B608 - all fragments come from the fixed _COLUMN_SQL allow-list
    # above (never from request data); every value is still passed as a
    # bound %s parameter, so this is not a SQL-injection sink.
    s.execute(f"UPDATE users SET {', '.join(set_sql)} WHERE id=%s", values)  # nosec B608

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
    token_hash = _hash_token(current["token"])
    s.execute("DELETE FROM sessions WHERE token=%s", (token_hash,))
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
def forgot_password(payload: ForgotPasswordRequest, request: Request, background: BackgroundTasks, db: MySQLService = Depends(get_mysql)):
    email = payload.email.lower()
    _enforce_rate_limit(request, "forgot", _client_ip(request), payload.captcha_token)

    s = db.get_session()
    user = s.execute("SELECT id FROM users WHERE email=%s", (email,)).one()

    raw_token: Optional[str] = None
    now = _utcnow()
    if user:
        raw_token = secrets.token_urlsafe(32)
        s.execute(
            "UPDATE users SET reset_token_hash=%s, reset_token_expires_at=%s, updated_at=%s WHERE id=%s",
            (_hash_token(raw_token), now + timedelta(hours=settings.RESET_TOKEN_TTL_HOURS), now, user.id),
        )

    response = ForgotPasswordResponse(success=True, message=GENERIC_RESET_MESSAGE)

    if raw_token:
        reset_url = _frontend_url(f"/auth?mode=reset&token={raw_token}")
        # Dispatch email off the request path so response time doesn't reveal
        # whether the account exists.
        background.add_task(_dispatch_password_reset, email, reset_url)

        # Never exposed by default — even under DEBUG — unless explicitly opted in.
        if settings.DEBUG and settings.EXPOSE_RESET_TOKEN_IN_DEBUG:
            response.reset_token = raw_token
            response.reset_url = reset_url

    return response


def _dispatch_password_reset(email: str, reset_url: str) -> None:
    if email_service.is_configured():
        try:
            email_service.send_password_reset(email, reset_url)
        except Exception:
            logger.exception("Failed to send password reset email")
    else:
        logger.warning("SMTP not configured; password reset link generated but not emailed")


@auth_router.post("/reset-password", response_model=SimpleMessageResponse)
def reset_password(payload: ResetPasswordRequest, request: Request, db: MySQLService = Depends(get_mysql)):
    _enforce_rate_limit(request, "reset", _client_ip(request), payload.captcha_token)

    s = db.get_session()
    token_hash = _hash_token(payload.token)
    user = s.execute(
        "SELECT id, reset_token_expires_at FROM users WHERE reset_token_hash=%s", (token_hash,)
    ).one()

    if not user or not user.reset_token_expires_at or user.reset_token_expires_at < _utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token is invalid or expired"
        )

    # Consume the token (single-use) and set the new password atomically.
    s.execute(
        "UPDATE users SET password_hash=%s, updated_at=%s, reset_token_hash=null, reset_token_expires_at=null WHERE id=%s",
        (_hash_password(payload.new_password), _utcnow(), user.id),
    )
    # Invalidate all existing sessions after a password reset.
    for sess in s.execute("SELECT token FROM sessions WHERE user_id=%s", (user.id,)):
        s.execute("DELETE FROM sessions WHERE token=%s", (sess.token,))
    return SimpleMessageResponse(success=True, message="Password has been reset")


@auth_router.post("/verify-email", response_model=SimpleMessageResponse)
def verify_email(payload: VerifyEmailRequest, db: MySQLService = Depends(get_mysql)):
    s = db.get_session()
    token_hash = _hash_token(payload.token)
    user = s.execute(
        "SELECT id, verification_expires_at FROM users WHERE verification_token_hash=%s", (token_hash,)
    ).one()

    if not user or not user.verification_expires_at or user.verification_expires_at < _utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification link is invalid or expired"
        )

    s.execute(
        "UPDATE users SET email_verified=1, verification_token_hash=null, verification_expires_at=null, updated_at=%s WHERE id=%s",
        (_utcnow(), user.id),
    )
    return SimpleMessageResponse(success=True, message="Email verified. You can now sign in.")


@auth_router.post("/resend-verification", response_model=SimpleMessageResponse)
def resend_verification(payload: ResendVerificationRequest, request: Request, background: BackgroundTasks, db: MySQLService = Depends(get_mysql)):
    email = payload.email.lower()
    _enforce_rate_limit(request, "resend", _client_ip(request), payload.captcha_token)

    s = db.get_session()
    user = s.execute("SELECT id, email_verified FROM users WHERE email=%s", (email,)).one()
    now = _utcnow()
    if user and not getattr(user, "email_verified", 0):
        raw_token = secrets.token_urlsafe(32)
        s.execute(
            "UPDATE users SET verification_token_hash=%s, verification_expires_at=%s, updated_at=%s WHERE id=%s",
            (_hash_token(raw_token), now + timedelta(hours=settings.EMAIL_VERIFICATION_TTL_HOURS), now, user.id),
        )
        background.add_task(_dispatch_verification_email, email, raw_token)

    # Always generic — never reveals whether the email exists or its state.
    return SimpleMessageResponse(success=True, message=GENERIC_SIGNUP_MESSAGE)


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

    # Build the query with urlencode rather than f-string interpolation: the
    # redirect URI carries "://" and path separators, and hand-pasting it into a
    # query value only happens to work while it contains no "&" or "?".
    if provider == "google":
        query = urlencode({
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": "openid email profile",
            "state": state,
        })
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
    else:  # github
        query = urlencode({
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": "user:email",
            "state": state,
        })
        auth_url = f"https://github.com/login/oauth/authorize?{query}"

    response = RedirectResponse(auth_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        max_age=600,
        samesite="lax",
        secure=_should_use_secure_cookie(),
        path="/auth/oauth",
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
                    logger.warning(f"Google token exchange error: {token_data.get('error_description', token_data.get('error'))}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="OAuth token exchange failed. Please try again."
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
                    logger.warning(f"GitHub token exchange error: {token_data.get('error_description', token_data.get('error'))}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="OAuth token exchange failed. Please try again."
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
            logger.error(f"OAuth authentication error for {provider}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth authentication failed. Please try again."
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
            INSERT INTO users (id, email, full_name, password_hash, auth_provider, created_at, updated_at, email_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, email, full_name, _hash_password(secrets.token_hex(16)), provider, now, now, 1)
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
    response.delete_cookie("oauth_state", samesite="lax", secure=_should_use_secure_cookie(), path="/auth/oauth")
    return response


@auth_router.post("/oauth/{provider}")
def oauth_post_fallback(provider: str):
    return {"url": f"{settings.BACKEND_BASE_URL.rstrip('/')}/auth/oauth/{provider}"}
