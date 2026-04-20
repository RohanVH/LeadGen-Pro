"""Google Places client service."""

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

    def _safe_request(self, url, params):
        try:
            print(f"Making request to {url}")
            response = requests.get(url, params=params, timeout=5)
            print(f"Response status: {response.status_code}")
            if response.status_code != 200:
                print("Bad status code")
                return {}
            data = response.json()
            return data
        except Exception as e:
            print(f"Request error: {str(e)}")
            return {}

    def _ensure_api_key(self):
        if not self._settings.google_places_api_key:
            print("Missing Google Places API key")
            return False
        print("API KEY present")
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
            params = {"key": self._settings.google_places_api_key}
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
                print(f"Bad status: {api_status}")
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
            print("Bad details status")
            return {}
        return payload.get("result", {})

    def autocomplete_locations(self, query: str, country: str | None = None) -> list[dict[str, Any]]:
        """Fetch location autocomplete suggestions."""
        print(f"autocomplete_locations query: {query}, country: {country}")
        if not self._ensure_api_key():
            print("No API key, fallback")
            return [{"description": query}]
        params = {
            "input": f"{query}, {country}" if country else query,
            "types": "(regions)",
            "key": self._settings.google_places_api_key,
        }
        payload = self._safe_request(self._settings.google_places_autocomplete_url, params)
        if not payload:
            return []
        api_status = payload.get("status", "UNKNOWN")
        if api_status not in {"OK", "ZERO_RESULTS"}:
            print(f"Bad autocomplete status: {api_status}")
            return []
        return payload.get("predictions", [])

    def popular_locations(self, country: str) -> list[dict[str, Any]]:
        """Fetch popular locations fallback."""
        places = self.search_businesses(f"major cities in {country}")
        if not places:
            print("No places, fallback cities")
            return [{"name": "Mumbai"}, {"name": "Delhi"}, {"name": "Bangalore"}]
        deduped = []
        seen = set()
        for place in places:
            name = (place.get("name") or "").strip().lower()
            if name not in seen and len(deduped) < 10:
                seen.add(name)
                deduped.append(place)
        return deduped

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
            print("Bad location details")
            return {}
        return payload.get("result", {})

