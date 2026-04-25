"""Google Places client service."""
# pylint: disable=invalid-name
from __future__ import annotations

import logging
import time
from typing import Any

import requests
from app.core.config import Settings

logger = logging.getLogger(__name__)


class GooglePlacesService:
    """Encapsulates communication with Google Places APIs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _safe_request(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            logger.debug("Places GET %s", url)
            response = requests.get(url, params=params, timeout=5)
            logger.debug("Places response status: %s", response.status_code)
            if response.status_code != 200:
                logger.warning("Places HTTP non-200: %s", response.status_code)
                return {}
            return response.json()
        except Exception:
            logger.exception("Places request failed")
            return {}

    def _ensure_api_key(self) -> bool:
        if not self._settings.google_places_api_key:
            logger.warning("Missing Google Places API key")
            return False
        return True

    def search_businesses(self, query: str, max_results: int = 300) -> list[dict[str, Any]]:
        """Run Places Text Search and return normalized place records."""
        if not self._ensure_api_key():
            return []
        if max_results <= 0:
            return []

        all_results: list[dict[str, Any]] = []
        seen_place_ids: set[str] = set()
        next_page_token: str | None = None

        while len(all_results) < max_results:
            params: dict[str, Any] = {"key": self._settings.google_places_api_key}
            if next_page_token:
                # Google requires a short delay before next_page_token becomes valid.
                time.sleep(2)
                params["pagetoken"] = next_page_token
            else:
                params["query"] = query

            payload = self._safe_request(self._settings.google_places_text_search_url, params)
            if not payload:
                break

            api_status = payload.get("status", "UNKNOWN")
            if api_status == "INVALID_REQUEST" and next_page_token:
                # token may still be warming up; retry once
                time.sleep(1)
                payload = self._safe_request(self._settings.google_places_text_search_url, params)
                if not payload:
                    break
                api_status = payload.get("status", "UNKNOWN")

            if api_status not in {"OK", "ZERO_RESULTS"}:
                logger.warning("Places Text Search status=%s", api_status)
                break

            for result in payload.get("results", []):
                place_id = (result.get("place_id") or "").strip()
                if place_id and place_id in seen_place_ids:
                    continue
                if place_id:
                    seen_place_ids.add(place_id)
                all_results.append(result)
                if len(all_results) >= max_results:
                    break

            next_page_token = payload.get("next_page_token")
            if not next_page_token:
                break

        return all_results[:max_results]

    def get_place_details(self, place_id: str) -> dict[str, Any]:
        """Fetch details used to enrich lead output."""
        if not self._ensure_api_key():
            return {}
        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,website,rating,user_ratings_total,reviews",
            "key": self._settings.google_places_api_key,
        }
        payload = self._safe_request(self._settings.google_places_details_url, params)
        if not payload:
            return {}
        if payload.get("status") != "OK":
            logger.warning("Places Details status=%s", payload.get("status"))
            return {}
        return payload.get("result", {})

    def autocomplete_locations(self, query: str, country: str | None = None) -> list[dict[str, Any]]:
        """Fetch location autocomplete suggestions."""
        logger.debug("autocomplete_locations query=%r country=%r", query, country)
        if not self._ensure_api_key():
            return []
        params = {
            "input": query,
            "types": "(cities)",
            "key": self._settings.google_places_api_key,
        }
        country_code_map = {
            "India": "in",
            "United States": "us",
            "United Kingdom": "gb",
            "Canada": "ca",
            "Australia": "au",
            "Germany": "de",
            "France": "fr",
            "Armenia": "am",
            "UAE": "ae",
            "Singapore": "sg",
            "United Arab Emirates": "ae",
        }
        if country:
            code = country_code_map.get(country)
            if code:
                params["components"] = f"country:{code}"
        payload = self._safe_request(self._settings.google_places_autocomplete_url, params)
        if not payload:
            return []
        api_status = payload.get("status", "UNKNOWN")
        if api_status not in {"OK", "ZERO_RESULTS"}:
            logger.warning(
                "Places Autocomplete status=%s error=%r query=%r country=%r",
                api_status,
                payload.get("error_message"),
                query,
                country,
            )
            return []
        results: list[dict[str, Any]] = []
        for item in payload.get("predictions", []):
            place_id = item.get("place_id")
            if not place_id:
                continue
            results.append(
                {
                    "placeId": place_id,
                    "mainText": item.get("structured_formatting", {}).get("main_text", ""),
                    "secondaryText": item.get("structured_formatting", {}).get("secondary_text", ""),
                }
            )
        logger.info("Google autocomplete output for query=%r country=%r: %s", query, country, results)
        return results

    def popular_locations(self, country: str) -> list[dict[str, Any]]:
        """Fetch popular locations fallback."""
        places = self.search_businesses(f"major cities in {country}")
        if not places:
            logger.info("No places from Text Search; using static city fallbacks for %s", country)
            return [
                {
                    "placeId": f"seed:{country}:Mumbai",
                    "mainText": "Mumbai",
                    "secondaryText": country,
                },
                {
                    "placeId": f"seed:{country}:Delhi",
                    "mainText": "Delhi",
                    "secondaryText": country,
                },
                {
                    "placeId": f"seed:{country}:Bangalore",
                    "mainText": "Bangalore",
                    "secondaryText": country,
                },
            ]
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for place in places:
            name = (place.get("name") or "").strip().lower()
            if name not in seen and len(deduped) < 10:
                seen.add(name)
                deduped.append(place)
        return [
            {
                "placeId": place.get("place_id"),
                "mainText": place.get("name", ""),
                "secondaryText": place.get("formatted_address", ""),
            }
            for place in deduped
            if place.get("place_id")
        ]

    def get_location_details(self, place_id: str) -> dict[str, Any]:
        """Fetch location details."""
        if not self._ensure_api_key():
            return {}
        params = {
            "place_id": place_id,
            "fields": "address_components,geometry,formatted_address,name",
            "key": self._settings.google_places_api_key,
        }
        payload = self._safe_request(self._settings.google_places_details_url, params)
        if not payload:
            return {}
        if payload.get("status") != "OK":
            logger.warning("Places location details status=%s", payload.get("status"))
            return {}
        result = payload.get("result", {})
        components = result.get("address_components", [])

        def find_component(*types: str) -> str:
            for component in components:
                component_types = component.get("types", [])
                if any(component_type in component_types for component_type in types):
                    return component.get("long_name", "")
            return ""

        geometry = result.get("geometry", {}).get("location", {})
        lat = geometry.get("lat")
        lng = geometry.get("lng")
        normalized = {
            "city": (
                find_component("locality", "postal_town", "administrative_area_level_2")
                or find_component("sublocality", "neighborhood")
                or result.get("name")
                or ""
            ),
            "state": find_component("administrative_area_level_1") or "",
            "country": find_component("country") or "",
            "lat": float(lat) if lat is not None else 0.0,
            "lng": float(lng) if lng is not None else 0.0,
            "displayName": result.get("formatted_address") or result.get("name") or "",
            "placeId": place_id,
        }
        logger.info("Google location details place_id=%s", place_id)
        logger.info("Google location details output: %s", normalized)
        return normalized
