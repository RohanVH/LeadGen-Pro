"""Google Places client service."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings

logger = logging.getLogger(__name__)


class GooglePlacesService:
    """Encapsulates communication with Google Places APIs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _ensure_api_key(self) -> None:
        if not self._settings.google_places_api_key:
            print("Missing Google Places API key")
            return
        print("API KEY present")

    async def search_businesses(self, query: str) -> list[dict[str, Any]]:
        """Run Places Text Search and return normalized place records."""
        self._ensure_api_key()

        params = {"query": query, "key": self._settings.google_places_api_key}
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(self._settings.google_places_text_search_url, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as exc:
            logger.warning("Google Places text search timed out for query '%s'.", query, exc_info=exc)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Lead search timed out. Please try again.",
            ) from exc
        except httpx.HTTPError as exc:
            logger.exception("Google Places text search failed for query '%s'.", query, exc_info=exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch leads from Google Places API.",
            ) from exc
        except ValueError as exc:
            logger.exception("Google Places text search returned invalid JSON for query '%s'.", query, exc_info=exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Received an invalid response from Google Places API.",
            ) from exc

        api_status = payload.get("status", "UNKNOWN")

        if api_status not in {"OK", "ZERO_RESULTS"}:
            message = payload.get("error_message", "Google Places returned an error.")
            logger.warning("Google Places text search returned status '%s' for query '%s': %s", api_status, query, message)
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
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(self._settings.google_places_details_url, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Google Places details lookup failed for place_id '%s'.", place_id, exc_info=exc)
            return {}
        if payload.get("status") != "OK":
            logger.warning("Google Places details returned non-OK status for place_id '%s': %s", place_id, payload)
            return {}

        return payload.get("result", {})

    async def autocomplete_locations(self, query: str, country: str | None = None) -> list[dict[str, Any]]:
        """Fetch location autocomplete suggestions restricted to geocoded places."""
        print("autocomplete_locations called with query:", query, "country:", country)
        self._ensure_api_key()
        if not self._settings.google_places_api_key:
            print("No API key, returning fallback")
            return [{"description": query}]
        params: dict[str, str] = {
            "input": f"{query}, {country}" if country else query,
            "types": "(regions)",
            "key": self._settings.google_places_api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(self._settings.google_places_autocomplete_url, params=params)
                print("Autocomplete response status:", response.status_code)
            response.raise_for_status()
            payload = response.json()
            print("Autocomplete payload status:", payload.get("status"))
        except Exception as exc:
            print("Autocomplete error:", str(exc))
            return []

        api_status = payload.get("status", "UNKNOWN")
        if api_status not in {"OK", "ZERO_RESULTS"}:
            print("Bad status:", api_status)
            return []

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
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(self._settings.google_places_details_url, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as exc:
            logger.warning("Google Places location details timed out for place_id '%s'.", place_id, exc_info=exc)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Location details timed out. Please try again.",
            ) from exc
        except httpx.HTTPError as exc:
            logger.exception("Google Places location details failed for place_id '%s'.", place_id, exc_info=exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch location details from Google Places API.",
            ) from exc
        except ValueError as exc:
            logger.exception("Google Places location details returned invalid JSON for place_id '%s'.", place_id, exc_info=exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Received an invalid response from Google Places API.",
            )

        if payload.get("status") != "OK":
            message = payload.get("error_message", "Unable to fetch location details.")
            logger.warning("Google Places location details returned non-OK status for place_id '%s': %s", place_id, message)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=message,
            )

        return payload.get("result", {})
