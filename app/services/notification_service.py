"""Unified notifications: in-app inbox + templated email with delivery tracking.

``notify()`` is the single entry point every feature uses. It:
  1. writes an in-app notification row (unless the user disabled in-app),
  2. queues an email delivery row (unless disabled / quiet hours), and
  3. lets ``process_pending()`` — run by the scheduler loop — send emails with
     exponential-backoff retries so SMTP hiccups never lose a message.
"""
from __future__ import annotations

import html
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.services import email_service

MAX_ATTEMPTS = 5
BACKOFF_SECONDS = [60, 300, 900, 3600, 10800]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Templates ────────────────────────────────────────────────────────────────
# Each template returns (subject, text, html). Keep copy short; the inbox
# shows title/body, email adds a CTA button.
def _cta(url: str, label: str) -> str:
    return (
        f'<p style="margin:24px 0"><a href="{html.escape(url)}" '
        f'style="background:#0f766e;color:#ffffff;padding:12px 20px;border-radius:8px;'
        f'text-decoration:none;font-weight:600;display:inline-block">{html.escape(label)}</a></p>'
    )


def _wrap(title: str, body_html: str) -> str:
    return (
        '<div style="font-family:Inter,Segoe UI,Arial,sans-serif;max-width:560px;margin:0 auto;'
        'padding:32px 24px;color:#0f172a;line-height:1.55">'
        f'<h2 style="margin:0 0 12px;font-size:20px">{html.escape(title)}</h2>{body_html}'
        '<p style="color:#64748b;font-size:12px;margin-top:32px">You are receiving this because notifications '
        'are enabled in your AI Interview settings. Manage preferences in the app.</p></div>'
    )


def render_email(n_type: str, title: str, body: str, action_url: Optional[str], data: Dict[str, Any]) -> tuple[str, str, str]:
    subject = title
    text = body or title
    parts = [f"<p>{html.escape(body)}</p>"] if body else []

    if n_type == "session_reminder":
        subject = f"Reminder: {title}"
        when = data.get("starts_at_human")
        if when:
            parts.append(f"<p><strong>When:</strong> {html.escape(str(when))}</p>")
        if action_url:
            parts.append(_cta(action_url, "Open session"))
    elif n_type == "streak_nudge":
        subject = title
        if action_url:
            parts.append(_cta(action_url, "Practice now"))
    elif n_type == "weekly_digest":
        subject = f"Your week in review — {title}"
        stats = data.get("stats") or {}
        rows = "".join(
            f"<tr><td style='padding:6px 12px 6px 0;color:#475569'>{html.escape(str(k))}</td>"
            f"<td style='padding:6px 0;font-weight:600'>{html.escape(str(v))}</td></tr>"
            for k, v in stats.items()
        )
        if rows:
            parts.append(f"<table style='border-collapse:collapse;margin:12px 0'>{rows}</table>")
        if action_url:
            parts.append(_cta(action_url, "View analytics"))
    elif n_type == "interview_complete":
        subject = f"Results ready: {title}"
        score = data.get("score")
        if score is not None:
            parts.append(f"<p><strong>Score:</strong> {html.escape(str(score))}/100</p>")
        if action_url:
            parts.append(_cta(action_url, "See feedback"))
    elif action_url:
        parts.append(_cta(action_url, "Open"))

    if action_url:
        text += f"\n\n{action_url}"
    return subject, text, _wrap(title, "".join(parts))


# ── Service ──────────────────────────────────────────────────────────────────
class NotificationService:
    def __init__(self, db):
        self.db = db

    # preferences
    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        s = self.db.get_session()
        row = s.execute("SELECT * FROM notification_preferences WHERE user_id=%s", (str(user_id),)).one()
        if not row:
            return {
                "email_enabled": True,
                "in_app_enabled": True,
                "reminders_enabled": True,
                "weekly_digest_enabled": True,
                "quiet_hours_start": None,
                "quiet_hours_end": None,
                "timezone": "UTC",
            }
        return {
            "email_enabled": bool(row["email_enabled"]),
            "in_app_enabled": bool(row["in_app_enabled"]),
            "reminders_enabled": bool(row["reminders_enabled"]),
            "weekly_digest_enabled": bool(row["weekly_digest_enabled"]),
            "quiet_hours_start": row["quiet_hours_start"],
            "quiet_hours_end": row["quiet_hours_end"],
            "timezone": row["timezone"] or "UTC",
        }

    def update_preferences(self, user_id: str, prefs: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_preferences(user_id)
        current.update({k: v for k, v in prefs.items() if k in current})
        s = self.db.get_session()
        now = _utcnow()
        exists = s.execute("SELECT user_id FROM notification_preferences WHERE user_id=%s", (str(user_id),)).one()
        values = (
            int(current["email_enabled"]),
            int(current["in_app_enabled"]),
            int(current["reminders_enabled"]),
            int(current["weekly_digest_enabled"]),
            current["quiet_hours_start"],
            current["quiet_hours_end"],
            current["timezone"],
            now,
        )
        if exists:
            s.execute(
                """UPDATE notification_preferences SET email_enabled=%s, in_app_enabled=%s, reminders_enabled=%s,
                   weekly_digest_enabled=%s, quiet_hours_start=%s, quiet_hours_end=%s, timezone=%s, updated_at=%s
                   WHERE user_id=%s""",
                (*values, str(user_id)),
            )
        else:
            s.execute(
                """INSERT INTO notification_preferences (email_enabled, in_app_enabled, reminders_enabled,
                   weekly_digest_enabled, quiet_hours_start, quiet_hours_end, timezone, updated_at, user_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (*values, str(user_id)),
            )
        return current

    def _in_quiet_hours(self, prefs: Dict[str, Any]) -> bool:
        start, end = prefs.get("quiet_hours_start"), prefs.get("quiet_hours_end")
        if start is None or end is None:
            return False
        try:
            from zoneinfo import ZoneInfo

            hour = datetime.now(ZoneInfo(prefs.get("timezone") or "UTC")).hour
        except Exception:
            hour = datetime.now(timezone.utc).hour
        if start <= end:
            return start <= hour < end
        return hour >= start or hour < end  # overnight window

    # create
    def notify(
        self,
        user_id: str,
        n_type: str,
        title: str,
        body: str = "",
        *,
        action_url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None,
        email_to: Optional[str] = None,
    ) -> Optional[str]:
        prefs = self.get_preferences(user_id)
        channels = channels or ["in_app", "email"]
        if n_type in {"session_reminder", "streak_nudge"} and not prefs["reminders_enabled"]:
            return None
        if n_type == "weekly_digest" and not prefs["weekly_digest_enabled"]:
            return None

        s = self.db.get_session()
        now = _utcnow()
        nid = str(uuid.uuid4())
        data = data or {}

        if "in_app" in channels and prefs["in_app_enabled"]:
            s.execute(
                """INSERT INTO notifications (id, user_id, type, title, body, action_url, data_json, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (nid, str(user_id), n_type, title[:300], (body or "")[:2000], action_url, json.dumps(data), now),
            )
        else:
            # Still create the row (unread=false) so email deliveries have a parent.
            s.execute(
                """INSERT INTO notifications (id, user_id, type, title, body, action_url, data_json, read_at, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (nid, str(user_id), n_type, title[:300], (body or "")[:2000], action_url, json.dumps(data), now, now),
            )

        if "email" in channels and prefs["email_enabled"]:
            recipient = email_to or self._user_email(user_id)
            if recipient:
                delay = 0
                if self._in_quiet_hours(prefs):
                    delay = 3600  # push past quiet window in hourly steps; re-checked on send
                s.execute(
                    """INSERT INTO notification_deliveries (id, notification_id, channel, status, attempts, next_attempt_at, created_at)
                       VALUES (%s, %s, 'email', 'pending', 0, %s, %s)""",
                    (str(uuid.uuid4()), nid, now + timedelta(seconds=delay), now),
                )
        return nid

    def _user_email(self, user_id: str) -> Optional[str]:
        row = self.db.get_session().execute("SELECT email FROM users WHERE id=%s", (str(user_id),)).one()
        return (row or {}).get("email") if row else None

    # inbox
    def list(self, user_id: str, *, limit: int = 30, unread_only: bool = False) -> Dict[str, Any]:
        s = self.db.get_session()
        limit = max(1, min(limit, 100))
        where = "user_id=%s" + (" AND read_at IS NULL" if unread_only else "")
        rows = s.execute(
            f"SELECT id, type, title, body, action_url, data_json, read_at, created_at FROM notifications WHERE {where} "  # nosec B608
            f"ORDER BY created_at DESC LIMIT {limit}",
            (str(user_id),),
        ).all()
        unread = s.execute(
            "SELECT COUNT(*) AS c FROM notifications WHERE user_id=%s AND read_at IS NULL", (str(user_id),)
        ).one()
        items = []
        for r in rows:
            try:
                data = json.loads(r["data_json"] or "{}")
            except Exception:
                data = {}
            items.append(
                {
                    "id": r["id"],
                    "type": r["type"],
                    "title": r["title"],
                    "body": r["body"],
                    "action_url": r["action_url"],
                    "data": data,
                    "read": r["read_at"] is not None,
                    "created_at": r["created_at"],
                }
            )
        return {"items": items, "unread_count": int((unread or {}).get("c") or 0)}

    def mark_read(self, user_id: str, ids: Optional[List[str]] = None) -> int:
        s = self.db.get_session()
        now = _utcnow()
        if ids:
            count = 0
            for nid in ids[:200]:
                res = s.execute(
                    "UPDATE notifications SET read_at=%s WHERE id=%s AND user_id=%s AND read_at IS NULL",
                    (now, nid, str(user_id)),
                )
                count += getattr(res, "rowcount", 0) or 0
            return count
        res = s.execute(
            "UPDATE notifications SET read_at=%s WHERE user_id=%s AND read_at IS NULL", (now, str(user_id))
        )
        return getattr(res, "rowcount", 0) or 0

    def delete(self, user_id: str, nid: str) -> bool:
        s = self.db.get_session()
        res = s.execute("DELETE FROM notifications WHERE id=%s AND user_id=%s", (nid, str(user_id)))
        return bool(getattr(res, "rowcount", 0))

    # delivery worker
    def process_pending(self, batch: int = 25) -> Dict[str, int]:
        """Send due email deliveries. Safe to call frequently; idempotent per row."""
        s = self.db.get_session()
        now = _utcnow()
        rows = s.execute(
            "SELECT d.id, d.notification_id, d.attempts, n.user_id, n.type, n.title, n.body, n.action_url, n.data_json "
            "FROM notification_deliveries d JOIN notifications n ON n.id = d.notification_id "
            f"WHERE d.status='pending' AND (d.next_attempt_at IS NULL OR d.next_attempt_at <= %s) LIMIT {int(batch)}",  # nosec B608
            (now,),
        ).all()
        sent = failed = deferred = 0
        for r in rows:
            prefs = self.get_preferences(r["user_id"])
            if self._in_quiet_hours(prefs):
                s.execute(
                    "UPDATE notification_deliveries SET next_attempt_at=%s WHERE id=%s",
                    (now + timedelta(hours=1), r["id"]),
                )
                deferred += 1
                continue
            recipient = self._user_email(r["user_id"])
            if not recipient or not email_service.is_configured():
                s.execute(
                    "UPDATE notification_deliveries SET status='skipped', last_error=%s, sent_at=%s WHERE id=%s",
                    ("no recipient" if not recipient else "smtp not configured", now, r["id"]),
                )
                continue
            try:
                data = json.loads(r["data_json"] or "{}")
            except Exception:
                data = {}
            subject, text, html_body = render_email(r["type"], r["title"], r["body"] or "", r["action_url"], data)
            try:
                email_service.send_email(recipient, subject, text, html_body)
                s.execute(
                    "UPDATE notification_deliveries SET status='sent', attempts=attempts+1, sent_at=%s WHERE id=%s",
                    (now, r["id"]),
                )
                sent += 1
            except Exception as exc:
                attempts = int(r["attempts"] or 0) + 1
                if attempts >= MAX_ATTEMPTS:
                    s.execute(
                        "UPDATE notification_deliveries SET status='failed', attempts=%s, last_error=%s WHERE id=%s",
                        (attempts, str(exc)[:1000], r["id"]),
                    )
                    failed += 1
                else:
                    backoff = BACKOFF_SECONDS[min(attempts - 1, len(BACKOFF_SECONDS) - 1)]
                    s.execute(
                        "UPDATE notification_deliveries SET attempts=%s, last_error=%s, next_attempt_at=%s WHERE id=%s",
                        (attempts, str(exc)[:1000], now + timedelta(seconds=backoff), r["id"]),
                    )
                    deferred += 1
                logger.warning(f"notification email failed (attempt {attempts}): {exc}")
        return {"sent": sent, "failed": failed, "deferred": deferred}


def app_url(path: str) -> str:
    base = settings.FRONTEND_BASE_URL.rstrip("/")
    base_path = getattr(settings, "FRONTEND_BASE_PATH", "").strip("/")
    if base_path and not base.endswith(f"/{base_path}"):
        base = f"{base}/{base_path}"
    return f"{base}{path}"
