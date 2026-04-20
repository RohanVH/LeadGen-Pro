"""Gemini-powered suggestion service for business sub-types."""

from __future__ import annotations

import json
import logging

import httpx
from app.core.config import Settings

logger = logging.getLogger(__name__)


class BusinessTypeSuggesterService:
    """Suggest related business sub-types when local suggestions are insufficient."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def suggest(self, query: str, category: str) -> list[str]:
        normalized_query = query.strip()
        normalized_category = category.strip()
        if len(normalized_query) < 2 or len(normalized_category) < 2:
            return []
        if not self._settings.gemini_api_key:
            logger.warning("Business type suggester skipped: missing GEMINI_API_KEY")
            return []

        prompt = (
            "You generate concise business subtype suggestions for SaaS lead search.\n"
            "Return ONLY JSON in this format: "
            '{"suggestions":["item 1","item 2","item 3"]}\n\n'
            f"Category: {normalized_category}\n"
            f"User query: {normalized_query}\n"
            "Rules:\n"
            "- Provide 5 to 8 short suggestions.\n"
            "- Include close synonyms and practical variants.\n"
            "- Keep suggestions relevant to the given category.\n"
            "- No explanation text."
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"},
        }
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._settings.gemini_model}:generateContent?key={self._settings.gemini_api_key}"
        )
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                text = str(data["candidates"][0]["content"]["parts"][0]["text"]).strip()
                parsed = json.loads(text)
                suggestions = parsed.get("suggestions") if isinstance(parsed, dict) else []
                if not isinstance(suggestions, list):
                    return []
                cleaned: list[str] = []
                seen: set[str] = set()
                for item in suggestions:
                    value = str(item).strip()
                    if len(value) < 2:
                        continue
                    key = value.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    cleaned.append(value)
                    if len(cleaned) >= 8:
                        break
                return cleaned
        except Exception as exc:
            logger.warning("Gemini business type suggestion failed.", exc_info=exc)
            return []
