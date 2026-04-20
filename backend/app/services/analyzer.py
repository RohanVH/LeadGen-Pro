"""Lead intelligence service for AI business analysis."""

from __future__ import annotations

import asyncio
import json
import logging
from hashlib import sha256

import httpx
from app.core.config import Settings
from app.schemas.lead import Lead

logger = logging.getLogger(__name__)


class LeadAnalyzerService:
    """Analyze leads with OpenAI and attach actionable sales intelligence."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache: dict[str, dict] = {}

    async def enrich(self, leads: list[Lead]) -> list[Lead]:
        """Enrich top leads with AI insights using async batched requests."""
        if not leads:
            return leads

        if not self._settings.openai_api_key:
            logger.info("OPENAI_API_KEY missing; returning leads without AI analysis.")
            return leads

        max_leads = max(1, min(self._settings.ai_max_leads, 15))
        batch_size = max(1, min(self._settings.ai_batch_size, 6))
        scored_indexes = sorted(
            range(len(leads)),
            key=lambda idx: self._priority_rank(leads[idx].priority_score),
        )
        target_indexes = scored_indexes[:max_leads]

        async with httpx.AsyncClient(timeout=25) as client:
            for start in range(0, len(target_indexes), batch_size):
                batch = target_indexes[start : start + batch_size]
                results = await asyncio.gather(
                    *(self._analyze_single_lead(client=client, lead=leads[idx]) for idx in batch),
                    return_exceptions=True,
                )
                for idx, result in zip(batch, results):
                    if isinstance(result, Exception):
                        logger.warning("AI analysis failed for %s.", leads[idx].name, exc_info=result)
                        self._apply_fallback(leads[idx])
                    else:
                        self._apply_ai_result(leads[idx], result)
        return leads

    async def _analyze_single_lead(self, client: httpx.AsyncClient, lead: Lead) -> dict:
        cache_key = self._cache_key(lead)
        if cache_key in self._cache:
            return self._cache[cache_key]

        payload = {
            "model": self._settings.openai_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a sales strategist for agencies. "
                        "Return only valid JSON and keep recommendations practical."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze this business lead and decide if it is worth contacting.\n\n"
                        f"Business name: {lead.name}\n"
                        f"Business type: {lead.business_type or 'unknown'}\n"
                        f"Website content: {lead.website_content or 'not available'}\n"
                        f"Rating: {lead.rating if lead.rating is not None else 'not available'}\n"
                        f"Review count: {lead.review_count}\n"
                        f"Google reviews: {' | '.join(lead.google_reviews[:4]) if lead.google_reviews else 'not available'}\n\n"
                        "Output JSON with this exact structure:\n"
                        "{"
                        '"summary":"...",'
                        '"pros":["...","..."],'
                        '"cons":["...","..."],'
                        '"sentiment":"positive/neutral/negative",'
                        '"action":"contact/skip",'
                        '"pitch":"suggest solution"'
                        "}"
                    ),
                },
            ],
        }
        response = await client.post(
            f"{self._settings.openai_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        self._cache[cache_key] = parsed
        return parsed

    def _apply_ai_result(self, lead: Lead, data: dict) -> None:
        lead.business_summary = str(data.get("summary") or "Not available")
        lead.pros = [str(item) for item in (data.get("pros") or [])][:4]
        lead.cons = [str(item) for item in (data.get("cons") or [])][:4]

        sentiment = str(data.get("sentiment") or "neutral").lower()
        lead.customer_sentiment = sentiment if sentiment in {"positive", "neutral", "negative"} else "neutral"

        action = str(data.get("action") or "manual review").lower()
        if action in {"contact", "skip"}:
            lead.recommended_action = action
        else:
            lead.recommended_action = "manual review"

        lead.pitch_suggestion = str(data.get("pitch") or "Not available")

    def _apply_fallback(self, lead: Lead) -> None:
        lead.business_summary = "Not available"
        lead.recommended_action = "manual review"
        if not lead.pitch_suggestion:
            lead.pitch_suggestion = "Not available"

    def _cache_key(self, lead: Lead) -> str:
        payload = "|".join(
            [
                lead.name or "",
                lead.business_type or "",
                lead.website or "",
                lead.website_content or "",
                str(lead.rating or ""),
                str(lead.review_count or 0),
            ]
        )
        return sha256(payload.encode("utf-8")).hexdigest()

    def _priority_rank(self, score: str) -> int:
        return {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(score, 3)

