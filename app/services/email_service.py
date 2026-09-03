"""
Email service — sends transactional email over SMTP.

Reads SMTP credentials from settings (env). If SMTP is not configured, the
service is considered unavailable and callers can fall back accordingly.
"""

from __future__ import annotations

import html as html_mod
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    """True when the minimum SMTP settings are present."""
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def _from_address() -> str:
    email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER or ""
    name = settings.SMTP_FROM_NAME
    return f"{name} <{email}>" if name else email


def send_email(to_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
    """Send an email. Raises on failure so the caller can decide how to react."""
    if not is_configured():
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = _from_address()
    message["To"] = to_email
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    host = settings.SMTP_HOST
    port = settings.SMTP_PORT

    if settings.SMTP_USE_TLS:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls(context=context)
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
    else:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context, timeout=15) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)

    logger.info("Sent email to %s (subject=%r)", to_email, subject)


def send_password_reset(to_email: str, reset_url: str) -> None:
    """Send the password-reset email containing the reset link."""
    subject = "Reset your AI Interview password"
    text_body = (
        "We received a request to reset your password.\n\n"
        f"Use the link below to choose a new password (valid for 1 hour):\n{reset_url}\n\n"
        "If you didn't request this, you can safely ignore this email."
    )
    html_body = f"""\
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:480px;margin:auto;padding:24px">
  <h2 style="margin:0 0 12px">Reset your password</h2>
  <p style="color:#555;line-height:1.6">We received a request to reset your password. This link is valid for 1 hour.</p>
  <p style="margin:24px 0">
    <a href="{html_mod.escape(reset_url)}" style="background:#6d5efc;color:#fff;text-decoration:none;padding:12px 22px;border-radius:10px;font-weight:600;display:inline-block">Choose a new password</a>
  </p>
  <p style="color:#888;font-size:13px;line-height:1.6">If the button doesn't work, copy this link:<br>{html_mod.escape(reset_url)}</p>
  <p style="color:#aaa;font-size:12px;margin-top:24px">If you didn't request this, you can safely ignore this email.</p>
</div>"""
    send_email(to_email, subject, text_body, html_body)


def send_verification_email(to_email: str, verify_url: str) -> None:
    """Send the account verification email containing the confirmation link."""
    subject = "Confirm your AI Interview email"
    text_body = (
        "Welcome to AI Interview!\n\n"
        f"Confirm your email address to activate your account (link valid for 24 hours):\n{verify_url}\n\n"
        "If you didn't create an account, you can safely ignore this email."
    )
    html_body = f"""\
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:480px;margin:auto;padding:24px">
  <h2 style="margin:0 0 12px">Confirm your email</h2>
  <p style="color:#555;line-height:1.6">Confirm your email address to activate your account. This link is valid for 24 hours.</p>
  <p style="margin:24px 0">
    <a href="{html_mod.escape(verify_url)}" style="background:#6d5efc;color:#fff;text-decoration:none;padding:12px 22px;border-radius:10px;font-weight:600;display:inline-block">Confirm email</a>
  </p>
  <p style="color:#888;font-size:13px;line-height:1.6">If the button doesn't work, copy this link:<br>{html_mod.escape(verify_url)}</p>
  <p style="color:#aaa;font-size:12px;margin-top:24px">If you didn't create an account, you can safely ignore this email.</p>
</div>"""
    send_email(to_email, subject, text_body, html_body)
