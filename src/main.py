"""CLI entry point for the clinical report summarization pipeline.

Supports multi-report memory chaining — after each run, you can
process another report for the same patient (same ``thread_id``).
The previous summary is passed as context so the Summary Agent can
include a "Trend vs Previous" section.

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
from src.data.synthetic.report_generator import generate_report

SAMPLE_REPORT = """Patient: John Doe, M/45
Date: 2026-03-15
Weight: 85 kg, Height: 1.75 m
BP: 145/92 mmHg

Lab Results:
- Glucose (fasting): 180 mg/dL (high, normal: 70-110)
- HbA1c: 8.2% (high, target: <7%)
- LDL: 160 mg/dL (high, target: <100)
- HDL: 35 mg/dL (low, target: >40)
- Creatinine: 1.1 mg/dL

Assessment: Uncontrolled type 2 diabetes with hyperlipidemia and hypertension.
Current medications: Metformin 1000mg BID, Atorvastatin 20mg QD.
"""

_THREAD_ID = "cli-patient-001"
_next_seed = 1  # for synthetic reports in the loop


def _load_report(path: str) -> str:
    """Read report text from a file."""
    return Path(path).read_text(encoding="utf-8")


def _run_single(report_text: str, previous_summary: str | None = None) -> dict:
    """Run the pipeline once, handle interrupts, return the output dict."""
    cfg = {"configurable": {"thread_id": _THREAD_ID}}

    inp = PipelineInput(
        report_text=report_text,
        previous_summary=previous_summary,
    )

    # First pass — runs until interrupt (or completes)
    chunks = list(pipeline.stream(inp, cfg))

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

    return result


def _prompt_yes_no(question: str) -> bool:
    """Prompt user for yes/no and return boolean."""
    while True:
        answer = input(f"\n{question} (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please enter 'y' or 'n'.")


def _print_result(result: dict) -> str | None:
    """Pretty-print pipeline output and return the summary string."""
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

    return summary


def main() -> None:
    """Parse args — loads ``.env`` file first, then runs the pipeline.

    After each run, prompts the user to chain another report for the
    same patient (same ``thread_id``) to demonstrate cross-report memory.
    """
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="AI Clinical Report Summarization Pipeline",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Path to a clinical report text file (optional — uses sample if omitted)",
    )
    parser.add_argument(
        "--no-loop",
        action="store_true",
        help="Run once without the multi-report memory loop",
    )
    args = parser.parse_args()

    if not os.environ.get("OPENROUTER_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        print(
            "Error: neither OPENROUTER_API_KEY nor OPENAI_API_KEY is set.\n"
            "  Create a .env file with OPENROUTER_API_KEY=sk-...",
            file=sys.stderr,
        )
        sys.exit(1)

    global _next_seed  # noqa: PLW0603

    report_text = _load_report(args.report) if args.report else SAMPLE_REPORT
    previous_summary: str | None = None
    iteration = 1

    while True:
        prefix = f"[Report {iteration}]"
        print(f"\n{'=' * 60}")
        print(f"  {prefix} {'(with memory of previous run)' if previous_summary else ''}")
        print(f"{'=' * 60}")

        result = _run_single(report_text, previous_summary)
        summary = _print_result(result)

        # Normal path: no summary generated → nothing to compare, stop looping
        if not summary:
            print("\n(Normal variant — no summary generated, stopping)")
            break

        # Ask if user wants to continue (unless --no-loop)
        if args.no_loop:
            break

        if not _prompt_yes_no("\nRun another report for same patient?"):
            break

        # Prepare next report: synthetic with next seed
        variant = input("  Variant (normal/abnormal/critical, default=abnormal): ").strip()
        if variant not in ("normal", "abnormal", "critical"):
            variant = "abnormal"

        report_text = generate_report(variant, seed=_next_seed)
        _next_seed += 1
        previous_summary = summary
        iteration += 1

    print("\nDone.")


if __name__ == "__main__":
    main()