"""Security regression tests for the auth flow.

Covers user-enumeration resistance, hashed single-use reset tokens, the
email-verification gate, and constant-response login. These run against the
app's SQLite fallback DB via TestClient (no external MySQL required).
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import auth_routes
from app.services.mysql_service import get_mysql


def _email() -> str:
    return f"sec_{uuid.uuid4().hex}@example.com"


VALID_PW = "Str0ng!pw1"


@pytest.fixture
def client():
    with TestClient(app, base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def _require_verification(monkeypatch):
    # Default the app to the secure posture for these tests.
    from app.core.config import settings
    monkeypatch.setattr(settings, "REQUIRE_EMAIL_VERIFICATION", True)
    yield


def _signup(client, email, pw=VALID_PW):
    return client.post("/auth/signup", json={"email": email, "password": pw, "full_name": "Sec User"})


class TestEnumerationResistance:
    def test_signup_identical_for_new_and_existing_email(self, client):
        email = _email()
        first = _signup(client, email)
        second = _signup(client, email)
        assert first.status_code == second.status_code == 202
        assert first.json() == second.json()
        # No token / user leaked.
        assert "access_token" not in first.json()
        assert "user" not in first.json()

    def test_login_unknown_vs_wrong_password_identical(self, client):
        email = _email()
        _signup(client, email)
        # verify the account so the failure is purely wrong-password
        _verify(client, email)

        unknown = client.post("/auth/login", json={"email": _email(), "password": VALID_PW})
        wrong = client.post("/auth/login", json={"email": email, "password": "Wr0ng!pass9"})
        assert unknown.status_code == wrong.status_code == 401
        assert unknown.json()["detail"] == wrong.json()["detail"] == "Invalid email or password"

    def test_forgot_password_generic_for_unknown(self, client):
        known = _email()
        _signup(client, known)
        r_known = client.post("/auth/forgot-password", json={"email": known})
        r_unknown = client.post("/auth/forgot-password", json={"email": _email()})
        assert r_known.json()["message"] == r_unknown.json()["message"]
        # No token exposed by default.
        assert r_known.json().get("reset_token") is None
        assert r_known.json().get("reset_url") is None


def _db_user(email):
    s = get_mysql().get_session()
    return s.execute("SELECT * FROM users WHERE email=%s", (email.lower(),)).one()


def _verify(client, email):
    """Fetch the stored verification hash's plaintext isn't available, so flip
    the flag directly for tests that need a usable account."""
    s = get_mysql().get_session()
    s.execute("UPDATE users SET email_verified=1 WHERE email=%s", (email.lower(),))


class TestResetTokenSecurity:
    def test_reset_token_stored_hashed(self, client, monkeypatch):
        from app.core.config import settings
        # Even with DEBUG exposure on, the raw token must never equal what's stored.
        monkeypatch.setattr(settings, "DEBUG", True)
        monkeypatch.setattr(settings, "EXPOSE_RESET_TOKEN_IN_DEBUG", True)

        email = _email()
        _signup(client, email)
        r = client.post("/auth/forgot-password", json={"email": email})
        raw = r.json().get("reset_token")
        assert raw is not None
        row = _db_user(email)
        assert row.reset_token_hash is not None
        assert row.reset_token_hash != raw
        assert row.reset_token_hash == auth_routes._hash_token(raw)

    def test_reset_token_single_use_and_expiry(self, client, monkeypatch):
        from app.core.config import settings
        monkeypatch.setattr(settings, "DEBUG", True)
        monkeypatch.setattr(settings, "EXPOSE_RESET_TOKEN_IN_DEBUG", True)

        email = _email()
        _signup(client, email)
        raw = client.post("/auth/forgot-password", json={"email": email}).json()["reset_token"]

        first = client.post("/auth/reset-password", json={"token": raw, "new_password": "N3w!pass99"})
        assert first.status_code == 200
        # Second use of the same token must fail (single-use).
        second = client.post("/auth/reset-password", json={"token": raw, "new_password": "N3w!pass98"})
        assert second.status_code == 400

    def test_invalid_reset_token_rejected(self, client):
        r = client.post("/auth/reset-password", json={"token": "not-a-real-token", "new_password": VALID_PW})
        assert r.status_code == 400


class TestVerificationGate:
    def test_unverified_login_blocked(self, client):
        email = _email()
        _signup(client, email)
        r = client.post("/auth/login", json={"email": email, "password": VALID_PW})
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid email or password"

    def test_verified_login_succeeds(self, client):
        email = _email()
        _signup(client, email)
        _verify(client, email)
        r = client.post("/auth/login", json={"email": email, "password": VALID_PW})
        assert r.status_code == 200
        assert r.json()["access_token"]


class TestClerkSessionExchange:
    def test_verified_clerk_session_creates_backend_session(self, client, monkeypatch):
        email = _email()
        subject = f"user_test_{uuid.uuid4().hex}"
        monkeypatch.setattr(auth_routes, "_clerk_subject", lambda _: subject)

        exchanged = client.post(
            "/auth/clerk/session",
            headers={"Authorization": "Bearer clerk-session-token"},
            json={"email": email, "full_name": "Clerk User"},
        )

        assert exchanged.status_code == 200
        token = exchanged.json()["access_token"]
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["user"]["email"] == email
