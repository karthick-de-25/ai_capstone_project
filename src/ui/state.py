"""In-memory state manager for the demo UI.

Maps ``thread_id`` → ``ThreadState`` so that pipeline execution state
survives across HTTP requests.  LangGraph interrupts require resuming
with ``Command(resume=...)``, which means we need to store the thread
configuration and re-enter the pipeline on the next request.

Only one state manager instance exists (module-level singleton).
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Literal

from langgraph.types import Command

from src.pipeline.contracts import PipelineInput, PipelineOutput
from src.pipeline.pipeline import pipeline

# ── Public types ───────────────────────────────────────────────────

Status = Literal["running", "interrupt", "complete", "error"]


@dataclass
class ThreadState:
    """Per-thread execution state for the demo UI."""

    thread_id: str
    report_text: str
    previous_summary: str | None = None
    status: Status = "running"
    interrupt_payload: dict | None = None
    output: PipelineOutput | None = None
    error: str | None = None
    config: dict | None = None
    current_step: str = "initial"  # initial | analysis | classification | summary | recommendations | done


# ── Clinical metrics extraction ────────────────────────────────────


def extract_clinical_metrics(analysis_text: str) -> dict[str, str]:
    """Parse ``[Tool]`` lines from the analysis text.

    Returns a dict like ``{"BMI": "27.8 (overweight)", "eGFR": "...", "BP": "..."}``.
    """
    metrics: dict[str, str] = {}
    for m in re.finditer(r"\[Tool\]\s*(.+?):\s*(.+)", analysis_text):
        key = m.group(1).strip()
        val = m.group(2).strip()
        metrics[key] = val
    return metrics


# ── State manager ──────────────────────────────────────────────────

_threads: dict[str, ThreadState] = {}
_THREAD_ID_PREFIX = "demo"


def _next_thread_id() -> str:
    """Generate a short unique thread ID."""
    return f"{_THREAD_ID_PREFIX}-{uuid.uuid4().hex[:6]}"


def _run_until_interrupt_or_done(
    ts: ThreadState,
    resume_value: dict | None = None,
) -> None:
    """Advance the pipeline for *ts* until an interrupt or completion.

    On the first call (``resume_value`` is ``None``) the pipeline is
    started with ``pipeline.stream()``.  Subsequent calls (resuming after
    an interrupt) use ``pipeline.invoke(Command(resume=...))``.

    Mutates *ts* in place.
    """
    cfg = ts.config or {"configurable": {"thread_id": ts.thread_id}}
    ts.config = cfg

    inp = PipelineInput(
        report_text=ts.report_text,
        previous_summary=ts.previous_summary,
    )

    if resume_value is None:
        # First invocation: analysis is about to run
        ts.current_step = "analysis"
        for chunk in pipeline.stream(inp, cfg):
            if _detect_interrupt(chunk, ts):
                _set_step_from_interrupt(ts)
                return
        # No interrupt — pipeline completed normally
        ts.current_step = "done"
        ts.output = _extract_output(cfg, inp) or PipelineOutput(
            analysis="", summary="", recommendations=[]
        )
        ts.status = "complete"
    else:
        _resume_and_continue(ts, resume_value, cfg)


def _detect_interrupt(chunk: object, ts: ThreadState) -> bool:
    """Check if *chunk* is an interrupt; if so, store payload and return True."""
    if isinstance(chunk, dict) and "__interrupt__" in chunk:
        ts.interrupt_payload = chunk["__interrupt__"][0].value
        ts.status = "interrupt"
        return True
    return False


def _set_step_from_interrupt(ts: ThreadState) -> None:
    """Set ``current_step`` based on the interrupt payload type."""
    payload = ts.interrupt_payload or {}
    if payload.get("level") == "critical":
        ts.current_step = "summary"  # summary is next after critical alert
    elif payload.get("question"):
        ts.current_step = "recommendations"  # recommendations are next
    else:
        ts.current_step = "analysis"


def _extract_output(cfg: dict, inp: PipelineInput) -> PipelineOutput | None:
    """Run ``pipeline.invoke()`` to get the final output (no interrupts case)."""
    result = pipeline.invoke(inp, cfg)
    if isinstance(result, dict) and "analysis" in result:
        return PipelineOutput(
            analysis=result.get("analysis", ""),
            summary=result.get("summary", ""),
            recommendations=result.get("recommendations", []),
        )
    return None


def _resume_and_continue(
    ts: ThreadState,
    resume_value: dict,
    cfg: dict,
) -> None:
    """Resume pipeline after an interrupt, checking for further interrupts."""
    # Mark step based on what's about to run
    payload = ts.interrupt_payload or {}
    if payload.get("level") == "critical":
        ts.current_step = "summary"
    elif payload.get("question"):
        ts.current_step = "recommendations"

    result = pipeline.invoke(Command(resume=resume_value), cfg)

    # Check for another interrupt
    if isinstance(result, dict) and "__interrupt__" in result:
        ts.interrupt_payload = result["__interrupt__"][0].value
        ts.status = "interrupt"
        _set_step_from_interrupt(ts)
        return

    # Check for pipeline output
    if isinstance(result, dict) and "analysis" in result:
        ts.output = PipelineOutput(
            analysis=result.get("analysis", ""),
            summary=result.get("summary", ""),
            recommendations=result.get("recommendations", []),
        )
        ts.current_step = "done"
        ts.status = "complete"
        return

    # Check for interrupt buried inside a dict
    if isinstance(result, dict):
        if "analysis" in result:
            ts.output = PipelineOutput(
                analysis=result.get("analysis", ""),
                summary=result.get("summary", ""),
                recommendations=result.get("recommendations", []),
            )
            ts.current_step = "done"
            ts.status = "complete"
            return
        for _v in result.values():
            if isinstance(_v, list) and len(_v) > 0:
                item = _v[0]
                if hasattr(item, "value") and isinstance(item.value, dict):
                    ts.interrupt_payload = item.value
                    ts.status = "interrupt"
                    _set_step_from_interrupt(ts)
                    return

    # Fallback: treat as complete
    ts.output = PipelineOutput(
        analysis=str(result) if result else "",
        summary="",
        recommendations=[],
    )
    ts.current_step = "done"
    ts.status = "complete"


# ── Public API ─────────────────────────────────────────────────────


def start_thread(
    report_text: str,
    previous_summary: str | None = None,
) -> str:
    """Start a new pipeline thread and return its ``thread_id``.

    The pipeline runs until the first interrupt (or completion).  Call
    ``resume_thread()`` if the thread status is ``"interrupt"``.
    """
    thread_id = _next_thread_id()
    ts = ThreadState(
        thread_id=thread_id,
        report_text=report_text,
        previous_summary=previous_summary,
    )
    _threads[thread_id] = ts

    try:
        _run_until_interrupt_or_done(ts)
    except Exception as exc:
        ts.status = "error"
        ts.error = str(exc)

    return thread_id


def resume_thread(thread_id: str, approved: bool) -> str | None:
    """Resume a paused pipeline thread with an approval decision.

    Returns ``None`` on success, or an error message string on failure.
    """
    ts = _threads.get(thread_id)
    if ts is None:
        return f"Unknown thread: {thread_id}"
    if ts.status != "interrupt":
        return f"Thread {thread_id} is not paused (status: {ts.status})"

    try:
        _run_until_interrupt_or_done(ts, resume_value={"approved": approved})
    except Exception as exc:
        ts.status = "error"
        ts.error = str(exc)
        return str(exc)

    return None


def get_thread(thread_id: str) -> ThreadState | None:
    """Return the thread state, or ``None`` if unknown."""
    return _threads.get(thread_id)