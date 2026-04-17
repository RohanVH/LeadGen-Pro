"""Outreach automation API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_email_sender_service
from app.schemas.outreach import SendEmailRequest, SendEmailResponse
from app.services.email_sender import EmailSenderService

router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.post("/send-email", response_model=SendEmailResponse)
async def send_outreach_email(
    payload: SendEmailRequest,
    email_sender: EmailSenderService = Depends(get_email_sender_service),
) -> SendEmailResponse:
    """Send a single outreach email to a lead."""
    await email_sender.send_email(
        to_email=payload.email,
        subject=payload.subject,
        message=payload.message,
    )
    return SendEmailResponse(status="sent", recipient=payload.email)
