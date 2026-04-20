"""Interactive AI assistant for per-lead analysis and follow-up chat."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from app.core.config import Settings
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
        except Exception:
            logger.exception("Lead analyze failed; using rule-based fallback.")
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
        openai_messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            *openai_history,
        ]

        openai_answer = await self._chat_openai(openai_messages)
        if openai_answer:
            logger.info("Lead chat response from OpenAI (preview): %s...", openai_answer[:120])
            return LeadChatResponse(response=openai_answer)

        gemini_answer = await self._chat_gemini(system_prompt, openai_history, user_message)
        if gemini_answer:
            logger.info("Lead chat response from Gemini (fallback) (preview): %s...", gemini_answer[:120])
            return LeadChatResponse(response=gemini_answer)

        logger.warning("Lead chat fallback triggered after OpenAI and Gemini failures.")
        return LeadChatResponse(
            response=self._dynamic_chat_fallback(user_message, context.model_dump(by_alias=True))
        )

    async def _chat_openai(self, messages: list[dict[str, str]]) -> str | None:
        if not self._settings.openai_api_key:
            logger.warning("OpenAI chat skipped: missing OPENAI_API_KEY")
            return None
        model = self._settings.openai_model
        base_payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 1200,
        }
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                url = f"{self._settings.openai_base_url.rstrip('/')}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self._settings.openai_api_key}",
                    "Content-Type": "application/json",
                }
                response = await client.post(url, headers=headers, json=base_payload)
                if response.status_code >= 400:
                    err_txt = response.text[:900]
                    logger.warning("OpenAI chat HTTP %s: %s", response.status_code, err_txt)
                    if response.status_code == 400 and (
                        "max_tokens" in err_txt or "max_completion_tokens" in err_txt
                    ):
                        retry = {k: v for k, v in base_payload.items() if k != "max_tokens"}
                        retry["max_completion_tokens"] = 1200
                        response = await client.post(url, headers=headers, json=retry)
                        if response.status_code >= 400:
                            logger.warning("OpenAI chat retry HTTP %s: %s", response.status_code, response.text[:600])
                response.raise_for_status()
                data = response.json()
                choice = (data.get("choices") or [{}])[0]
                message = (choice.get("message") or {})
                content = message.get("content")
                if not content:
                    logger.warning("OpenAI chat returned empty content: %s", data)
                    return None
                return str(content).strip()
        except Exception as exc:
            logger.warning("OpenAI chat failed.", exc_info=exc)
            return None

    def _gemini_chat_model_id(self) -> str:
        """Same model as batch/analyze unless GEMINI_CHAT_MODEL is set explicitly."""
        return (self._settings.gemini_chat_model or "").strip() or self._settings.gemini_model

    def _gemini_model_fallback_chain(self) -> list[str]:
        """Try chat model first, then the analyze model, then common ids (deduped)."""
        ordered: list[str] = []
        seen: set[str] = set()
        for mid in (
            self._gemini_chat_model_id(),
            self._settings.gemini_model,
            "gemini-1.5-flash",
            "gemini-2.0-flash",
        ):
            m = (mid or "").strip()
            if m and m not in seen:
                seen.add(m)
                ordered.append(m)
        return ordered

    @staticmethod
    def _openai_history_to_gemini_contents(openai_history: list[dict[str, str]]) -> list[dict[str, Any]]:
        """Map to Gemini roles (user/model). Gemini rejects invalid turns; merge consecutive same-role messages."""
        contents: list[dict[str, Any]] = []
        for m in openai_history:
            role = m["role"]
            text = (m.get("content") or "").strip()
            if not text:
                continue
            gemini_role = "model" if role == "assistant" else "user"
            if contents and contents[-1]["role"] == gemini_role:
                prev = contents[-1]["parts"][0]["text"]
                contents[-1]["parts"][0]["text"] = f"{prev}\n\n{text}"
            else:
                contents.append({"role": gemini_role, "parts": [{"text": text}]})
        return contents

    @staticmethod
    def _gemini_safety_settings() -> list[dict[str, str]]:
        """Reduce false blocks on business/sales chat (names, reviews)."""
        categories = (
            "HARM_CATEGORY_HARASSMENT",
            "HARM_CATEGORY_HATE_SPEECH",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "HARM_CATEGORY_DANGEROUS_CONTENT",
        )
        return [{"category": c, "threshold": "BLOCK_ONLY_HIGH"} for c in categories]

    @staticmethod
    def _extract_gemini_text(data: dict[str, Any]) -> tuple[str | None, str]:
        """Return (text, reason_if_empty)."""
        candidates = data.get("candidates") or []
        if not candidates:
            prompt_fb = data.get("promptFeedback") or {}
            return None, f"no candidates; promptFeedback={prompt_fb}"
        c0 = candidates[0]
        reason = str(c0.get("finishReason") or "")
        parts = ((c0.get("content") or {}).get("parts")) or []
        if not parts:
            return None, f"empty parts; finishReason={reason}"
        text = parts[0].get("text") or ""
        if not str(text).strip():
            return None, f"empty text; finishReason={reason}"
        return str(text).strip(), ""

    async def _chat_gemini(
        self,
        system_prompt: str,
        openai_history: list[dict[str, str]],
        fallback_user_text: str,
    ) -> str | None:
        if not self._settings.gemini_api_key:
            logger.warning("Gemini chat skipped: missing GEMINI_API_KEY")
            return None

        api_key = self._settings.gemini_api_key
        base_url = "https://generativelanguage.googleapis.com/v1beta/models"

        def build_url(mid: str) -> str:
            return f"{base_url}/{mid}:generateContent?key={api_key}"

        contents = self._openai_history_to_gemini_contents(openai_history)
        if not contents and fallback_user_text.strip():
            contents = [{"role": "user", "parts": [{"text": fallback_user_text.strip()}]}]
        if contents and contents[0]["role"] != "user":
            contents.insert(
                0,
                {"role": "user", "parts": [{"text": "Here is our conversation so far. Answer the latest user message."}]},
            )

        gen_cfg: dict[str, Any] = {"temperature": 0.65, "maxOutputTokens": 2048}

        async def post_json(url: str, body: dict[str, Any]) -> httpx.Response:
            async with httpx.AsyncClient(timeout=90.0) as client:
                return await client.post(url, json=body)

        body_fb: dict[str, Any] = {
            "contents": [],
            "generationConfig": gen_cfg,
            "safetySettings": self._gemini_safety_settings(),
        }
        if contents:
            sys_as_user = (
                "System / lead context (follow these facts when answering):\n\n"
                f"{system_prompt}\n\n---\nContinue the conversation below."
            )
            first = contents[0]
            if first["role"] == "user":
                combined = f"{sys_as_user}\n\n{first['parts'][0]['text']}"
                body_fb["contents"] = [{"role": "user", "parts": [{"text": combined}]}, *contents[1:]]
            else:
                body_fb["contents"] = [{"role": "user", "parts": [{"text": sys_as_user}]}, *contents]
        else:
            body_fb["contents"] = [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\nUser: {fallback_user_text.strip()}"}],
                }
            ]

        body_primary: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": gen_cfg,
            "safetySettings": self._gemini_safety_settings(),
        }

        def try_parse(resp: httpx.Response) -> str | None:
            if resp.status_code >= 400:
                return None
            resp.raise_for_status()
            text, err = self._extract_gemini_text(resp.json())
            if not text:
                logger.warning("Gemini chat empty body: %s", err)
            return text

        try:
            for model_id in self._gemini_model_fallback_chain():
                url = build_url(model_id)
                response = await post_json(url, body_primary)
                if response.status_code >= 400:
                    logger.warning(
                        "Gemini chat HTTP %s model=%s: %s",
                        response.status_code,
                        model_id,
                        response.text[:900],
                    )
                else:
                    try:
                        t = try_parse(response)
                        if t:
                            return t
                    except Exception:
                        logger.warning("Gemini chat parse failed model=%s", model_id, exc_info=True)

                response_fb = await post_json(url, body_fb)
                if response_fb.status_code >= 400:
                    logger.warning(
                        "Gemini chat fallback HTTP %s model=%s: %s",
                        response_fb.status_code,
                        model_id,
                        response_fb.text[:600],
                    )
                else:
                    try:
                        t = try_parse(response_fb)
                        if t:
                            return t
                    except Exception:
                        logger.warning("Gemini chat fallback parse failed model=%s", model_id, exc_info=True)

            one_shot = (
                f"{system_prompt}\n\n"
                f"User question:\n{fallback_user_text.strip()}\n\n"
                "Answer directly in plain language."
            )
            body_simple = {
                "contents": [{"role": "user", "parts": [{"text": one_shot}]}],
                "generationConfig": gen_cfg,
                "safetySettings": self._gemini_safety_settings(),
            }
            for model_id in self._gemini_model_fallback_chain():
                response2 = await post_json(build_url(model_id), body_simple)
                if response2.status_code >= 400:
                    continue
                try:
                    t = try_parse(response2)
                    if t:
                        return t
                except Exception:
                    continue

            body_plain = {
                "contents": [{"role": "user", "parts": [{"text": one_shot}]}],
                "generationConfig": gen_cfg,
            }
            for model_id in self._gemini_model_fallback_chain():
                response3 = await post_json(build_url(model_id), body_plain)
                if response3.status_code >= 400:
                    continue
                try:
                    t = try_parse(response3)
                    if t:
                        return t
                except Exception:
                    continue

            return None
        except Exception as exc:
            logger.warning("Gemini chat failed.", exc_info=exc)
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
                    f"We don't have live AI right now, but from Google review text for {lead_name}: "
                    f"customers mention things like: {preview}{rating_bit} "
                    "High stars plus positive wording usually implies people felt well treated, but reviews rarely spell out "
                    "'customer support' as a department. On a call, ask how they handle after-hours issues and new-patient questions."
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

        review_signal = "limited social proof" if not reviews else "existing customer feedback"
        condition = f"rating {rating}" if rating is not None else "unknown rating"
        return (
            f"(Offline mode) For {lead_name} ({business_type}): use {review_signal} and {condition}. "
            f'About your question: "{message}" — use the table fields above on your call. '
            "The AI chat request did not return a usable reply from the model (timeout, model name, or provider error). "
            "If this persists, check server logs for OpenAI/Gemini HTTP errors (e.g. OPENAI_MODEL, quotas, timeouts)."
        )
