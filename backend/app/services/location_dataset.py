"""Structured location dataset access via GeoDB."""

from __future__ import annotations

import logging

import requests
from app.core.config import Settings

logger = logging.getLogger(__name__)


class LocationDatasetService:
    """Fetch cities from GeoDB."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cities_cache: dict[str, list[dict[str, str]]] = {}

    def get_cities_by_country(self, country_name: str) -> list[dict[str, str]]:
        cached = self._cities_cache.get(country_name)
        if cached:
            return cached

        if not self._settings.geodb_api_key:
            logger.debug("GeoDB skipped: missing GEODB_API_KEY")
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
                logger.warning("GeoDB HTTP %s for %s", response.status_code, country_name)
                return []
            payload = response.json()
        except Exception:
            logger.exception("GeoDB request failed for %s", country_name)
            return []

        cities = [
            {"city": item.get("city", ""), "state": item.get("region", ""), "country": country_name}
            for item in payload.get("data", [])
        ]
        self._cities_cache[country_name] = cities
        return cities
