"""Pipeline orchestrator — LangGraph 1.x ``@entrypoint``.

Runs the three agents sequentially with conditional routing and a
human-in-the-loop checkpoint before recommendations.
"""

from __future__ import annotations

import logging

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint
from langgraph.types import interrupt

from src.pipeline.agents.analysis import analyze_report, classify_patient
from src.pipeline.agents.recommendation import generate_recommendations
from src.pipeline.agents.summary import generate_summary
from src.pipeline.contracts import PipelineInput, PipelineOutput

log = logging.getLogger(__name__)


@entrypoint(checkpointer=InMemorySaver())
def pipeline(report: PipelineInput) -> PipelineOutput:
    """Orchestrate the 3-agent clinical report summarization pipeline.

    Flow
    ----
    1. ``analyze_report`` — Agent 1 extracts findings from the raw report.
    2. ``classify_patient`` — ``@task`` helper routes by severity.
       - **normal** → return early (skip summary + recommendations).
       - **critical** → ``interrupt()`` for an alert-human checkpoint, then
         optionally continue.
    3. ``generate_summary`` — Agent 2 produces a structured clinical summary
       (includes ``Trend vs Previous`` when ``previous_summary`` is provided).
    4. ``interrupt()`` — human-in-the-loop checkpoint (approve recommendations?).
       - **rejected** → return early.
    5. ``generate_recommendations`` — Agent 3 produces 3–5 action items.

    Returns
    -------
    PipelineOutput
        Always contains the ``analysis`` field.  ``summary`` and
        ``recommendations`` may be empty depending on routing decisions.
    """
    # ── Agent 1 ───────────────────────────────────────────────────────
    analysis = analyze_report(report["report_text"]).result()

    # ── Classifier → conditional routing ──────────────────────────────
    patient_class = classify_patient(analysis).result()
    log.info("Patient classification: %s", patient_class)

    if patient_class == "normal":
        log.info("Normal report — skipping summary and recommendations")
        return PipelineOutput(analysis=analysis, summary="", recommendations=[])

    if patient_class == "critical":
        log.info("Critical report — alerting human")
        alert = interrupt({"level": "critical", "analysis": analysis})
        if not alert.get("approved", False):
            log.info("Human declined critical alert — stopping")
            return PipelineOutput(analysis=analysis, summary="", recommendations=[])

    # ── Agent 2 ───────────────────────────────────────────────────────
    prev = report.get("previous_summary")
    summary = generate_summary(analysis, previous_summary=prev).result()

    # ── Human-in-the-loop checkpoint (gate Agent 3) ──────────────────
    review = interrupt({
        "question": "Approve recommendations?",
        "analysis": analysis,
        "summary": summary,
    })
    if not review.get("approved", False):
        log.warning("Human rejected recommendations — stopping pipeline")
        return PipelineOutput(analysis=analysis, summary=summary, recommendations=[])

    # ── Agent 3 ───────────────────────────────────────────────────────
    recommendations = generate_recommendations(analysis, summary).result()
    log.info(
        "Pipeline complete: %d recommendations",
        len(recommendations),
    )
    return PipelineOutput(
        analysis=analysis,
        summary=summary,
        recommendations=recommendations,
    )