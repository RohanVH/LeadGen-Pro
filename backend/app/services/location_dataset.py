"""Structured location dataset access via GeoDB."""

from __future__ import annotations
import logging
from typing import Any

import requests
from app.core.config import Settings

logger = logging.getLogger(__name__)


class LocationDatasetService:
    """Fetch cities from GeoDB."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._cities_cache = {}

    def get_cities_by_country(self, country_name: str) -> list[dict[str, str]]:
        cached = self._cities_cache.get(country_name)
        if cached:
            return cached

        if not self._settings.geodb_api_key:
            print("No GeoDB key")
            return []

        # Fallback country code
        country_code = "US"

        headers = {
            "X-RapidAPI-Key": self._settings.geodb_api_key,
            "X-RapidAPI-Host": self._settings.geodb_api_host,
        }
        params = {"limit": 20, "sort": "-population"}
        url = self._settings.geodb_cities_url.format(country_code=country_code)

        try:
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code != 200:
                print("GeoDB bad status")
                return []
            payload = response.json()
        except Exception as e:
            print(f"GeoDB error: {e}")
            return []

        cities = [{"city": item.get("city", ""), "state": item.get("region", ""), "country": country_name} for item in payload.get("data", [])]
        self._cities_cache[country_name] = cities
        return cities

