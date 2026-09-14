"""Flask app for the clinical report summarization demo UI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import flask

# Make the project root importable
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from dotenv import load_dotenv

from src.data.synthetic.report_generator import generate_report
from src.ui.state import (
    extract_clinical_metrics,
    get_thread,
    resume_thread,
    start_thread,
)

load_dotenv()

_DEMO_REPORTS = {
    "normal": {
        "label": "🟢 Normal — Early Exit",
        "explanation": (
            "All labs within range. The <strong>classifier</strong> labels this "
            "<em>normal</em>, so the pipeline <em>skips</em> the Summary and "
            "Recommendation agents — demonstrating <strong>conditional routing</strong>."
        ),
    },
    "abnormal": {
        "label": "🟡 Abnormal — Full Pipeline",
        "explanation": (
            "Elevated glucose, HbA1c, LDL; low HDL. The classifier labels this "
            "<em>abnormal</em>, so the full pipeline runs: Analysis → Summary → "
            "<strong>HITL approval</strong> → Recommendations. The summary includes "
            "a <em>Trend vs Previous</em> section when multi-report chaining is used."
        ),
    },
    "critical": {
        "label": "🔴 Critical — Alert + Full Pipeline",
        "explanation": (
            "Life-threatening values. The classifier labels this <em>critical</em>, "
            "triggering a <strong>critical alert interrupt</strong>. After approval, "
            "the pipeline continues through Summary → Recommendations, with another "
            "HITL checkpoint before recommendations."
        ),
    },
}


def _has_api_key() -> bool:
    """Check if any supported API key is configured."""
    return bool(os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def create_app() -> flask.Flask:
    """Create and configure the Flask application."""
    app = flask.Flask(__name__)
    app.secret_key = "demo-secret-key-change-in-production"

    # ── Routes ──────────────────────────────────────────────────────

    @app.route("/", methods=["GET"])
    def index():
        """Landing page with report input form."""
        return flask.render_template(
            "index.html",
            has_api_key=_has_api_key(),
        )

    @app.route("/run", methods=["POST"])
    def run_pipeline():
        """Submit a report and start the pipeline.

        Redirects to ``/status/<thread_id>`` so the user can see
        progress and respond to any interrupts.
        """
        if not _has_api_key():
            return flask.render_template(
                "index.html",
                error="No API key configured. Set <code>OPENROUTER_API_KEY</code> in your <code>.env</code> file.",
                has_api_key=False,
            )
        report_text = flask.request.form.get("report_text", "").strip()
        previous_summary = flask.request.form.get("previous_summary", "").strip() or None
        if not report_text:
            return flask.render_template("index.html", error="Please enter a report.", has_api_key=_has_api_key())

        thread_id = start_thread(report_text, previous_summary)
        return flask.redirect(flask.url_for("status", thread_id=thread_id))

    @app.route("/status/<thread_id>", methods=["GET"])
    def status(thread_id: str):
        """Show current pipeline state for a thread.

        If the pipeline is paused at an interrupt, display the
        interrupt payload with approve/reject buttons.
        If complete, display the results.
        """
        ts = get_thread(thread_id)
        if ts is None:
            return flask.render_template("index.html", error=f"Unknown thread: {thread_id}", has_api_key=_has_api_key())

        # Extract clinical metrics from analysis text (for the summary card)
        metrics = {}
        if ts.output and ts.output.get("analysis"):
            metrics = extract_clinical_metrics(ts.output["analysis"])

        return flask.render_template(
            "status.html",
            ts=ts,
            metrics=metrics,
        )

    @app.route("/synthetic", methods=["GET"])
    def synthetic():
        """Return a synthetic report for the given variant.

        Query params:
          variant  — ``normal``, ``abnormal``, or ``critical`` (default ``abnormal``)
          seed     — optional integer for reproducible output
          raw      — if ``1``, return plain text (for XHR); else return HTML page
        """
        variant = flask.request.args.get("variant", "abnormal")
        if variant not in ("normal", "abnormal", "critical"):
            variant = "abnormal"

        seed_str = flask.request.args.get("seed")
        seed = int(seed_str) if seed_str and seed_str.isdigit() else None

        report_text = generate_report(variant, seed=seed)

        if flask.request.args.get("raw") == "1":
            return report_text, 200, {"Content-Type": "text/plain; charset=utf-8"}

        return flask.render_template("index.html", report_text=report_text, has_api_key=_has_api_key())

    @app.route("/resume/<thread_id>", methods=["POST"])
    def resume(thread_id: str):
        """Resume a paused pipeline after an interrupt."""
        approved = flask.request.form.get("approved", "no").strip().lower() in ("yes", "y", "1", "true")
        error = resume_thread(thread_id, approved)
        if error:
            return flask.redirect(flask.url_for("status", thread_id=thread_id, error=error))
        return flask.redirect(flask.url_for("status", thread_id=thread_id))

    @app.route("/demo", methods=["GET"])
    def demo():
        """Guided demo tour page showing all three classification paths."""
        return flask.render_template(
            "demo.html",
            reports=_DEMO_REPORTS,
            has_api_key=_has_api_key(),
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=5000)