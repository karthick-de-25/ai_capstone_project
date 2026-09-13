"""Pipeline data contracts.

LangGraph 1.x uses a decorator style: ``@entrypoint`` functions receive a
single input object and return a single output object. Task functions exchange
plain values between themselves. These TypedDicts define the public data
surface of the pipeline and are used as type hints in every node.

Field names intentionally align with ``agent.md`` and the feature specs in
``.scratch/`` (report_text, analysis, summary, recommendations).
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class PipelineInput(TypedDict):
    """What enters the pipeline: one raw clinical report.

    ``previous_summary`` is optional — set it when chaining multiple
    reports for the same patient to enable cross-report memory.
    """

    report_text: str
    previous_summary: NotRequired[str | None]


class PipelineOutput(TypedDict):
    """What the pipeline produces: analysis → summary → recommendations."""

    analysis: str
    summary: str
    recommendations: list[str]