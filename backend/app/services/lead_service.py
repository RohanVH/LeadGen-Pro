"""Business logic for lead generation and processing."""

from __future__ import annotations

import asyncio
import logging
import re

from app.core.config import Settings
from app.schemas.lead import Lead
from app.services.analyzer import LeadAnalyzerService
from app.services.email_scraper import EmailScraperService
from app.services.google_places import GooglePlacesService
from app.services.website_analyzer import WebsiteAnalyzerService

logger = logging.getLogger(__name__)


class LeadService:
    """Coordinates search, processing, and enrichment of lead data."""

    MAX_RESULTS_CEILING = 15

    def __init__(
        self,
        settings: Settings,
        places_service: GooglePlacesService,
        email_scraper_service: EmailScraperService,
        website_analyzer_service: WebsiteAnalyzerService,
        analyzer_service: LeadAnalyzerService,
    ) -> None:
        self._settings = settings
        self._places_service = places_service
        self._email_scraper_service = email_scraper_service
        self._website_analyzer_service = website_analyzer_service
        self._analyzer_service = analyzer_service

    async def search(self, city: str, business_type: str, country: str | None = None) -> list[Lead]:
        """Search and process leads from Google Places."""
        location_suffix = f", {country}" if country else ""
        query = f"{business_type} in {city}{location_suffix}"

        places = self._places_service.search_businesses(query=query)
        filtered_places = self._filter_relevant_places(
            places=places,
            city=city,
            country=country,
        )
        max_results = max(1, min(self._settings.lead_max_results, self.MAX_RESULTS_CEILING))
        limited_places = filtered_places[:max_results]
        logger.info(
            "Lead search for query '%s' returned %s places, %s after filtering, %s after limiting.",
            query,
            len(places),
            len(filtered_places),
            len(limited_places),
        )

        semaphore = asyncio.Semaphore(self._settings.scraper_max_concurrency)
        tasks = [
            self._build_lead(
                place=place,
                city=city,
                business_type=business_type,
                semaphore=semaphore,
            )
            for place in limited_places
        ]
        leads = [lead for lead in await asyncio.gather(*tasks) if lead is not None]

        return await self._analyzer_service.enrich(leads)

    async def _build_lead(
        self,
        place: dict,
        city: str,
        business_type: str,
        semaphore: asyncio.Semaphore,
    ) -> Lead | None:
        place_id = place.get("place_id")
        details = self._places_service.get_place_details(place_id=place_id) if place_id else {}
        if place_id and not details:
            logger.info("Proceeding without place details for place_id '%s'.", place_id)

        website = details.get("website")
        phone_number = details.get("formatted_phone_number")

        email: str | None = None
        weak_website = False
        website_quality = "NO_WEBSITE"
        if website:
            async with semaphore:
                email = await self._email_scraper_service.extract_email(website)
                website_quality = await self._website_analyzer_service.analyze_website(website)
                weak_website = website_quality == "WEAK_WEBSITE"

        lead = Lead(
            name=place.get("name", "Unknown"),
            address=place.get("formatted_address"),
            phone_number=phone_number,
            website=website,
            email=email,
            city=city,
            business_type=business_type,
            priority_score=self._compute_priority_score(
                website=website,
                phone_number=phone_number,
                email=email,
                weak_website=weak_website,
            ),
            is_hot_lead=self._is_hot_lead(
                website=website,
                phone_number=phone_number,
                email=email,
            ),
            website_quality=website_quality,
        )
        return lead

    def _compute_priority_score(
        self,
        website: str | None,
        phone_number: str | None,
        email: str | None,
        weak_website: bool,
    ) -> str:
        """Compute lead priority score for conversion-focused triage."""
        has_phone_or_email = bool(phone_number or email)
        if not website and has_phone_or_email:
            return "HIGH"

        if website and (not email or weak_website):
            return "MEDIUM"

        if website and email and phone_number:
            return "LOW"

        # Fallback bucket for incomplete records that do not qualify as hot leads.
        return "MEDIUM"

    def _is_hot_lead(
        self,
        website: str | None,
        phone_number: str | None,
        email: str | None,
    ) -> bool:
        """Return True when lead matches Hot Leads Focus criteria."""
        return (not website) and bool(phone_number or email)

    def _filter_relevant_places(
        self,
        places: list[dict],
        city: str,
        country: str | None,
    ) -> list[dict]:
        """Remove duplicates and results outside the requested location."""
        city_l = city.lower()
        country_l = country.lower() if country else None
        seen_keys: set[str] = set()
        filtered: list[dict] = []

        for place in places:
            name = (place.get("name") or "").strip()
            address = (place.get("formatted_address") or "").strip()
            if not name:
                continue

            dedupe_key = (place.get("place_id") or f"{name}|{address}").lower()
            if dedupe_key in seen_keys:
                continue

            searchable_text = f"{name} {address}".lower()
            if city_l not in searchable_text:
                continue
            if country_l and country_l not in searchable_text:
                continue

            if self._is_irrelevant_entry(name=name):
                continue

            seen_keys.add(dedupe_key)
            filtered.append(place)
        return filtered

    def _is_irrelevant_entry(self, name: str) -> bool:
        """
        Basic heuristics to remove generic directory/listing results.

        Places responses occasionally include aggregator-like entries that are
        low-value for direct agency outreach.
        """
        normalized = re.sub(r"\s+", " ", name).strip().lower()
        noisy_tokens = ["directory", "listing", "map", "search results"]
        return any(token in normalized for token in noisy_tokens)
