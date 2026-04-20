"""Lead intelligence service for AI business analysis."""

from __future__ import annotations

import asyncio
import logging
from hashlib import sha256

from app.core.config import Settings
from app.schemas.lead import Lead
from app.services.ai_router import AIRouterService

logger = logging.getLogger(__name__)


class LeadAnalyzerService:
    """Analyze leads with OpenAI and attach actionable sales intelligence."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache: dict[str, dict] = {}
        self._ai_router = AIRouterService(settings=settings)

    async def enrich(self, leads: list[Lead]) -> list[Lead]:
        """Enrich top leads with AI insights using async batched requests."""
        if not leads:
            return leads

        max_leads = max(1, min(self._settings.ai_max_leads, 15))
        batch_size = max(1, min(self._settings.ai_batch_size, 6))
        scored_indexes = sorted(
            range(len(leads)),
            key=lambda idx: self._priority_rank(leads[idx].priority_score),
        )
        target_indexes = scored_indexes[:max_leads]

        for start in range(0, len(target_indexes), batch_size):
            batch = target_indexes[start : start + batch_size]
            results = await asyncio.gather(
                *(self._analyze_single_lead(lead=leads[idx]) for idx in batch),
                return_exceptions=True,
            )
            for idx, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.warning("AI analysis failed for %s.", leads[idx].name, exc_info=result)
                    self._apply_fallback(leads[idx])
                else:
                    self._apply_ai_result(leads[idx], result)
        return leads

    async def _analyze_single_lead(self, lead: Lead) -> dict:
        cache_key = self._cache_key(lead)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = await self._ai_router.analyze_business(
            {
                "name": lead.name,
                "business_type": lead.business_type,
                "website": lead.website,
                "website_content": lead.website_content,
                "rating": lead.rating,
                "review_count": lead.review_count,
                "google_reviews": lead.google_reviews,
            }
        )
        self._cache[cache_key] = result
        return result

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
        lead.business_summary = (
            f"{(lead.business_type or 'Business').title()} has room for stronger digital conversion positioning."
        )
        lead.pros = ["Established local presence", "Core offer appears marketable online"]
        lead.cons = ["Likely missing optimized lead capture flow", "Opportunity to improve automated follow-up"]
        lead.customer_sentiment = "neutral"
        lead.recommended_action = "contact"
        lead.pitch_suggestion = "Website and automation improvement package"

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

