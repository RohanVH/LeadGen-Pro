"""Interactive lead AI assistant endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_lead_ai_assistant_service
from app.schemas.lead_ai import (
    LeadAnalyzeRequest,
    LeadAnalyzeResponse,
    LeadChatRequest,
    LeadChatResponse,
)
from app.services.lead_ai_assistant import LeadAIAssistantService

router = APIRouter(prefix="/v1/lead", tags=["lead-ai"])


@router.post("/analyze", response_model=LeadAnalyzeResponse)
async def analyze_lead(
    payload: LeadAnalyzeRequest,
    assistant: LeadAIAssistantService = Depends(get_lead_ai_assistant_service),
) -> LeadAnalyzeResponse:
    """Run AI analysis for a single lead on demand."""
    return await assistant.analyze(payload)


@router.post("/chat", response_model=LeadChatResponse)
async def chat_with_lead_assistant(
    payload: LeadChatRequest,
    assistant: LeadAIAssistantService = Depends(get_lead_ai_assistant_service),
) -> LeadChatResponse:
    """Chat with AI assistant using lead context and prior conversation."""
    return await assistant.chat(payload)
