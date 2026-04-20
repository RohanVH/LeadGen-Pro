"""Gemini-powered suggestion service for business sub-types."""

from __future__ import annotations

import json
import logging

from app.core.config import Settings
from app.core.gemini_models import gemini_model_chain
from app.services.llm_clients import gemini_generate_content_v1_sync, run_sync_with_ai_timeout

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

        for model_id in gemini_model_chain(self._settings.gemini_model):
            for use_json in (True, False):
                try:
                    raw = await run_sync_with_ai_timeout(
                        gemini_generate_content_v1_sync,
                        self._settings.gemini_api_key,
                        model_id,
                        prompt,
                        response_mime_json=use_json,
                    )
                except Exception as exc:
                    logger.warning(
                        "Gemini business type suggestion failed model=%s json=%s: %s",
                        model_id,
                        use_json,
                        exc,
                    )
                    continue
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("Gemini suggest non-JSON text for model=%s", model_id)
                    continue
                suggestions = parsed.get("suggestions") if isinstance(parsed, dict) else []
                if not isinstance(suggestions, list):
                    continue
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
                        return cleaned
                if cleaned:
                    return cleaned
        return []
