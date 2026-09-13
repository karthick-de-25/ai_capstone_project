"""Tests for the 3-agent clinical report summarization pipeline.

All tests use ``FakeListChatModel`` — no API key required.
"""

from __future__ import annotations

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.types import Command

from src.pipeline.contracts import PipelineInput, PipelineOutput
from src.pipeline.llm import inject_llm, reset_llm
from src.pipeline.pipeline import pipeline


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clean_llm():
    """Reset LLM after every test so tests don't leak state."""
    yield
    reset_llm()


def _run(thread_id: str, responses: list[str], input_text: str = "dummy report"):
    """Helper: inject fake LLM, run pipeline, resume with approval, return output.

    Returns the final ``PipelineOutput`` dict, handling the interrupt if one
    occurs.
    """
    fake = FakeListChatModel(responses=responses)
    inject_llm(fake)

    cfg = {"configurable": {"thread_id": thread_id}}
    chunks = list(pipeline.stream(
        PipelineInput(report_text=input_text),
        cfg,
    ))

    # If no interrupt → unwrap from the 'pipeline' key
    has_interrupt = any(
        isinstance(c, dict) and "__interrupt__" in c for c in chunks
    )
    if not has_interrupt:
        final = chunks[-1] if chunks else {}
        return final.get("pipeline", final)

    # Loop: resume with approval until no more interrupts
    result = pipeline.invoke(Command(resume={"approved": True}), cfg)
    while isinstance(result, dict) and "__interrupt__" in result:
        result = pipeline.invoke(Command(resume={"approved": True}), cfg)
    return result


# ── Tests ─────────────────────────────────────────────────────────────


class TestNormalPath:
    """Reports with all values in range → skip summary + recommendations."""

    def test_early_return(self):
        """Normal classification must return only analysis (no summary/recs)."""
        # 2 LLM calls: analyze_report, classify_patient → "normal"
        result = _run(
            "test-normal-001",
            responses=[
                "Key Findings:\n- All values within normal range.",
                "normal",
            ],
        )
        assert result["analysis"]
        assert result["summary"] == ""
        assert result["recommendations"] == []


class TestAbnormalPath:
    """Standard flow: analysis → summary → (interrupt) → recommendations."""

    def test_full_pipeline_with_approval(self):
        """Abnormal report flows through all 3 agents when approved."""
        # 4 LLM calls: analyze, classify("abnormal"), summarize, recommend
        result = _run(
            "test-abnormal-001",
            responses=[
                "Glucose 180 mg/dL, BP 145/92.",
                "abnormal",
                "**Summary:**\n- ⚠️ Glucose: 180 mg/dL\n- ⚠️ BP: 145/92",
                "- Schedule HbA1c.\n- Refer to specialist.",
            ],
        )
        assert result["analysis"]
        assert result["summary"]
        assert len(result["recommendations"]) >= 1

    def test_rejected_recommendations(self):
        """Human rejects → summary preserved, no recommendations."""
        fake = FakeListChatModel(responses=[
            "Glucose 180 mg/dL.",
            "abnormal",
            "**Summary:** glucose elevated.",
        ])
        inject_llm(fake)

        cfg = {"configurable": {"thread_id": "test-abnormal-reject-001"}}
        list(pipeline.stream(
            PipelineInput(report_text="dummy"),
            cfg,
        ))
        result = pipeline.invoke(Command(resume={"approved": False}), cfg)

        assert result["analysis"]
        assert result["summary"]
        assert result["recommendations"] == []


class TestCriticalPath:
    """Life-threatening findings trigger a separate alert interrupt."""

    def test_critical_approved_continues(self):
        """Critical alert approved → continues to summary + recommendations."""
        result = _run(
            "test-critical-001",
            responses=[
                "Glucose 350, BP 200/120.",
                "critical",
                "**Summary:** critical values detected.",
                "- Immediate ER referral.",
            ],
        )
        assert result["analysis"]
        assert result["summary"]
        assert result["recommendations"]

    def test_critical_rejected_stops(self):
        """Critical alert rejected → stops early with only analysis."""
        fake = FakeListChatModel(responses=[
            "Glucose 350, BP 200/120.",
            "critical",
        ])
        inject_llm(fake)

        cfg = {"configurable": {"thread_id": "test-critical-reject-001"}}
        list(pipeline.stream(
            PipelineInput(report_text="dummy"),
            cfg,
        ))
        result = pipeline.invoke(Command(resume={"approved": False}), cfg)

        assert result["analysis"]
        assert result["summary"] == ""
        assert result["recommendations"] == []


class TestOutputContract:
    """PipelineOutput always has the correct shape."""

    def test_output_is_pipelineoutput(self):
        """The result is a dict matching PipelineOutput fields."""
        result = _run(
            "test-contract-001",
            responses=[
                "Normal findings.",
                "normal",
            ],
        )
        assert isinstance(result, dict)
        # All PipelineOutput keys present
        for key in ("analysis", "summary", "recommendations"):
            assert key in result, f"Missing key: {key}"
        # No unexpected keys
        expected = set(PipelineOutput.__annotations__)
        assert set(result.keys()) == expected