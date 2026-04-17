"""Google Places client service."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings


class GooglePlacesService:
    """Encapsulates communication with Google Places APIs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _ensure_api_key(self) -> None:
        if not self._settings.google_places_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google Places API key is not configured.",
            )

    async def search_businesses(self, query: str) -> list[dict[str, Any]]:
        """Run Places Text Search and return normalized place records."""
        self._ensure_api_key()

        params = {"query": query, "key": self._settings.google_places_api_key}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(self._settings.google_places_text_search_url, params=params)

        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch leads from Google Places API.",
            )

        payload = response.json()
        api_status = payload.get("status", "UNKNOWN")

        if api_status not in {"OK", "ZERO_RESULTS"}:
            message = payload.get("error_message", "Google Places returned an error.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{api_status}: {message}",
            )

        return payload.get("results", [])

    async def get_place_details(self, place_id: str) -> dict[str, Any]:
        """Fetch details used to enrich lead output."""
        self._ensure_api_key()
        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,website",
            "key": self._settings.google_places_api_key,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(self._settings.google_places_details_url, params=params)

        if response.status_code != status.HTTP_200_OK:
            return {}

        payload = response.json()
        if payload.get("status") != "OK":
            return {}

        return payload.get("result", {})

    async def autocomplete_locations(self, query: str, country: str | None = None) -> list[dict[str, Any]]:
        """Fetch location autocomplete suggestions restricted to geocoded places."""
        self._ensure_api_key()
        params: dict[str, str] = {
            "input": f"{query}, {country}" if country else query,
            "types": "(regions)",
            "key": self._settings.google_places_api_key,
        }

        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(self._settings.google_places_autocomplete_url, params=params)

        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch location suggestions from Google Places API.",
            )

        payload = response.json()
        api_status = payload.get("status", "UNKNOWN")
        if api_status not in {"OK", "ZERO_RESULTS"}:
            message = payload.get("error_message", "Google Places returned an error.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{api_status}: {message}",
            )

        return payload.get("predictions", [])

    async def popular_locations(self, country: str) -> list[dict[str, Any]]:
        """Fetch popular city and town suggestions for a country."""
        places = await self.search_businesses(query=f"major cities in {country}")
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

        return deduped_results

    async def get_location_details(self, place_id: str) -> dict[str, Any]:
        """Fetch geometry and address components for a selected location."""
        self._ensure_api_key()
        params = {
            "place_id": place_id,
            "fields": "address_component,geometry,formatted_address,name",
            "key": self._settings.google_places_api_key,
        }
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(self._settings.google_places_details_url, params=params)

        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch location details from Google Places API.",
            )

        payload = response.json()
        if payload.get("status") != "OK":
            message = payload.get("error_message", "Unable to fetch location details.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=message,
            )

        return payload.get("result", {})
