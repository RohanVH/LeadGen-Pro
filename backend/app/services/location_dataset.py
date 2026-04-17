"""Structured location dataset access via GeoDB Cities API."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings


class LocationDatasetService:
    """Fetch and cache city lists from GeoDB Cities API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._country_code_cache: dict[str, str | None] = {}
        self._cities_cache: dict[str, list[dict[str, str]]] = {}

    async def get_cities_by_country(self, country_name: str) -> list[dict[str, str]]:
        """Return top cities for a country using GeoDB as the primary dataset."""
        cached = self._cities_cache.get(country_name)
        if cached is not None:
            return cached

        if not self._settings.geodb_api_key:
            return []

        country_code = await self._resolve_country_code(country_name)
        if not country_code:
            return []

        headers = {
            "X-RapidAPI-Key": self._settings.geodb_api_key,
            "X-RapidAPI-Host": self._settings.geodb_api_host,
        }
        params = {
            "limit": 20,
            "offset": 0,
            "sort": "-population",
            "hateoasMode": "false",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                self._settings.geodb_cities_url.format(country_code=country_code),
                params=params,
                headers=headers,
            )

        if response.status_code != 200:
            return []

        payload = response.json()
        cities = [
            {
                "city": item.get("city", ""),
                "state": item.get("region") or item.get("regionCode") or "",
                "country": item.get("country", country_name),
            }
            for item in payload.get("data", [])
            if item.get("city")
        ]
        self._cities_cache[country_name] = cities
        return cities

    async def _resolve_country_code(self, country_name: str) -> str | None:
        cached = self._country_code_cache.get(country_name)
        if cached is not None:
            return cached

        headers = {
            "X-RapidAPI-Key": self._settings.geodb_api_key,
            "X-RapidAPI-Host": self._settings.geodb_api_host,
        }
        params = {
            "namePrefix": country_name,
            "limit": 5,
            "hateoasMode": "false",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                self._settings.geodb_countries_url,
                params=params,
                headers=headers,
            )

        if response.status_code != 200:
            self._country_code_cache[country_name] = None
            return None

        payload = response.json()
        data: list[dict[str, Any]] = payload.get("data", [])
        resolved = next(
            (
                item.get("code")
                for item in data
                if (item.get("name") or "").strip().lower() == country_name.strip().lower()
            ),
            None,
        )
        if not resolved and data:
            resolved = data[0].get("code")

        self._country_code_cache[country_name] = resolved
        return resolved
