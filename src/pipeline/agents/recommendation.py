"""Agent 3 — Recommendation Agent.

Generates 3–5 actionable follow-up recommendations based on the analysis
and summary.  Only runs after the human-in-the-loop checkpoint approves.
"""

from __future__ import annotations

import logging

from langgraph.func import task
from langgraph.types import RetryPolicy

from src.pipeline.llm import get_llm

log = logging.getLogger(__name__)


@task(retry_policy=RetryPolicy(max_attempts=3))
def generate_recommendations(analysis: str, summary: str) -> list[str]:
    """Generate 3–5 actionable follow-up recommendations.

    Returns a list of strings, each being one specific action item.
    Falls back to ``["Unable to generate recommendations"]`` if parsing
    produces nothing.
    """
    log.info("Agent 3: Generating recommendations...")
    llm = get_llm()
    prompt = (
        "You are a clinical recommendation specialist. Based on the analysis "
        "and summary below, provide 3–5 actionable follow-up recommendations, "
        "one per line prefixed with '-':\n\n"
        f"Analysis:\n{analysis}\n\nSummary:\n{summary}"
    )
    raw = llm.invoke(prompt).content
    recs = [
        line.strip().lstrip("- ").strip()
        for line in raw.strip().splitlines()
        if line.strip()
    ]
    result = recs[:5] or ["Consult with a specialist."]
    log.info("Agent 3: %d recommendations generated", len(result))
    return result