from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


class GooglePlacesService:
    """Encapsulates communication with Google Places APIs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _has_api_key(self) -> bool:
        return bool(self._settings.google_places_api_key)

    async def _safe_request(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        """Safe HTTP request that NEVER crashes."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url, params=params)

            if response.status_code != 200:
                logger.warning("Bad response status: %s", response.status_code)
                return {}

            try:
                return response.json()
            except Exception:
                logger.warning("Invalid JSON response")
                return {}

        except Exception as e:
            logger.warning("Request failed: %s", str(e))
            return {}

    async def search_businesses(self, query: str) -> list[dict[str, Any]]:
        """Safe search (never throws)."""
        if not self._has_api_key():
            logger.warning("Missing Google API key")
            return []

        params = {
            "query": query,
            "key": self._settings.google_places_api_key,
        }

        payload = await self._safe_request(
            self._settings.google_places_text_search_url,
            params,
        )

        if not payload:
            return []

        api_status = payload.get("status", "UNKNOWN")

        if api_status not in {"OK", "ZERO_RESULTS"}:
            logger.warning("Google API bad status: %s", api_status)
            return []

        return payload.get("results", [])

    async def get_place_details(self, place_id: str) -> dict[str, Any]:
        """Safe details fetch."""
        if not self._has_api_key():
            return {}

        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,website",
            "key": self._settings.google_places_api_key,
        }

        payload = await self._safe_request(
            self._settings.google_places_details_url,
            params,
        )

        if payload.get("status") != "OK":
            return {}

        return payload.get("result", {})

    async def autocomplete_locations(
        self, query: str, country: str | None = None
    ) -> list[dict[str, Any]]:
        """Safe autocomplete (never crashes)."""
        if not self._has_api_key():
            return [{"description": query}]

        params = {
            "input": f"{query}, {country}" if country else query,
            "types": "(regions)",
            "key": self._settings.google_places_api_key,
        }

        payload = await self._safe_request(
            self._settings.google_places_autocomplete_url,
            params,
        )

        if not payload:
            return []

        api_status = payload.get("status", "UNKNOWN")

        if api_status not in {"OK", "ZERO_RESULTS"}:
            return []

        return payload.get("predictions", [])

    async def popular_locations(self, country: str) -> list[dict[str, Any]]:
        """Safe popular locations (with fallback)."""
        try:
            places = await self.search_businesses(
                query=f"major cities in {country}"
            )
        except Exception as e:
            logger.warning("Popular locations failed: %s", str(e))
            places = []

        deduped_results: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        country_normalized = country.strip().lower()

        for place in places:
            name = (place.get("name") or "").strip()
            if not name:
                continue

            normalized = name.lower()

            if normalized == country_normalized:
                continue

            if normalized in seen_names:
                continue

            seen_names.add(normalized)
            deduped_results.append(place)

            if len(deduped_results) >= 10:
                break

        # 🔥 HARD FALLBACK (prevents empty UI)
        if not deduped_results:
            return [
                {"name": "Mumbai"},
                {"name": "Delhi"},
                {"name": "Bangalore"},
                {"name": "Chennai"},
            ]

        return deduped_results

    async def get_location_details(self, place_id: str) -> dict[str, Any]:
        """Safe location details."""
        if not self._has_api_key():
            return {}

        params = {
            "place_id": place_id,
            "fields": "address_component,geometry,formatted_address,name",
            "key": self._settings.google_places_api_key,
        }

        payload = await self._safe_request(
            self._settings.google_places_details_url,
            params,
        )

        if payload.get("status") != "OK":
            return {}

        return payload.get("result", {})