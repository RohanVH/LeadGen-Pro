"""Website email extraction service."""

from __future__ import annotations

import asyncio
import logging
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EmailScraperService:
    """Scrapes business websites and extracts contact emails."""

    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", re.IGNORECASE)
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    }

    def __init__(self, timeout_seconds: int = 6) -> None:
        self._timeout = timeout_seconds

    async def extract_email(self, website_url: str | None) -> str | None:
        """
        Extract the first valid email from homepage, /contact, and /about pages.

        This function offloads blocking HTTP calls to a worker thread so the
        FastAPI event loop remains responsive under concurrent requests.
        """
        if not website_url:
            return None
        return await asyncio.to_thread(self._extract_email_sync, website_url)

    async def is_weak_website(self, website_url: str | None) -> bool:
        """
        Basic weak-site detection.

        A website is considered weak if title/meta tags are missing or page fetch fails.
        """
        if not website_url:
            return False
        return await asyncio.to_thread(self._is_weak_website_sync, website_url)

    def _extract_email_sync(self, website_url: str) -> str | None:
        normalized = self._normalize_url(website_url)
        if not normalized:
            return None

        candidates = [
            normalized,
            urljoin(normalized, "/contact"),
            urljoin(normalized, "/about"),
        ]

        for url in candidates:
            html = self._safe_fetch(url)
            if not html:
                continue
            email = self._find_email(html)
            if email:
                return email
        return None

    def _is_weak_website_sync(self, website_url: str) -> bool:
        normalized = self._normalize_url(website_url)
        if not normalized:
            return True

        html = self._safe_fetch(normalized)
        if not html:
            return True

        soup = BeautifulSoup(html, "html.parser")
        has_title = bool(soup.title and (soup.title.string or "").strip())
        has_meta = bool(soup.find("meta"))
        return not (has_title and has_meta)

    def _safe_fetch(self, url: str) -> str | None:
        try:
            response = requests.get(
                url,
                timeout=min(self._timeout, 5),
                headers=self.DEFAULT_HEADERS,
                allow_redirects=True,
            )
            if response.status_code >= 400:
                logger.warning("Email scraper received status %s for %s.", response.status_code, url)
                return None
            return response.text
        except requests.RequestException as exc:
            logger.warning("Email scraper request failed for %s.", url, exc_info=exc)
            return None

    def _find_email(self, html: str) -> str | None:
        found = self.EMAIL_PATTERN.findall(html)
        if not found:
            return None

        for email in found:
            cleaned = email.strip(" .,;:()[]{}<>\"'")
            if cleaned.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
                continue
            return cleaned
        return None

    def _normalize_url(self, website_url: str) -> str | None:
        value = website_url.strip()
        if not value:
            return None
        if not value.startswith(("http://", "https://")):
            value = f"https://{value}"

        parsed = urlparse(value)
        if not parsed.netloc:
            return None
        return f"{parsed.scheme}://{parsed.netloc}"
