"""Schemas for outreach actions."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}$")


class SendEmailRequest(BaseModel):
    """Request payload for sending an outreach email."""

    email: str = Field(min_length=5, max_length=255)
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=10, max_length=5000)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Ensure recipient email is valid before SMTP submission."""
        normalized = value.strip()
        if not EMAIL_REGEX.match(normalized):
            raise ValueError("Invalid email address.")
        return normalized


class SendEmailResponse(BaseModel):
    """Response payload for outreach email submission."""

    status: str
    recipient: str
