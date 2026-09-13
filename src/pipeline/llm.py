"""LLM factory — one place to get the pipeline's language model.

Uses **OpenRouter** as the LLM provider with ``deepseek/deepseek-v4-flash``.

API key resolution (in order):
1. ``OPENROUTER_API_KEY``
2. ``OPENAI_API_KEY`` (fallback)

Swappable for unit tests via ``inject_llm(fake_llm)`` / ``reset_llm()`` so
every agent task is testable without an API key.
"""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

_llm_instance = None


def _resolve_api_key() -> str | None:
    """Return the best available API key."""
    return os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")


def _default_llm() -> ChatOpenAI:
    """Build a ChatOpenAI instance pointed at OpenRouter."""
    api_key = _resolve_api_key()
    return ChatOpenAI(
        model="deepseek/deepseek-v4-flash",
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        temperature=0,
    )


def get_llm() -> ChatOpenAI:
    """Return the shared LLM instance (lazy-initialized)."""
    global _llm_instance  # noqa: PLW0603
    if _llm_instance is None:
        _llm_instance = _default_llm()
    return _llm_instance


def inject_llm(fake_llm: object) -> None:
    """Inject a fake LLM (e.g. ``FakeListChatModel``) for testing.

    Call ``reset_llm()`` after the test to restore the default.
    """
    global _llm_instance  # noqa: PLW0603
    _llm_instance = fake_llm  # type: ignore[assignment]


def reset_llm() -> None:
    """Reset to the default LLM instance.

    Always call this in test teardown after ``inject_llm()``.
    """
    global _llm_instance  # noqa: PLW0603
    _llm_instance = None