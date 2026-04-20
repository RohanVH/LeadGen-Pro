"""Interactive AI assistant for per-lead analysis and follow-up chat."""

from __future__ import annotations

import json
import logging

import httpx
from app.core.config import Settings
from app.schemas.lead_ai import (
    LeadAnalyzeRequest,
    LeadAnalyzeResponse,
    LeadChatRequest,
    LeadChatResponse,
)

logger = logging.getLogger(__name__)


class LeadAIAssistantService:
    """Generate sales intelligence and answer lead-specific follow-up questions."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def analyze(self, payload: LeadAnalyzeRequest) -> LeadAnalyzeResponse:
        """Generate a structured analysis for a lead."""
        if not self._settings.openai_api_key:
            return self._fallback_analysis(payload.business_type)

        try:
            async with httpx.AsyncClient(timeout=25) as client:
                response = await client.post(
                    f"{self._settings.openai_base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._settings.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=self._analyze_prompt(payload),
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                data = json.loads(content)
                return LeadAnalyzeResponse(
                    overview=str(data.get("overview") or ""),
                    strengths=[str(item) for item in (data.get("strengths") or [])][:4],
                    weaknesses=[str(item) for item in (data.get("weaknesses") or [])][:4],
                    customer_perception=str(data.get("customer_perception") or "neutral"),
                    opportunities=[str(item) for item in (data.get("opportunities") or [])][:4],
                    what_to_sell=str(data.get("what_to_sell") or ""),
                    outreach_angle=str(data.get("outreach_angle") or ""),
                )
        except Exception as exc:
            logger.warning("Lead AI analyze failed, using fallback.", exc_info=exc)
            return self._fallback_analysis(payload.business_type)

    async def chat(self, payload: LeadChatRequest) -> LeadChatResponse:
        """Continue a contextual conversation for a specific lead."""
        if not self._settings.openai_api_key:
            return LeadChatResponse(
                response=self._fallback_chat(payload.message, payload.lead_context.business_type),
            )

        history = [{"role": msg.role, "content": msg.content} for msg in payload.previous_conversation[-10:]]
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a practical SaaS sales assistant. Be concise, tactical, and specific. "
                    "Always aim to help close this lead."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Lead: {payload.lead_context.name}\n"
                    f"Type: {payload.lead_context.business_type}\n"
                    f"Rating: {payload.lead_context.rating if payload.lead_context.rating is not None else 'unknown'}\n"
                    f"Reviews: {' | '.join(payload.lead_context.reviews[:4]) if payload.lead_context.reviews else 'none'}\n"
                    f"Website notes: {payload.lead_context.website_content or 'none'}\n"
                    f"Current overview: {payload.lead_context.overview or 'none'}\n"
                    f"Recommended offer: {payload.lead_context.what_to_sell or 'unknown'}"
                ),
            },
            *history,
            {"role": "user", "content": payload.message},
        ]
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                response = await client.post(
                    f"{self._settings.openai_base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._settings.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._settings.openai_model,
                        "messages": messages,
                    },
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return LeadChatResponse(response=str(content).strip())
        except Exception as exc:
            logger.warning("Lead AI chat failed, using fallback.", exc_info=exc)
            return LeadChatResponse(
                response=self._fallback_chat(payload.message, payload.lead_context.business_type),
            )

    def _analyze_prompt(self, payload: LeadAnalyzeRequest) -> dict:
        return {
            "model": self._settings.openai_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a sales consultant for agencies. Return only JSON with actionable output."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze this business for client acquisition.\n\n"
                        f"Business name: {payload.name}\n"
                        f"Type: {payload.business_type}\n"
                        f"Website content: {payload.website_content or 'not available'}\n"
                        f"Rating: {payload.rating if payload.rating is not None else 'not available'}\n"
                        f"Reviews: {' | '.join(payload.reviews[:4]) if payload.reviews else 'not available'}\n\n"
                        "Return JSON with keys:\n"
                        "{"
                        '"overview":"...",'
                        '"strengths":["..."],'
                        '"weaknesses":["..."],'
                        '"customer_perception":"...",'
                        '"opportunities":["..."],'
                        '"what_to_sell":"website/app/automation recommendation",'
                        '"outreach_angle":"first message angle"'
                        "}"
                    ),
                },
            ],
        }

    def _fallback_analysis(self, business_type: str) -> LeadAnalyzeResponse:
        type_label = business_type or "local business"
        return LeadAnalyzeResponse(
            overview=f"{type_label} appears to have room for stronger digital acquisition and conversion flows.",
            strengths=["Existing market presence", "Clear core service offering"],
            weaknesses=["Inconsistent online positioning", "Likely weak lead capture journey"],
            customer_perception="mixed but recoverable with better digital experience",
            opportunities=[
                "Improve trust with modern web presentation",
                "Add conversion-focused funnels and automation follow-up",
            ],
            what_to_sell="Website revamp with lead capture automation",
            outreach_angle=(
                f"Offer a quick teardown for this {type_label} showing 2-3 conversion fixes that can increase inquiries."
            ),
        )

    def _fallback_chat(self, message: str, business_type: str) -> str:
        return (
            f"For this {business_type or 'business'}, position the pitch around revenue impact. "
            "Lead with one visible problem, one quick win, and a low-friction next step (10-minute audit call). "
            f"Question asked: {message}"
        )
