"""
gemini_client.py
=================
Thin wrapper around the Gemini API using the current `google-genai` SDK.

NOTE: the older `google-generativeai` package is deprecated (Google has
ended support for it) — this project uses the replacement `google-genai`
package instead. Every other module calls `generate()` here rather than
touching the SDK directly, so there is exactly one place that knows about
API keys, model names, and SDK details.

Environment variables (see .env.example):
    GEMINI_API_KEY   - required. Get one free at https://aistudio.google.com/apikey
    GEMINI_MODEL     - optional, defaults to "gemini-3.6-flash"
"""

import os
from google import genai
from google.genai import types

_client = None


class GeminiNotConfigured(RuntimeError):
    """Raised when GEMINI_API_KEY is missing or empty."""
    pass


def _get_client():
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise GeminiNotConfigured(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key "
            "(https://aistudio.google.com/apikey)."
        )
    _client = genai.Client(api_key=api_key)
    return _client


def generate(prompt: str, json_mode: bool = False) -> str:
    """
    Send a single prompt to Gemini and return the plain text response.

    Args:
        prompt:    the full prompt text.
        json_mode: if True, asks the model to return raw JSON
                   (response_mime_type="application/json") — used by the
                   NLU extraction layer so the caller never has to
                   regex-parse free-text output.

    Raises:
        GeminiNotConfigured: if GEMINI_API_KEY is missing.
    """
    client = _get_client()
    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash").strip()
    config = types.GenerateContentConfig(response_mime_type="application/json") if json_mode else None

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )
    return response.text or ""


def is_configured() -> bool:
    """Cheap check used by callers that want to fail gracefully without
    raising (e.g. to fall back to a template-based reply)."""
    return bool(os.environ.get("GEMINI_API_KEY", "").strip())
