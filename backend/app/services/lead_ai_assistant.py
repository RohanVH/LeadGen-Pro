"""Interactive AI assistant for per-lead analysis and follow-up chat."""

from __future__ import annotations
import logging

import httpx
from app.core.config import Settings
from app.schemas.lead_ai import (
    LeadAnalyzeRequest,
    LeadAnalyzeResponse,
    LeadChatRequest,
    LeadChatResponse,
)
from app.services.ai_router import AIRouterService

logger = logging.getLogger(__name__)


class LeadAIAssistantService:
    """Generate sales intelligence and answer lead-specific follow-up questions."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._ai_router = AIRouterService(settings=settings)

    async def analyze(self, payload: LeadAnalyzeRequest) -> LeadAnalyzeResponse:
        """Generate a structured analysis for a lead."""
        logger.info("Lead analyze request payload: %s", payload.model_dump(by_alias=True))
        lead_input = {
            "name": payload.name,
            "business_type": payload.business_type,
            "website_content": payload.website_content,
            "rating": payload.rating,
            "review_count": len(payload.reviews),
            "google_reviews": payload.reviews,
        }
        try:
            normalized = await self._ai_router.analyze_business(lead_input)
        except Exception:
            logger.exception("Lead analyze failed; using rule-based fallback.")
            normalized = self._ai_router.normalized_rule_based_fallback(lead_input)
        logger.info("Lead analyze normalized AI response: %s", normalized)
        return LeadAnalyzeResponse(
            overview=str(normalized.get("summary") or ""),
            strengths=[str(item) for item in (normalized.get("pros") or [])][:4],
            weaknesses=[str(item) for item in (normalized.get("cons") or [])][:4],
            customer_perception=str(normalized.get("sentiment") or "neutral"),
            opportunities=[
                f"Prioritize outreach because action is '{normalized.get('action', 'contact')}'.",
                f"Lead with this offer: {normalized.get('pitch', 'digital growth package')}.",
            ],
            what_to_sell=str(normalized.get("pitch") or "digital growth package"),
            outreach_angle=(
                f"Reference '{normalized.get('summary', 'their business context')}' and propose "
                f"{normalized.get('pitch', 'a focused conversion upgrade')} in a short audit call."
            ),
        )

    async def chat(self, payload: LeadChatRequest) -> LeadChatResponse:
        """Continue a contextual conversation for a specific lead."""
        context = payload.lead_context or payload.lead
        if context is None:
            return LeadChatResponse(response="Please provide lead context so I can give a targeted answer.")

        history_source = payload.messages or payload.previous_conversation
        history = [{"role": msg.role, "content": msg.content} for msg in history_source[-12:]]
        user_message = (payload.message or "").strip()
        if not user_message:
            # If caller sends full messages array, use the last user message as active prompt.
            for item in reversed(history):
                if item["role"] == "user":
                    user_message = item["content"]
                    break
        if not user_message:
            return LeadChatResponse(response="Ask a question and I will generate a lead-specific response.")

        logger.info(
            "Lead chat request payload: %s",
            payload.model_dump(by_alias=True),
        )
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
                    f"Lead: {context.name}\n"
                    f"Type: {context.business_type}\n"
                    f"Rating: {context.rating if context.rating is not None else 'unknown'}\n"
                    f"Reviews: {' | '.join(context.reviews[:4]) if context.reviews else 'none'}\n"
                    f"Website notes: {context.website_content or 'none'}\n"
                    f"Current overview: {context.overview or 'none'}\n"
                    f"Recommended offer: {context.what_to_sell or 'unknown'}"
                ),
            },
            *history,
            {"role": "user", "content": user_message},
        ]
        openai_answer = await self._chat_openai(messages)
        if openai_answer:
            print("Using OpenAI")
            logger.info("Lead chat response from OpenAI: %s", openai_answer)
            return LeadChatResponse(response=openai_answer)

        gemini_answer = await self._chat_gemini(messages)
        if gemini_answer:
            print("Using Gemini")
            logger.info("Lead chat response from Gemini: %s", gemini_answer)
            return LeadChatResponse(response=gemini_answer)

        print("Using fallback")
        logger.warning("Lead chat fallback triggered after provider failures.")
        return LeadChatResponse(response=self._dynamic_chat_fallback(user_message, context.model_dump()))

    async def _chat_openai(self, messages: list[dict]) -> str | None:
        if not self._settings.openai_api_key:
            logger.warning("OpenAI chat skipped: missing OPENAI_API_KEY")
            return None
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                response = await client.post(
                    f"{self._settings.openai_base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._settings.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"model": self._settings.openai_model, "messages": messages},
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return str(content).strip()
        except Exception as exc:
            logger.warning("OpenAI chat failed, trying Gemini.", exc_info=exc)
            return None

    async def _chat_gemini(self, messages: list[dict]) -> str | None:
        if not self._settings.gemini_api_key:
            logger.warning("Gemini chat skipped: missing GEMINI_API_KEY")
            return None
        try:
            conversation = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            prompt = (
                "You are a SaaS sales assistant. Respond with tactical, lead-specific advice.\n\n"
                f"{conversation}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
            }
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self._settings.gemini_model}:generateContent?key={self._settings.gemini_api_key}"
            )
            async with httpx.AsyncClient(timeout=25) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return str(data["candidates"][0]["content"]["parts"][0]["text"]).strip()
        except Exception as exc:
            logger.warning("Gemini chat failed, using fallback.", exc_info=exc)
            return None

    def _dynamic_chat_fallback(self, message: str, lead_context: dict) -> str:
        lead_name = lead_context.get("name") or "this lead"
        business_type = lead_context.get("business_type") or "business"
        rating = lead_context.get("rating")
        review_signal = "limited social proof" if not lead_context.get("reviews") else "existing customer feedback"
        condition = (
            f"rating {rating}" if rating is not None else "unknown rating"
        )
        return (
            f"I could not reach AI providers right now, so here is a contextual response for {lead_name} ({business_type}): "
            f"anchor your answer to {review_signal} and {condition}. Start by addressing this question directly: '{message}'. "
            "Then propose one immediate fix, one measurable KPI outcome, and a 10-minute audit call CTA."
        )
