"""Interactive AI assistant for per-lead analysis and follow-up chat."""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import Settings
from app.core.gemini_models import gemini_model_chain
from app.services.llm_clients import (
    gemini_chat_flat_v1_sync,
    openai_chat_completion_sync,
    run_sync_with_ai_timeout,
)
from app.schemas.lead_ai import (
    LeadAnalyzeRequest,
    LeadAnalyzeResponse,
    LeadChatRequest,
    LeadChatResponse,
    LeadContext,
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
            "website": (payload.website or "").strip() or None,
            "website_content": payload.website_content,
            "rating": payload.rating,
            "review_count": len(payload.reviews),
            "google_reviews": payload.reviews,
        }
        try:
            normalized = await self._ai_router.analyze_business(lead_input)
        except Exception as e:
            logger.exception("Lead analyze failed; using rule-based fallback: %s", e)
            logger.error("Lead analyze outer failure: %s", e, exc_info=True)
            normalized = self._ai_router.normalized_rule_based_fallback(lead_input)
        logger.info("Lead analyze normalized AI response: %s", normalized)
        pitch = str(normalized.get("pitch") or "").strip() or "a focused digital upgrade for their funnel"
        action = str(normalized.get("action") or "contact").strip()
        overview = str(normalized.get("summary") or "").strip()
        return LeadAnalyzeResponse(
            overview=overview,
            strengths=[str(item) for item in (normalized.get("pros") or [])][:4],
            weaknesses=[str(item) for item in (normalized.get("cons") or [])][:4],
            customer_perception=str(normalized.get("sentiment") or "neutral"),
            opportunities=[
                f"Deal angle: start with what their reviews/rating imply about demand, then connect to {pitch}.",
                f"Suggested next step: {'book a 15-min audit' if action == 'contact' else 'qualify fit first'} — tie every claim to their site, reviews, or gaps above.",
            ],
            what_to_sell=pitch,
            outreach_angle=(
                f"Open by naming {payload.name} and one concrete signal from their data (review theme, rating, or website gap). "
                f"Offer {pitch} as the logical next step, not a generic pitch deck."
            ),
        )

    def _build_chat_system_prompt(self, context: LeadContext) -> str:
        """Single system message with all lead facts so the model can answer factual questions."""
        reviews = " | ".join(str(r) for r in context.reviews[:6] if str(r).strip()) if context.reviews else "none"
        email = (context.email or "").strip() or "not available"
        phone = (context.phone_number or "").strip() or "not available"
        website = (context.website or "").strip() or "not available"
        wc_raw = (context.website_content or "").strip()
        if len(wc_raw) > 6000:
            wc_raw = wc_raw[:6000] + "\n[website text truncated for chat context size]"
        return (
            "You are a practical B2B sales assistant helping with ONE selected business lead from a CRM table.\n"
            "Rules:\n"
            "- Answer the user's question directly. Do not change the subject to generic sales advice unless they asked for it.\n"
            "- If they ask what a name or phrase means (including Arabic, transliterated, or mixed-language business names), "
            "translate or explain it briefly, then relate it to this lead if relevant.\n"
            "- If they ask what to pitch or how to approach, give concrete angles using rating, reviews, and offer fields below.\n"
            "- Use the facts below. Do not invent email, phone, or URLs.\n"
            "- If email/phone/website are marked 'not available', say clearly we do not have them and suggest next steps.\n"
            "- Keep replies concise unless they ask for detail.\n"
            "- Stay focused on this lead only.\n\n"
            f"Lead name: {context.name}\n"
            f"Business type: {context.business_type}\n"
            f"Email (from our data): {email}\n"
            f"Phone (from our data): {phone}\n"
            f"Website URL (from our data): {website}\n"
            f"Rating: {context.rating if context.rating is not None else 'unknown'}\n"
            f"Review snippets: {reviews}\n"
            f"Website text notes (scraped, may be short): {wc_raw or 'none'}\n"
            f"AI overview: {context.overview or 'none'}\n"
            f"Suggested offer: {context.what_to_sell or 'unknown'}\n"
            f"Outreach angle: {context.outreach_angle or 'none'}"
        )

    @staticmethod
    def _history_to_openai_messages(history: list[dict[str, str]]) -> list[dict[str, str]]:
        """Map chat history to OpenAI roles (assistant/user only)."""
        out: list[dict[str, str]] = []
        for item in history:
            role = (item.get("role") or "user").lower()
            content = (item.get("content") or "").strip()
            if not content:
                continue
            if role == "assistant":
                out.append({"role": "assistant", "content": content})
            else:
                out.append({"role": "user", "content": content})
        return out

    async def chat(self, payload: LeadChatRequest) -> LeadChatResponse:
        """Continue a contextual conversation for a specific lead."""
        context = payload.lead_context or payload.lead
        if context is None:
            return LeadChatResponse(response="Please provide lead context so I can give a targeted answer.")

        history_source = payload.messages or payload.previous_conversation
        raw_history = [{"role": msg.role, "content": msg.content} for msg in history_source[-16:]]

        user_message = (payload.message or "").strip()
        if not user_message:
            for item in reversed(raw_history):
                if (item.get("role") or "").lower() == "user":
                    user_message = (item.get("content") or "").strip()
                    break
        if not user_message:
            return LeadChatResponse(response="Ask a question and I will generate a lead-specific response.")

        logger.info("Lead chat request payload: %s", payload.model_dump(by_alias=True))

        system_prompt = self._build_chat_system_prompt(context)
        openai_history = self._history_to_openai_messages(raw_history)
        hist_for_gemini = list(openai_history)
        if (
            hist_for_gemini
            and hist_for_gemini[-1].get("role") == "user"
            and (hist_for_gemini[-1].get("content") or "").strip() == user_message
        ):
            hist_for_gemini = hist_for_gemini[:-1]

        openai_messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            *openai_history,
        ]
        last = openai_messages[-1] if len(openai_messages) > 1 else None
        if not last or last.get("role") != "user" or (last.get("content") or "").strip() != user_message:
            openai_messages.append({"role": "user", "content": user_message})

        openai_answer = await self._chat_openai(openai_messages)
        if openai_answer:
            logger.info("Lead chat response from OpenAI (preview): %s...", openai_answer[:120])
            return LeadChatResponse(response=openai_answer)

        gemini_answer = await self._chat_gemini(system_prompt, hist_for_gemini, user_message)
        if gemini_answer:
            logger.info("Lead chat response from Gemini (fallback) (preview): %s...", gemini_answer[:120])
            return LeadChatResponse(response=gemini_answer)

        logger.warning("Fallback triggered: lead chat using rule-based reply after provider failures.")
        return LeadChatResponse(
            response=self._dynamic_chat_fallback(user_message, context.model_dump(by_alias=True))
        )

    async def _chat_openai(self, messages: list[dict[str, str]]) -> str | None:
        if not self._settings.openai_api_key:
            logger.warning("OpenAI chat skipped: missing OPENAI_API_KEY")
            return None
        try:
            return await run_sync_with_ai_timeout(
                openai_chat_completion_sync,
                self._settings,
                messages,
                temperature=0.7,
            )
        except Exception as exc:
            logger.error("AI OPENAI CHAT ERROR: %s", exc, exc_info=True)
            return None

    def _gemini_model_fallback_chain(self) -> list[str]:
        """Prefer GEMINI_CHAT_MODEL when set, else GEMINI_MODEL, then shared REST fallbacks."""
        primary = (self._settings.gemini_chat_model or "").strip() or self._settings.gemini_model
        return gemini_model_chain(primary)

    async def _chat_gemini(
        self,
        system_prompt: str,
        openai_history: list[dict[str, str]],
        user_message: str,
    ) -> str | None:
        if not self._settings.gemini_api_key:
            logger.warning("Gemini chat skipped: missing GEMINI_API_KEY")
            return None

        api_key = self._settings.gemini_api_key
        for model_id in self._gemini_model_fallback_chain():
            try:
                return await run_sync_with_ai_timeout(
                    gemini_chat_flat_v1_sync,
                    api_key,
                    model_id,
                    system_prompt,
                    openai_history,
                    user_message,
                )
            except Exception as exc:
                logger.error("AI GEMINI CHAT ERROR model=%s: %s", model_id, exc, exc_info=True)
                continue
        return None

    def _dynamic_chat_fallback(self, message: str, lead_context: dict[str, Any]) -> str:
        """Rule-based reply when APIs fail; still answers email/phone using known fields."""
        lead_name = lead_context.get("name") or "this lead"
        email = (lead_context.get("email") or "").strip()
        phone = (lead_context.get("phone_number") or lead_context.get("phoneNumber") or "").strip()
        website = (lead_context.get("website") or "").strip()
        business_type = (
            lead_context.get("business_type") or lead_context.get("businessType") or "business"
        )
        rating = lead_context.get("rating")
        msg_lower = message.lower()

        if any(k in msg_lower for k in ("email", "e-mail", "mail id", "mail address")):
            if email:
                return (
                    f"For {lead_name}, the email we have on file is {email}. "
                    "If this was auto-generated, verify it on their website or via a quick call before sending bulk mail."
                )
            return (
                f"We don't have a verified email for {lead_name} in this export. "
                f"Try their site ({website or 'search the business name'}) or call {phone or 'their listed phone if available'}."
            )

        if any(k in msg_lower for k in ("phone", "call", "whatsapp", "number")):
            if phone:
                return f"For {lead_name}, the phone number we have is {phone}."
            return f"We don't have a phone number on file for {lead_name}. Check Google Maps or their website."

        if "website" in msg_lower or "url" in msg_lower:
            if website:
                return f"Website: {website}"
            return f"We don't have a website URL stored for {lead_name}. Search the business name to find it."

        reviews_raw = lead_context.get("reviews") or []
        reviews = [str(r).strip() for r in reviews_raw if str(r).strip()]

        supportish = any(
            k in msg_lower
            for k in (
                "support",
                "customer service",
                "good service",
                "bad service",
                "staff",
                "friendly",
                "helpful",
                "care",
                "experience",
                "reputation",
                "trustworthy",
                "reliable",
                "quality",
            )
        ) or ("review" in msg_lower and "?" in message)

        if supportish or ("customer" in msg_lower and "?" in message):
            if reviews:
                preview = " | ".join(reviews[:3])[:600]
                if len(preview) >= 600:
                    preview = preview[:597] + "..."
                rating_bit = f" Their Google rating in our export is {rating}." if rating is not None else ""
                return (
                    f"For {lead_name} ({business_type}), Google review text mentions themes like: {preview}{rating_bit} "
                    "Strong stars plus positive wording usually means customers felt well treated overall; reviews rarely spell out "
                    "a formal “support desk.” On a call, ask how they handle after-hours requests and complaints."
                )
            if rating is not None:
                return (
                    f"We only have the aggregate Google rating ({rating}) for {lead_name}, not review text in this export. "
                    "A strong rating usually correlates with good experiences overall, but it is not proof of phone/chat support quality. "
                    "Ask them directly how patients reach a clinician after hours."
                )
            return (
                f"We don't have review snippets or a rating in this row for {lead_name}, so we can't infer support quality from data. "
                "Check Google Maps reviews or ask on discovery: average response time, after-hours coverage, and how complaints are handled."
            )

        rating_phrase = (
            f"public rating is about {rating} stars"
            if rating is not None
            else "we do not have a rating in this row"
        )
        review_phrase = (
            "review snippets give concrete phrases you can mirror in outreach."
            if reviews
            else "review text is thin here—lean on category fit and discovery questions."
        )
        return (
            f"{lead_name} is a {business_type} lead; {rating_phrase}, and {review_phrase} "
            f"For “{message.strip()}”, anchor your reply on that profile: if ratings are strong, stress proof and capacity; "
            "if they are middling or unknown, lead with a short audit and one measurable improvement (calls, bookings, reviews)—not a generic pitch."
        )
