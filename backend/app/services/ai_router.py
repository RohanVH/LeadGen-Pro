"""Multi-provider AI router with deterministic fallback."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from app.core.config import Settings

logger = logging.getLogger(__name__)


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
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a sales strategist for agencies. "
                            "Return only valid JSON in the requested format."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            }
            async with httpx.AsyncClient(timeout=25) as client:
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
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"},
            }
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self._settings.gemini_model}:generateContent?key={self._settings.gemini_api_key}"
            )
            async with httpx.AsyncClient(timeout=25) as client:
                response = await client.post(url, json=payload)
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
        website_content = lead_input.get("website_content") or "not available"
        rating = lead_input.get("rating")
        review_count = int(lead_input.get("review_count") or 0)
        reviews = lead_input.get("google_reviews") or []
        review_snippets = " | ".join(str(r) for r in reviews[:4] if str(r).strip()) if reviews else "not available"
        return (
            "Analyze this business lead and decide if it is worth contacting.\n\n"
            f"Business name: {name}\n"
            f"Business type: {business_type}\n"
            f"Website content: {website_content}\n"
            f"Rating: {rating if rating is not None else 'not available'}\n"
            f"Review count: {review_count}\n"
            f"Google reviews: {review_snippets}\n\n"
            "Output JSON with this exact structure:\n"
            "{"
            '"summary":"...",'
            '"pros":["...","..."],'
            '"cons":["...","..."],'
            '"sentiment":"positive/neutral/negative",'
            '"action":"contact/skip",'
            '"pitch":"suggest solution"'
            "}"
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
        business_type = str(lead_input.get("business_type") or "local business")
        has_website = bool(lead_input.get("website"))
        rating = lead_input.get("rating")
        review_count = int(lead_input.get("review_count") or 0)

        weak_social_proof = rating is not None and float(rating) < 4.0 and review_count >= 3
        poor_presence = (not has_website) or review_count == 0

        if poor_presence or weak_social_proof:
            sentiment = "negative" if weak_social_proof else "neutral"
            action = "contact"
            pitch = "Website + automation lead capture package"
            cons = [
                "Limited digital trust and conversion flow",
                "Potentially weak follow-up systems for new inquiries",
            ]
        else:
            sentiment = "positive"
            action = "contact"
            pitch = "Automation and conversion optimization upgrade"
            cons = [
                "Likely missing advanced funnel automation",
                "Opportunity to improve retention and reactivation",
            ]

        return {
            "summary": (
                f"{business_type.title()} shows clear potential for stronger client acquisition "
                "with conversion-focused digital improvements."
            ),
            "pros": [
                "Active business presence in local market",
                "Clear service positioning that can be amplified online",
            ],
            "cons": cons,
            "sentiment": sentiment,
            "action": action,
            "pitch": pitch,
        }
