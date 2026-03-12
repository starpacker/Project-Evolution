"""
Shared LLM utility functions.
Used by both ReflectionTool and IntelligenceTool to avoid code duplication.
Uses OpenAI-compatible API gateway.
Supports both plain chat and function-calling (tools) modes.

v0.2.1: Added retry with exponential backoff, timeout, and log sanitization.
"""

import json
import logging
import time
from typing import Optional, List, Dict, Any

logger = logging.getLogger("evolution.utils.llm")

# ── Constants ────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0        # seconds
RETRY_MAX_DELAY = 16.0        # seconds
DEFAULT_TIMEOUT = 60.0         # seconds per API call

# Module-level client cache
_client = None


def _sanitize_for_log(text: str, max_len: int = 200) -> str:
    """Truncate and mask sensitive content before logging."""
    if not text:
        return ""
    sanitized = text[:max_len]
    if len(text) > max_len:
        sanitized += "...[truncated]"
    return sanitized


def _get_client():
    """Lazy-init OpenAI client with gateway config."""
    global _client
    if _client is None:
        from openai import OpenAI
        from evolution.config.settings import LLM_API_KEY, LLM_BASE_URL

        if not LLM_API_KEY:
            logger.error("[LLM] No LLM_API_KEY configured")
            return None
        _client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            timeout=DEFAULT_TIMEOUT,
        )
    return _client


def reset_client():
    """Reset cached client (useful for testing)."""
    global _client
    _client = None


def _retry_with_backoff(func, max_retries: int = MAX_RETRIES):
    """Execute *func* with exponential backoff on transient failures.

    Returns the result of *func* on success, or None after all retries
    are exhausted.
    """
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exc = e
            err_str = str(e).lower()
            # Non-retryable errors — fail fast
            if any(kw in err_str for kw in (
                "authentication", "invalid api key", "unauthorized",
                "not found", "invalid model",
            )):
                logger.error(f"[LLM] Non-retryable error: {e}")
                return None

            delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
            logger.warning(
                f"[LLM] Attempt {attempt}/{max_retries} failed: {_sanitize_for_log(str(e))}. "
                f"Retrying in {delay:.1f}s …"
            )
            time.sleep(delay)

    logger.error(f"[LLM] All {max_retries} retries exhausted. Last error: {last_exc}")
    return None


def call_claude_api(
    prompt: str = "",
    max_tokens: int = 8192,
    system: str = None,
    messages: list = None,
) -> Optional[str]:
    """Call LLM via OpenAI-compatible API (plain chat mode).

    Returns response text or None on failure.

    Args:
        prompt: 用户消息（单轮模式）
        max_tokens: 最大 token 数
        system: 系统提示词
        messages: 多轮消息列表（如果提供，忽略 prompt 参数）
    """
    try:
        from evolution.config.settings import LLM_MODEL, LLM_TEMPERATURE

        client = _get_client()
        if client is None:
            return None

        if messages is not None:
            final_messages = []
            if system:
                final_messages.append({"role": "system", "content": system})
            final_messages.extend(messages)
        else:
            final_messages = []
            if system:
                final_messages.append({"role": "system", "content": system})
            final_messages.append({"role": "user", "content": prompt})

        def _do_call():
            response = client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=max_tokens,
                temperature=LLM_TEMPERATURE,
                messages=final_messages,
            )
            return response.choices[0].message.content

        result = _retry_with_backoff(_do_call)
        return result

    except ImportError:
        logger.error("[LLM] openai package not installed")
        return None
    except Exception as e:
        logger.error(f"[LLM] Unexpected error in call_claude_api: {_sanitize_for_log(str(e))}")
        return None


def call_llm_with_tools(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    system: str = None,
    max_tokens: int = 2048,
) -> Optional[Dict[str, Any]]:
    """Call LLM with OpenAI function-calling (tools) support.

    Args:
        messages: 对话消息列表
        tools: OpenAI tools 定义列表
        system: 系统提示词
        max_tokens: 最大 token 数

    Returns:
        dict with keys:
            "content": str | None
            "tool_calls": list | None
            "raw_message": 原始 message 对象
        或 None（调用失败 / 网关不支持 tools 时）
    """
    try:
        from evolution.config.settings import LLM_MODEL, LLM_TEMPERATURE

        client = _get_client()
        if client is None:
            return None

        final_messages = []
        if system:
            final_messages.append({"role": "system", "content": system})
        final_messages.extend(messages)

        kwargs = dict(
            model=LLM_MODEL,
            max_tokens=max_tokens,
            temperature=LLM_TEMPERATURE,
            messages=final_messages,
        )

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        def _do_call():
            return client.chat.completions.create(**kwargs)

        response = _retry_with_backoff(_do_call)
        if response is None:
            return None

        msg = response.choices[0].message

        # Parse tool_calls
        parsed_tool_calls = None
        if msg.tool_calls:
            parsed_tool_calls = []
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {}
                parsed_tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": args,
                })

        return {
            "content": msg.content,
            "tool_calls": parsed_tool_calls,
            "raw_message": msg,
        }

    except Exception as e:
        err_str = str(e).lower()
        # If the gateway simply doesn't support the tools parameter, fall back
        if "tool" in err_str or "function" in err_str:
            logger.info("[LLM] Gateway may not support tools param — falling back to plain chat")
        else:
            logger.error(f"[LLM] API error (with tools): {_sanitize_for_log(str(e))}")
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
