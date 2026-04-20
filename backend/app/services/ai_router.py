"""Multi-provider AI router with deterministic fallback."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from app.core.config import Settings

logger = logging.getLogger(__name__)

_ANALYSIS_SYSTEM = (
    "You are a senior B2B sales strategist helping reps close deals. "
    "You output ONLY valid JSON. Every sentence must be grounded in the inputs: business name, type, reviews, rating, website text. "
    "Forbidden: generic filler like 'shows clear potential', 'conversion-focused digital improvements', "
    "'active business presence', 'amplified online', or any wording that could apply equally to any random business. "
    "Required: mention the business by name at least once in 'summary'; tie pros/cons to review themes, stars, or site gaps when data exists."
)


def _coerce_to_object(parsed: Any) -> dict[str, Any] | None:
    """Ensure provider output is a single JSON object (OpenAI/Gemini sometimes wrap or mis-shape)."""
    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, list) and len(parsed) == 1 and isinstance(parsed[0], dict):
        return parsed[0]
    return None


def _parse_json_object_from_text(text: str | None) -> dict[str, Any] | None:
    """Parse JSON from model text; strip markdown fences; return None if not a dict."""
    if not text or not str(text).strip():
        return None
    stripped = str(text).strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return _coerce_to_object(parsed)


class AIRouterService:
    """Route AI analysis across OpenAI, Gemini, and rule-based fallback."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def analyze_business(self, lead_input: dict[str, Any]) -> dict[str, Any]:
        """Return normalized analysis from best available provider."""
        prompt = self._build_prompt(lead_input)
        logger.info("AI analyze request payload: %s", lead_input)

        openai_result = await self._try_openai(prompt)
        if openai_result is not None:
            print("Using OpenAI")
            logger.info("AI analyze response from OpenAI: %s", openai_result)
            return self._normalize(openai_result, lead_input)

        gemini_result = await self._try_gemini(prompt)
        if gemini_result is not None:
            print("Using Gemini")
            logger.info("AI analyze response from Gemini: %s", gemini_result)
            return self._normalize(gemini_result, lead_input)

        print("Using fallback")
        logger.warning("AI analyze fallback triggered after provider failures.")
        return self._normalize(self._rule_based_fallback(lead_input), lead_input)

    def normalized_rule_based_fallback(self, lead_input: dict[str, Any]) -> dict[str, Any]:
        """Deterministic analysis when providers fail or callers need a safe fallback."""
        return self._normalize(self._rule_based_fallback(lead_input), lead_input)

    async def _try_openai(self, prompt: str) -> dict[str, Any] | None:
        if not self._settings.openai_api_key:
            logger.warning("OpenAI skipped: missing OPENAI_API_KEY")
            return None
        try:
            payload = {
                "model": self._settings.openai_model,
                "temperature": 0.35,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": _ANALYSIS_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            }
            async with httpx.AsyncClient(timeout=55) as client:
                response = await client.post(
                    f"{self._settings.openai_base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._settings.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                parsed = _parse_json_object_from_text(content)
                if parsed is None:
                    logger.warning("OpenAI returned non-object JSON; trying Gemini.")
                    return None
                return parsed
        except Exception as exc:
            logger.warning("OpenAI provider failed, trying Gemini.", exc_info=exc)
            return None

    async def _try_gemini(self, prompt: str) -> dict[str, Any] | None:
        if not self._settings.gemini_api_key:
            logger.warning("Gemini skipped: missing GEMINI_API_KEY")
            return None
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._settings.gemini_model}:generateContent?key={self._settings.gemini_api_key}"
        )
        payload_primary = {
            "systemInstruction": {"parts": [{"text": _ANALYSIS_SYSTEM}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.35},
        }
        payload_flat = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{_ANALYSIS_SYSTEM}\n\n---\n\n{prompt}"}],
                }
            ],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.35},
        }
        try:
            async with httpx.AsyncClient(timeout=55) as client:
                response = await client.post(url, json=payload_primary)
                if response.status_code >= 400:
                    logger.warning("Gemini analyze HTTP %s; retrying without systemInstruction.", response.status_code)
                    response = await client.post(url, json=payload_flat)
                response.raise_for_status()
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = _parse_json_object_from_text(text)
                if parsed is None:
                    logger.warning("Gemini returned non-object JSON; using fallback.")
                    return None
                return parsed
        except Exception as exc:
            logger.warning("Gemini provider failed, using fallback.", exc_info=exc)
            return None

    def _build_prompt(self, lead_input: dict[str, Any]) -> str:
        name = lead_input.get("name") or "Unknown business"
        business_type = lead_input.get("business_type") or "unknown"
        website_url = (lead_input.get("website") or "").strip() or "not listed"
        website_content = lead_input.get("website_content") or ""
        if not str(website_content).strip():
            website_content = "not available (no crawl or no site)"
        else:
            website_content = str(website_content).strip()[:4000]
        rating = lead_input.get("rating")
        review_count = int(lead_input.get("review_count") or 0)
        reviews = lead_input.get("google_reviews") or []
        review_lines = "\n".join(f"- {str(r).strip()}" for r in reviews[:6] if str(r).strip())
        if not review_lines:
            review_lines = "(no review text in our export)"

        return (
            "Produce a DEAL-READY analysis for ONE lead the rep is about to call or email.\n\n"
            "INPUTS\n"
            f"- Business name: {name}\n"
            f"- Category / type: {business_type}\n"
            f"- Public website URL (if known): {website_url}\n"
            f"- Homepage / site text we scraped (may be partial): {website_content}\n"
            f"- Google star rating: {rating if rating is not None else 'unknown'}\n"
            f"- Review count (Google): {review_count}\n"
            f"- Review excerpts:\n{review_lines}\n\n"
            "RULES\n"
            f"1) summary: 2–4 sentences. Name “{name}” explicitly. Say what they likely sell/do for customers, "
            "what the rating/reviews suggest about quality or demand, and one concrete gap or opportunity "
            "(e.g. booking, mobile site, follow-up) inferred from reviews or site text—not generic marketing speak.\n"
            "2) pros: 2-4 bullets. Each bullet must cite a signal (e.g. \"4.8* with 40+ reviews implies...\", "
            "“Reviewers mention ‘friendly staff’ → …”). If data is thin, say what is missing and how to verify on the call.\n"
            "3) cons / risks: 2–4 bullets. Honest blockers (e.g. weak site, few reviews, seasonal risk) tied to this business.\n"
            "4) sentiment: positive | neutral | negative — from review tone + rating, not a guess from category alone.\n"
            "5) action: contact if worth a conversation; skip only if clearly a bad fit.\n"
            "6) pitch: ONE specific offer line (e.g. “mobile booking + SMS reminders for grooming slots”) aligned with "
            f"{business_type} and the gaps you inferred—not a vague “digital package”.\n\n"
            "Return ONLY valid JSON with exactly these keys (no markdown, no extra keys):\n"
            '{"summary":"string","pros":["string","string"],"cons":["string","string"],'
            '"sentiment":"positive|neutral|negative","action":"contact|skip","pitch":"string"}'
        )

    def _normalize(self, output: dict[str, Any], lead_input: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(output, dict):
            logger.warning("AI output was type %s, not dict; using rule-based fallback.", type(output).__name__)
            return self._normalize(self._rule_based_fallback(lead_input), lead_input)

        summary = str(output.get("summary") or "").strip()
        pros = [str(item).strip() for item in (output.get("pros") or []) if str(item).strip()]
        cons = [str(item).strip() for item in (output.get("cons") or []) if str(item).strip()]
        sentiment = str(output.get("sentiment") or "").strip().lower()
        action = str(output.get("action") or "").strip().lower()
        pitch = str(output.get("pitch") or "").strip()

        if not summary or not pros or not cons or sentiment not in {"positive", "neutral", "negative"}:
            fallback = self._rule_based_fallback(lead_input)
            summary = summary or fallback["summary"]
            pros = pros or fallback["pros"]
            cons = cons or fallback["cons"]
            if sentiment not in {"positive", "neutral", "negative"}:
                sentiment = fallback["sentiment"]
            if action not in {"contact", "skip"}:
                action = fallback["action"]
            pitch = pitch or fallback["pitch"]

        if action not in {"contact", "skip"}:
            action = "contact"

        return {
            "summary": summary,
            "pros": pros[:4],
            "cons": cons[:4],
            "sentiment": sentiment,
            "action": action,
            "pitch": pitch,
        }

    def _rule_based_fallback(self, lead_input: dict[str, Any]) -> dict[str, Any]:
        name = str(lead_input.get("name") or "This business").strip() or "This business"
        business_type = str(lead_input.get("business_type") or "business").strip()
        website_url = (lead_input.get("website") or "").strip()
        wc = (lead_input.get("website_content") or "").strip()
        has_site_signal = bool(website_url) or bool(wc)
        rating = lead_input.get("rating")
        review_count = int(lead_input.get("review_count") or 0)
        reviews = [str(r).strip() for r in (lead_input.get("google_reviews") or []) if str(r).strip()]
        first_review = reviews[0][:220] + ("…" if len(reviews[0]) > 220 else "") if reviews else ""

        try:
            rnum = float(rating) if rating is not None else None
        except (TypeError, ValueError):
            rnum = None

        weak_social = rnum is not None and rnum < 4.0 and review_count >= 3
        thin_reviews = review_count == 0 and not reviews

        if rnum is not None and rnum >= 4.5 and review_count >= 8:
            sentiment = "positive"
        elif weak_social:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        action = "contact"

        if business_type.lower() in {"pet grooming salon", "pet grooming", "grooming"} or "groom" in business_type.lower():
            pitch = "Online booking + SMS reminders for appointments, plus a simple ‘before/after’ gallery to lift conversions"
        elif "restaurant" in business_type.lower() or "cafe" in business_type.lower():
            pitch = "Reservations, menu SEO, and Google Business Profile review capture tied to dine-in traffic"
        else:
            pitch = f"Clear website offer + lead capture tuned to {business_type} buyers (audit first call)"

        summary_parts = [
            f"{name} operates as {business_type}.",
        ]
        if rnum is not None:
            summary_parts.append(
                f"Signals: about {review_count} Google reviews and a {rnum}* average - use that social proof in your opener."
            )
        elif review_count:
            summary_parts.append(f"They have roughly {review_count} Google reviews—quote themes on the call.")
        else:
            summary_parts.append("Review volume in our export is low; validate reputation live on the call.")

        if first_review:
            summary_parts.append(f'Example review theme to reference: "{first_review}"')

        if not has_site_signal:
            summary_parts.append(
                "We see little or no website text—position a small site or landing page plus measurable lead capture."
            )
        else:
            summary_parts.append(
                "We have some site text—use a short audit to find booking/contact friction and fix the top leak first."
            )

        pros = [
            f"Named account “{name}” — you can personalize outreach and avoid spray-and-pray.",
        ]
        if rnum is not None and rnum >= 4.2:
            pros.append(
                f"Rating {rnum}* suggests satisfied customers - ask what they want next (booking, upsell, loyalty)."
            )
        elif reviews:
            pros.append("Review excerpts give you real phrases to mirror in email subject lines and calls.")
        else:
            pros.append("Category + location are enough to run a tight discovery call if you prepare 3 questions.")

        cons = []
        if thin_reviews:
            cons.append("Thin or missing review text in export—confirm trust signals before promising ROI.")
        if not has_site_signal:
            cons.append("Weak or missing web presence in our data—scope a minimal viable site before big builds.")
        if weak_social:
            cons.append("Rating/review mix looks fragile—lead with diagnosis, not a big retainer pitch.")
        if not cons:
            cons.append("Differentiation vs nearby competitors still unknown—ask how they win repeat customers.")

        return {
            "summary": " ".join(summary_parts),
            "pros": pros[:4],
            "cons": cons[:4],
            "sentiment": sentiment,
            "action": action,
            "pitch": pitch,
        }
