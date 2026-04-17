"""Website quality analysis service."""

from __future__ import annotations

import asyncio
import time

import requests
from bs4 import BeautifulSoup


class WebsiteAnalyzerService:
    """Analyze business websites and classify their quality."""

    def __init__(self, timeout_seconds: int = 6) -> None:
        self._timeout = timeout_seconds

    async def analyze_website(self, url: str | None) -> str:
        """Analyze website quality without blocking the event loop."""
        if not url:
            return "NO_WEBSITE"
        return await asyncio.to_thread(self._analyze_website_sync, url)

    def _analyze_website_sync(self, url: str) -> str:
        started_at = time.perf_counter()
        try:
            response = requests.get(
                url,
                timeout=self._timeout,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    )
                },
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.RequestException:
            return "WEAK_WEBSITE"

        response_time = time.perf_counter() - started_at
        soup = BeautifulSoup(response.text, "html.parser")

        has_https = url.startswith("https://")
        has_title = bool(soup.title and (soup.title.string or "").strip())
        has_meta_description = bool(
            soup.find("meta", attrs={"name": lambda value: value and value.lower() == "description"})
        )
        is_fast = response_time <= 3

        if has_https and has_title and has_meta_description and is_fast:
            return "GOOD_WEBSITE"
        return "WEAK_WEBSITE"
