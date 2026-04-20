"""Website email extraction service."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailEnrichment:
    """Normalized email enrichment payload."""

    email: str | None
    email_type: str
    email_confidence: str


class EmailScraperService:
    """Scrapes business websites and extracts contact emails."""

    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", re.IGNORECASE)
    GENERIC_PREFIXES = {"info", "contact", "hello"}
    HIGH_CONFIDENCE_PREFIXES = {"owner", "founder"}
    LOW_SIGNAL_PREFIXES = {
        "admin",
        "billing",
        "careers",
        "help",
        "hr",
        "jobs",
        "marketing",
        "noreply",
        "no-reply",
        "sales",
        "support",
        "team",
    }
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
        enrichment = await self.enrich_email(website_url)
        return enrichment.email

    async def enrich_email(self, website_url: str | None) -> EmailEnrichment:
        """Return the best available email plus type and confidence metadata."""
        if not website_url:
            return EmailEnrichment(email=None, email_type="missing", email_confidence="LOW")
        return await asyncio.to_thread(self._enrich_email_sync, website_url)

    async def is_weak_website(self, website_url: str | None) -> bool:
        """
        Basic weak-site detection.

        A website is considered weak if title/meta tags are missing or page fetch fails.
        """
        if not website_url:
            return False
        return await asyncio.to_thread(self._is_weak_website_sync, website_url)

    def _enrich_email_sync(self, website_url: str) -> EmailEnrichment:
        normalized = self._normalize_url(website_url)
        if not normalized:
            return EmailEnrichment(email=None, email_type="missing", email_confidence="LOW")

        candidates = [
            normalized,
            urljoin(normalized, "/contact"),
            urljoin(normalized, "/about"),
        ]
        discovered: list[str] = []
        seen: set[str] = set()

        for url in candidates:
            html = self._safe_fetch(url)
            if not html:
                continue
            for email in self._find_emails(html):
                normalized_email = email.lower()
                if normalized_email in seen:
                    continue
                seen.add(normalized_email)
                discovered.append(normalized_email)

        best_email = self._choose_best_email(discovered)
        if best_email:
            return EmailEnrichment(
                email=best_email,
                email_type=self._classify_email_type(best_email, is_generated=False),
                email_confidence=self._classify_email_confidence(best_email, is_generated=False),
            )

        generated_email = self._generate_fallback_email(normalized)
        if not generated_email:
            return EmailEnrichment(email=None, email_type="missing", email_confidence="LOW")

        return EmailEnrichment(
            email=generated_email,
            email_type="generated",
            email_confidence="LOW",
        )

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

    def _find_emails(self, html: str) -> list[str]:
        found = self.EMAIL_PATTERN.findall(html)
        cleaned_emails: list[str] = []
        seen: set[str] = set()
        for email in found:
            cleaned = email.strip(" .,;:()[]{}<>\"'")
            if cleaned.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
                continue
            normalized = cleaned.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            cleaned_emails.append(normalized)
        return cleaned_emails

    def _choose_best_email(self, emails: list[str]) -> str | None:
        if not emails:
            return None
        ranked = sorted(
            emails,
            key=lambda email: (
                self._confidence_rank(self._classify_email_confidence(email, is_generated=False)),
                self._type_rank(self._classify_email_type(email, is_generated=False)),
                len(email),
            ),
        )
        return ranked[0]

    def _generate_fallback_email(self, website_url: str) -> str | None:
        domain = self._extract_domain(website_url)
        if not domain:
            return None
        for prefix in ("info", "contact", "hello"):
            return f"{prefix}@{domain}"
        return None

    def _extract_domain(self, website_url: str) -> str | None:
        parsed = urlparse(website_url)
        domain = parsed.netloc.lower().strip()
        if not domain:
            return None
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or None

    def _classify_email_type(self, email: str, is_generated: bool) -> str:
        if is_generated:
            return "generated"
        local_part = email.split("@", 1)[0].lower()
        if local_part in self.HIGH_CONFIDENCE_PREFIXES:
            return local_part
        if local_part in self.GENERIC_PREFIXES:
            return local_part
        return "name"

    def _classify_email_confidence(self, email: str, is_generated: bool) -> str:
        if is_generated:
            return "LOW"
        local_part = email.split("@", 1)[0].lower()
        if local_part in self.HIGH_CONFIDENCE_PREFIXES or self._looks_like_named_mailbox(local_part):
            return "HIGH"
        if local_part in self.GENERIC_PREFIXES:
            return "MEDIUM"
        if local_part in self.LOW_SIGNAL_PREFIXES:
            return "MEDIUM"
        return "HIGH"

    def _looks_like_named_mailbox(self, local_part: str) -> bool:
        if not local_part or any(char.isdigit() for char in local_part):
            return False
        if local_part in self.GENERIC_PREFIXES or local_part in self.LOW_SIGNAL_PREFIXES:
            return False
        return bool(re.fullmatch(r"[a-z]+([._-][a-z]+)?", local_part))

    def _confidence_rank(self, confidence: str) -> int:
        return {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(confidence, 3)

    def _type_rank(self, email_type: str) -> int:
        return {
            "owner": 0,
            "founder": 1,
            "name": 2,
            "info": 3,
            "contact": 4,
            "hello": 5,
            "generated": 6,
            "missing": 7,
        }.get(email_type, 8)

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
