"""Website quality analysis service."""

from __future__ import annotations

import asyncio
import logging
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebsiteAnalyzerService:
    """Analyze business websites and classify their quality."""

    def __init__(self, timeout_seconds: int = 6) -> None:
        self._timeout = timeout_seconds

    async def analyze_website(self, url: str | None) -> str:
        """Analyze website quality without blocking the event loop."""
        if not url:
            return "NO_WEBSITE"
        return await asyncio.to_thread(self._analyze_website_sync, url)

    async def extract_website_text(self, url: str | None, max_chars: int = 3000) -> str:
        """Fetch and return cleaned website text content for AI analysis."""
        if not url:
            return ""
        return await asyncio.to_thread(self._extract_website_text_sync, url, max_chars)

    def _analyze_website_sync(self, url: str) -> str:
        started_at = time.perf_counter()
        try:
            response = requests.get(
                url,
                timeout=min(self._timeout, 5),
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    )
                },
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Website analysis failed for %s.", url, exc_info=exc)
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

    def _extract_website_text_sync(self, url: str, max_chars: int) -> str:
        try:
            response = requests.get(
                url,
                timeout=min(self._timeout, 6),
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    )
                },
                allow_redirects=True,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            content = " ".join(soup.get_text(separator=" ").split())
            return content[:max_chars]
        except requests.RequestException as exc:
            logger.warning("Website content extraction failed for %s.", url, exc_info=exc)
            return ""
