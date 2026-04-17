"""SMTP-backed email delivery service."""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from fastapi import HTTPException, status

from app.core.config import Settings

logger = logging.getLogger(__name__)


class EmailSenderService:
    """Send outbound outreach emails through configured SMTP credentials."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_email(self, to_email: str, subject: str, message: str) -> None:
        """Deliver an email asynchronously by offloading SMTP I/O."""
        self._ensure_configured()
        await asyncio.to_thread(self._send_email_sync, to_email, subject, message)

    def _send_email_sync(self, to_email: str, subject: str, message: str) -> None:
        email_message = EmailMessage()
        email_message["From"] = self._settings.email_user
        email_message["To"] = to_email
        email_message["Subject"] = subject
        email_message.set_content(message)

        try:
            with smtplib.SMTP(self._settings.email_host, self._settings.email_port, timeout=20) as server:
                server.starttls()
                server.login(self._settings.email_user, self._settings.email_pass)
                server.send_message(email_message)
        except smtplib.SMTPException as exc:
            logger.exception("SMTP delivery failed for recipient '%s'.", to_email, exc_info=exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to send outreach email.",
            ) from exc
        except OSError as exc:
            logger.exception("SMTP server connection failed for recipient '%s'.", to_email, exc_info=exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach the configured email server.",
            ) from exc

    def _ensure_configured(self) -> None:
        if not all(
            [
                self._settings.email_host,
                self._settings.email_port,
                self._settings.email_user,
                self._settings.email_pass,
            ]
        ):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email SMTP settings are not configured.",
            )
