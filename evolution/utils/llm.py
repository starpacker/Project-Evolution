"""
Shared LLM utility functions.
Used by both ReflectionTool and IntelligenceTool to avoid code duplication.
Uses OpenAI-compatible API gateway.
"""

import logging
from typing import Optional

logger = logging.getLogger("evolution.utils.llm")

# Module-level client cache
_client = None


def _get_client():
    """Lazy-init OpenAI client with gateway config."""
    global _client
    if _client is None:
        from openai import OpenAI
        from evolution.config.settings import LLM_API_KEY, LLM_BASE_URL

        if not LLM_API_KEY:
            logger.error("[LLM] No LLM_API_KEY configured")
            return None
        _client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    return _client


def reset_client():
    """Reset cached client (useful for testing)."""
    global _client
    _client = None


def call_claude_api(prompt: str, max_tokens: int = 8192, system: str = None) -> Optional[str]:
    """Call LLM via OpenAI-compatible API. Returns response text or None on failure."""
    try:
        from evolution.config.settings import LLM_MODEL, LLM_TEMPERATURE

        client = _get_client()
        if client is None:
            return None

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=LLM_MODEL,
            max_tokens=max_tokens,
            temperature=LLM_TEMPERATURE,
            messages=messages,
        )
        return response.choices[0].message.content
    except ImportError:
        logger.error("[LLM] openai package not installed")
        return None
    except Exception as e:
        logger.error(f"[LLM] API error: {e}")
        return None


def extract_json(text: str) -> str:
    """Extract JSON from LLM output, stripping markdown fences."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start : end + 1]
    return text
