"""
Security regression tests for the auth password-strength policy.

Signup and reset-password must reject passwords that are shorter than the
minimum length or that lack an uppercase letter, lowercase letter, number, or
special character. These are Pydantic validation failures that fire before any
DB access, so no database is required.
"""

import pytest

from app.api.auth_routes import (
    SignUpRequest,
    ResetPasswordRequest,
    MIN_PASSWORD_LENGTH,
    _validate_password_strength,
)

VALID = "Str0ng!pw"  # >=8, upper, lower, digit, special


class TestPasswordStrengthValidator:
    @pytest.mark.parametrize(
        "bad",
        [
            "Sh0rt!",          # too short
            "alllower1!",      # no uppercase
            "ALLUPPER1!",      # no lowercase
            "NoDigits!!",      # no number
            "NoSpecial1",      # no special character
            "",                # empty
        ],
    )
    def test_rejects_weak(self, bad):
        with pytest.raises(ValueError):
            _validate_password_strength(bad)

    def test_accepts_valid(self):
        assert _validate_password_strength(VALID) == VALID

    def test_boundary_length(self):
        # Exactly MIN_PASSWORD_LENGTH with all classes present is accepted.
        pw = "Aa1!" + "a" * (MIN_PASSWORD_LENGTH - 4)
        assert len(pw) == MIN_PASSWORD_LENGTH
        assert _validate_password_strength(pw) == pw


class TestSignUpPasswordPolicy:
    @pytest.mark.parametrize("bad", ["short7", "nouppercase1!", "NoSpecial1", "NoDigit!!"])
    def test_weak_password_rejected(self, bad):
        with pytest.raises(ValueError):
            SignUpRequest(email="user@example.com", password=bad, full_name="A User")

    def test_valid_password_accepted(self):
        req = SignUpRequest(email="user@example.com", password=VALID, full_name="A User")
        assert req.password == VALID


class TestResetPasswordPolicy:
    @pytest.mark.parametrize("bad", ["short7", "nouppercase1!", "NoSpecial1", "NoDigit!!"])
    def test_weak_password_rejected(self, bad):
        with pytest.raises(ValueError):
            ResetPasswordRequest(token="t", new_password=bad)

    def test_valid_password_accepted(self):
        req = ResetPasswordRequest(token="t", new_password=VALID)
        assert req.new_password == VALID
