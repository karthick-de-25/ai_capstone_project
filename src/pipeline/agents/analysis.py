"""Agent 1 — Report Analysis Agent.

Analyzes a raw clinical report and extracts key findings, abnormal lab
values, and notable observations.  Before calling the LLM, it scans the
report text for numeric values (weight, height, creatinine, BP) and
computes clinical metrics (BMI, eGFR, BP classification) using the
``src.pipeline.tools`` library.  These computed values are injected into
the LLM prompt so the analysis always includes them.

Also provides the ``classify_patient`` ``@task`` for conditional routing.
"""

from __future__ import annotations

import logging
import re

from langgraph.func import task
from langgraph.types import RetryPolicy

from src.pipeline.llm import get_llm
from src.pipeline.tools.clinical import (
    calculate_bmi,
    classify_bmi,
    calculate_eGFR,
    classify_blood_pressure,
)

log = logging.getLogger(__name__)


# ── Report parsing helpers ──────────────────────────────────────────


def _parse_float(pattern: str, text: str) -> float | None:
    """Return the first float match for *pattern* in *text*, or ``None``."""
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except (ValueError, IndexError):
            return None
    return None


def _compute_tools_from_report(report_text: str) -> str:
    """Scan the report for numeric values and compute clinical metrics.

    Returns a text block to inject into the LLM prompt, or an empty
    string if no tool-triggering data is found.
    """
    lines: list[str] = []

    # --- BMI ---
    weight = _parse_float(
        r"(?:weight|Weight)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:kg|kgs)?",
        report_text,
    )
    height = _parse_float(
        r"(?:height|Height)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:m|meters?|cm)?",
        report_text,
    )
    # Convert cm to m (if value > 3, it's likely cm)
    if height is not None and height > 3:
        height = height / 100

    if weight is not None and weight > 0 and height is not None and height > 0:
        bmi = calculate_bmi(weight, height)
        cat = classify_bmi(bmi)
        lines.append(
            f"[Tool] BMI: {bmi} ({cat}) — "
            f"computed from weight={weight}kg, height={height}m"
        )

    # --- eGFR ---
    cr = _parse_float(
        r"(?:creatinine|Cr)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:mg/dL)?",
        report_text,
    )

    # Age: standalone "age: XX" or embedded in patient line "M/45"
    age = _parse_float(r"(?:age|Age)\s*[:\-]?\s*(\d+)", report_text)
    if age is None:
        age = _parse_float(r"[MF]/(\d+)", report_text)  # e.g. "M/45"

    # Gender: explicit field or embedded "M/45" / "F/30"
    gender_m = re.search(
        r"(?:gender|sex|Sex)\s*[:\-]?\s*(M(?:ale)?|F(?:emale)?)",
        report_text,
        re.IGNORECASE,
    )
    if gender_m is None:
        gender_m = re.search(r"\b([MF])/\d+", report_text)

    if cr is not None and cr > 0 and age is not None and age >= 18 and gender_m:
        g = gender_m.group(1).upper()[0]  # "M" or "F"
        egfr = calculate_eGFR(cr, int(age), g)
        lines.append(
            f"[Tool] eGFR: {egfr} mL/min/1.73m² — "
            f"computed from Cr={cr}, age={int(age)}, gender={g}"
        )

    # --- BP classification ---
    bp = re.search(
        r"(?:BP|Blood\s*Pressure)\s*[:\-]?\s*(\d+)\s*[/]\s*(\d+)",
        report_text,
        re.IGNORECASE,
    )
    if bp:
        sys_val, dia_val = int(bp.group(1)), int(bp.group(2))
        stage = classify_blood_pressure(sys_val, dia_val)
        lines.append(
            f"[Tool] BP classification: {stage} — "
            f"computed from {sys_val}/{dia_val} mmHg"
        )

    return "\n".join(lines)


# ── Agent 1 ─────────────────────────────────────────────────────────


@task(retry_policy=RetryPolicy(max_attempts=3))
def analyze_report(report_text: str) -> str:
    """Extract key findings, abnormal lab values, and clinical impressions.

    Scans the report for tool-triggering values (weight, height, Cr, BP)
    and computes clinical metrics (BMI, eGFR, BP stage) before calling
    the LLM.  Tool results are injected into the prompt so the analysis
    always incorporates them.
    """
    log.info("Agent 1: Analyzing report...")

    # Compute tool results from raw report data
    tool_block = _compute_tools_from_report(report_text)
    if tool_block:
        log.info("Tool results computed:\n%s", tool_block)

    llm = get_llm()
    prompt = (
        "You are a clinical report analyst. Extract key findings, abnormal lab "
        "values, and notable observations from this report. Be thorough but concise."
    )
    if tool_block:
        prompt += (
            f"\n\nPre-computed clinical metrics (include these in your analysis):\n"
            f"{tool_block}"
        )
    prompt += f"\n\nReport:\n{report_text}"

    result = llm.invoke(prompt)
    log.info("Agent 1: analysis complete (%d chars)", len(result.content))
    return result.content


# ── Classifier ──────────────────────────────────────────────────────


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