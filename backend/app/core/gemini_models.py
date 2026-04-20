"""Gemini model ids for REST ``generateContent`` (AI Studio / Generative Language API)."""

from __future__ import annotations

# Ordered after the configured primary; bare ``gemini-1.5-flash`` is often retired or unavailable per account.
_GEMINI_REST_FALLBACKS: tuple[str, ...] = (
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
)


def gemini_model_chain(primary: str | None) -> list[str]:
    """Deduplicated model order: env primary first, then known-good fallbacks."""
    ordered: list[str] = []
    seen: set[str] = set()
    p = (primary or "").strip()
    if p and p not in seen:
        seen.add(p)
        ordered.append(p)
    for mid in _GEMINI_REST_FALLBACKS:
        if mid not in seen:
            seen.add(mid)
            ordered.append(mid)
    return ordered
