"""Social media discovery for business leads."""

from __future__ import annotations

import asyncio
import logging
import re
from urllib.parse import unquote, urlparse

import requests

logger = logging.getLogger(__name__)


class SocialDiscoveryService:
    """Find Instagram and YouTube links using lightweight web search queries."""

    SEARCH_URL = "https://duckduckgo.com/html/"
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    }

    INSTAGRAM_REGEX = re.compile(r"https?://(?:www\.)?instagram\.com/[A-Za-z0-9._-]+/?", re.IGNORECASE)
    YOUTUBE_REGEX = re.compile(
        r"https?://(?:www\.)?youtube\.com/(?:@[\w.-]+|channel/[\w-]+|c/[\w-]+|user/[\w-]+)",
        re.IGNORECASE,
    )

    def __init__(self, timeout_seconds: int = 6) -> None:
        self._timeout = timeout_seconds

    async def discover(self, business_name: str, city: str) -> tuple[str | None, str | None]:
        """Discover Instagram and YouTube URLs for a business."""
        instagram_query = f"{business_name} {city} instagram"
        youtube_query = f"{business_name} {city} youtube"
        instagram_task = asyncio.to_thread(self._find_first_match, instagram_query, self.INSTAGRAM_REGEX)
        youtube_task = asyncio.to_thread(self._find_first_match, youtube_query, self.YOUTUBE_REGEX)
        instagram_url, youtube_url = await asyncio.gather(instagram_task, youtube_task)
        return instagram_url, youtube_url

    def _find_first_match(self, query: str, pattern: re.Pattern[str]) -> str | None:
        html = self._search_html(query)
        if not html:
            return None

        for match in pattern.finditer(html):
            normalized = self._normalize_url(match.group(0))
            if normalized:
                return normalized
        return None

    def _search_html(self, query: str) -> str:
        try:
            response = requests.get(
                self.SEARCH_URL,
                params={"q": query},
                headers=self.DEFAULT_HEADERS,
                timeout=min(self._timeout, 6),
                allow_redirects=True,
            )
            if response.status_code >= 400:
                return ""
            return response.text
        except requests.RequestException as exc:
            logger.warning("Social discovery request failed for query '%s'.", query, exc_info=exc)
            return ""

    def _normalize_url(self, url: str) -> str | None:
        decoded = unquote(url).strip().rstrip(").,;")
        parsed = urlparse(decoded)
        if not parsed.scheme or not parsed.netloc:
            return None
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
