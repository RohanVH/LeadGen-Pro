"""Production LLM calls: OpenAI official SDK + Google Gemini REST (v1beta generateContent), strict timeouts and logging."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from openai import OpenAI

from app.core.config import Settings

logger = logging.getLogger(__name__)

# Hard cap per user spec (production); raise or fallback at boundary.
AI_REQUEST_TIMEOUT_SEC = 10.0


def _openai_client(settings: Settings) -> OpenAI:
    base = (settings.openai_base_url or "").strip()
    kwargs: dict[str, Any] = {
        "api_key": settings.openai_api_key,
        "timeout": AI_REQUEST_TIMEOUT_SEC,
        # Single HTTP attempt per call so asyncio's 10s cap matches "hard timeout" semantics.
        "max_retries": 0,
    }
    if base:
        kwargs["base_url"] = base.rstrip("/")
    return OpenAI(**kwargs)


def openai_chat_completion_sync(
    settings: Settings,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 1200,
) -> str:
    """Blocking OpenAI chat; raises on API/timeout errors."""
    client = _openai_client(settings)
    model = settings.openai_model
    logger.info("Using OpenAI for chat (model=%s)", model)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as first_exc:
        err_txt = str(first_exc)
        if "max_tokens" in err_txt or "max_completion_tokens" in err_txt:
            logger.warning("OpenAI chat retry with max_completion_tokens: %s", err_txt[:500])
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                )
            except Exception as retry_exc:
                logger.error("AI OPENAI CHAT ERROR (retry): %s", retry_exc, exc_info=True)
                raise
        else:
            logger.error("AI OPENAI CHAT ERROR: %s", first_exc, exc_info=True)
            raise
    content = response.choices[0].message.content
    if not content or not str(content).strip():
        raise ValueError("OpenAI returned empty message content")
    return str(content).strip()


def openai_chat_completion_json_analyze_sync(
    settings: Settings,
    system_text: str,
    user_text: str,
    *,
    temperature: float = 0.35,
) -> str:
    """Blocking OpenAI chat with JSON object format for lead analyze."""
    client = _openai_client(settings)
    model = settings.openai_model
    logger.info("Using OpenAI for analyze (model=%s)", model)
    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    try:
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=messages,
            temperature=temperature,
        )
    except Exception as first_exc:
        err_txt = str(first_exc)
        if "max_tokens" in err_txt or "max_completion_tokens" in err_txt:
            logger.warning("OpenAI analyze retry with max_completion_tokens: %s", err_txt[:500])
            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=messages,
                temperature=temperature,
                max_completion_tokens=4096,
            )
        else:
            logger.error("AI OPENAI ANALYZE ERROR: %s", first_exc, exc_info=True)
            raise
    content = response.choices[0].message.content
    if not content or not str(content).strip():
        raise ValueError("OpenAI analyze returned empty content")
    return str(content).strip()


def gemini_generate_content_v1_sync(
    api_key: str,
    model_id: str,
    prompt_text: str,
    *,
    response_mime_json: bool = False,
) -> str:
    """
    Gemini REST generateContent.

    Google currently serves ``gemini-1.5-flash`` (and similar) on the **v1beta** surface; the plain ``v1`` URL often
    returns 404 for the same model id, and ``v1`` rejects JSON ``generationConfig`` fields that v1beta accepts.

    Request shape matches the public API: ``contents`` → ``parts`` → ``text``; response:
    ``candidates[0].content.parts[0].text``.
    """
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_id}:generateContent?key={api_key}"
    )
    body: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ],
    }
    if response_mime_json:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "temperature": 0.35,
        }
    else:
        body["generationConfig"] = {"temperature": 0.65, "maxOutputTokens": 2048}

    logger.info("Using Gemini (v1beta REST, model=%s)", model_id)
    with httpx.Client(timeout=AI_REQUEST_TIMEOUT_SEC) as client:
        response = client.post(url, json=body)
        if response.status_code >= 400:
            logger.error(
                "GEMINI HTTP ERROR model=%s status=%s body=%s",
                model_id,
                response.status_code,
                response.text[:1200],
            )
            raise ValueError(
                f"Gemini generateContent HTTP {response.status_code} for model {model_id!r}"
            ) from None
        data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        logger.error("GEMINI empty candidates: %s", data)
        raise ValueError("Gemini returned no candidates")
    parts = ((candidates[0].get("content") or {}).get("parts")) or []
    if not parts:
        logger.error("GEMINI empty parts: %s", data)
        raise ValueError("Gemini returned empty parts")
    text = parts[0].get("text") or ""
    if not str(text).strip():
        raise ValueError("Gemini returned empty text")
    return str(text).strip()


def gemini_chat_flat_v1_sync(
    api_key: str,
    model_id: str,
    system_prompt: str,
    openai_style_history: list[dict[str, str]],
    latest_user: str,
) -> str:
    """Single v1 generateContent call with system + transcript + latest user (no JSON mode)."""
    chunks: list[str] = [system_prompt.strip(), "\n\nConversation:\n"]
    for m in openai_style_history:
        role = (m.get("role") or "user").lower()
        label = "Assistant" if role == "assistant" else "User"
        chunks.append(f"{label}: {(m.get('content') or '').strip()}\n")
    chunks.append(f"User: {latest_user.strip()}\n\nReply as the assistant. Be concise and specific to this lead.")
    prompt = "".join(chunks)[:48000]
    return gemini_generate_content_v1_sync(
        api_key,
        model_id,
        prompt,
        response_mime_json=False,
    )


async def run_sync_with_ai_timeout(func, /, *args, **kwargs) -> Any:
    """Run blocking func in a thread pool with strict wall-clock timeout."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(func, *args, **kwargs),
            timeout=AI_REQUEST_TIMEOUT_SEC,
        )
    except asyncio.TimeoutError:
        logger.error(
            "AI TIMEOUT after %s seconds for %s",
            AI_REQUEST_TIMEOUT_SEC,
            getattr(func, "__name__", str(func)),
        )
        raise TimeoutError(f"AI request exceeded {AI_REQUEST_TIMEOUT_SEC}s") from None
