"""CLI entry point for the clinical report summarization pipeline.

Usage
-----
    python src/main.py                     # uses hardcoded sample report
    python src/main.py --report <file>     # reads report from a text file

Requires one of these in the environment (or in a ``.env`` file at the project root):

- ``OPENROUTER_API_KEY`` (preferred)
- ``OPENAI_API_KEY`` (fallback)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Make the project root importable when running  python src/main.py
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from dotenv import load_dotenv
from langgraph.types import Command

from src.pipeline.contracts import PipelineInput
from src.pipeline.pipeline import pipeline

SAMPLE_REPORT = """Patient: John Doe, M/45
Date: 2026-03-15

Lab Results:
- Glucose (fasting): 180 mg/dL (high, normal: 70-110)
- HbA1c: 8.2% (high, target: <7%)
- LDL: 160 mg/dL (high, target: <100)
- HDL: 35 mg/dL (low, target: >40)
- Blood Pressure: 145/92 mmHg (Stage 2 hypertension)

Assessment: Uncontrolled type 2 diabetes with hyperlipidemia and hypertension.
Current medications: Metformin 1000mg BID, Atorvastatin 20mg QD.
"""


def _load_report(path: str) -> str:
    """Read report text from a file."""
    return Path(path).read_text(encoding="utf-8")


def run_pipeline(report_text: str) -> None:
    """Run the pipeline, handle interrupts, and print results."""
    thread_id = "cli-patient-001"
    cfg = {"configurable": {"thread_id": thread_id}}

    # First pass — runs until interrupt (or completes)
    chunks = list(pipeline.stream(
        PipelineInput(report_text=report_text),
        cfg,
    ))

    # Check if we hit an interrupt
    for c in chunks:
        if isinstance(c, dict) and "__interrupt__" in c:
            payload = c["__interrupt__"][0].value
            print("\n" + "=" * 60)
            print("  HUMAN REVIEW REQUIRED")
            print("=" * 60)

            if payload.get("level") == "critical":
                print("[CRITICAL ALERT] Severe abnormalities detected!")
                print(f"  Analysis: {payload.get('analysis', '')[:200]}...\n")
                approved = _prompt_yes_no("Proceed with summary?")
            else:
                print(f"  Question: {payload.get('question', '')}")
                print(f"  Summary preview: {payload.get('summary', '')[:200]}...\n")
                approved = _prompt_yes_no("Approve recommendations?")

            # Loop through multiple interrupts (critical path has 2)
            result = pipeline.invoke(
                Command(resume={"approved": approved}),
                cfg,
            )
            while isinstance(result, dict) and "__interrupt__" in result:
                result = pipeline.invoke(
                    Command(resume={"approved": approved}),
                    cfg,
                )
            break
    else:
        # No interrupt — normal classification early return
        result = chunks[-1] if chunks else {}

    # Print results
    print("\n" + "=" * 60)
    print("  PIPELINE RESULTS")
    print("=" * 60)
    _print_result(result)


def _prompt_yes_no(question: str) -> bool:
    """Prompt user for yes/no and return boolean."""
    while True:
        answer = input(f"\n{question} (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please enter 'y' or 'n'.")


def _print_result(result: dict) -> None:
    """Pretty-print the pipeline output."""
    analysis = result.get("analysis", "")
    summary = result.get("summary", "")
    recommendations = result.get("recommendations", [])

    if analysis:
        print(f"\n--- Analysis ({len(analysis)} chars) ---")
        print(analysis[:300])
    if summary:
        print(f"\n--- Summary ({len(summary)} chars) ---")
        print(summary[:300])
    if recommendations:
        print(f"\n--- Recommendations ({len(recommendations)} items) ---")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

    if not analysis and not summary and not recommendations:
        print("(empty result)")


def main() -> None:
    """Parse args — loads ``.env`` file first, then runs the pipeline."""
    load_dotenv()  # read .env from project root

    parser = argparse.ArgumentParser(
        description="AI Clinical Report Summarization Pipeline",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Path to a clinical report text file (optional — uses sample if omitted)",
    )
    args = parser.parse_args()

    if not os.environ.get("OPENROUTER_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        print(
            "Error: neither OPENROUTER_API_KEY nor OPENAI_API_KEY is set.\n"
            "  Create a .env file with OPENROUTER_API_KEY=sk-...",
            file=sys.stderr,
        )
        sys.exit(1)

    report_text = _load_report(args.report) if args.report else SAMPLE_REPORT
    run_pipeline(report_text)


if __name__ == "__main__":
    main()