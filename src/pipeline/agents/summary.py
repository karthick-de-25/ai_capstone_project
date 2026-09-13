"""Agent 2 — Summary Agent.

Takes the structured analysis from Agent 1 and produces a concise,
bullet-point clinical summary (3–5 findings).  Abnormal values are
visually marked.
"""

from __future__ import annotations

import logging

from langgraph.func import task
from langgraph.types import RetryPolicy

from src.pipeline.llm import get_llm

log = logging.getLogger(__name__)


@task(retry_policy=RetryPolicy(max_attempts=3))
def generate_summary(analysis: str) -> str:
    """Produce a concise, structured clinical summary (3–5 bullet points).

    Abnormal values should be marked with ``⚠️`` or bold formatting.
    """
    log.info("Agent 2: Generating summary...")
    llm = get_llm()
    prompt = (
        "You are a clinical summary specialist. Produce a concise, structured "
        "summary in 3–5 bullet points covering: Key Findings, Abnormal Values, "
        "and Clinical Impression. Mark abnormal values with ⚠️ or **bold**.\n\n"
        f"Analysis:\n{analysis}"
    )
    result = llm.invoke(prompt)
    log.info("Agent 2: summary complete (%d chars)", len(result.content))
    return result.content