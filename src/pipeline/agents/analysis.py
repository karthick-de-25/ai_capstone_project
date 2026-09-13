"""Agent 1 — Report Analysis Agent.

Analyzes a raw clinical report and extracts key findings, abnormal lab
values, and notable observations.  Also provides the ``classify_patient``
``@task`` that the entrypoint uses for conditional routing.
"""

from __future__ import annotations

import logging

from langgraph.func import task
from langgraph.types import RetryPolicy

from src.pipeline.llm import get_llm

log = logging.getLogger(__name__)


@task(retry_policy=RetryPolicy(max_attempts=3))
def analyze_report(report_text: str) -> str:
    """Extract key findings, abnormal lab values, and clinical impressions.

    Returns a structured analysis string.
    """
    log.info("Agent 1: Analyzing report...")
    llm = get_llm()
    prompt = (
        "You are a clinical report analyst. Extract key findings, abnormal lab "
        "values, and notable observations from this report. Be thorough but concise.\n\n"
        f"Report:\n{report_text}"
    )
    result = llm.invoke(prompt)
    log.info("Agent 1: analysis complete (%d chars)", len(result.content))
    return result.content


@task(retry_policy=RetryPolicy(max_attempts=3))
def classify_patient(analysis: str) -> str:
    """Classify severity from the analysis text.

    Returns one of ``"normal"``, ``"abnormal"``, or ``"critical"``.
    """
    llm = get_llm()
    prompt = (
        "Classify this clinical analysis as one word only: normal, abnormal, or critical.\n\n"
        f"Analysis:\n{analysis}"
    )
    label = llm.invoke(prompt).content.strip().lower()
    return label if label in ("normal", "abnormal", "critical") else "abnormal"