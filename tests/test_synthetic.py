"""Tests for the synthetic clinical report generator.

All pure string assertions — no API key or external deps needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.data.synthetic.report_generator import (
    generate_report,
    generate_report_to_file,
)


class TestNormalVariant:
    """Normal reports have no out-of-range flags."""

    def test_no_flags(self):
        report = generate_report("normal", seed=1)
        assert "(high" not in report and "(low" not in report
        assert "within normal range" in report

    def test_lab_sections_present(self):
        report = generate_report("normal", seed=1)
        assert "Lab Results:" in report
        assert "Assessment:" in report
        assert "Current medications:" in report


class TestAbnormalVariant:
    """Abnormal reports have flagged out-of-range values."""

    def test_contains_flags(self):
        report = generate_report("abnormal", seed=7)
        assert "(high" in report or "(low" in report
        assert "Glucose" in report

    def test_medication_present(self):
        report = generate_report("abnormal", seed=7)
        assert "Metformin" in report


class TestCriticalVariant:
    """Critical reports flag life-threatening values."""

    def test_life_threatening_marker(self):
        report = generate_report("critical", seed=3)
        assert "LIFE-THREATENING" in report
        assert "ICU" in report or "immediate" in report.lower()

    def test_all_values_flagged(self):
        """Every lab value in a critical report is flagged."""
        report = generate_report("critical", seed=3)
        flag_count = report.count("(high") + report.count("(low")
        assert flag_count >= 5, f"Expected >=5 flagged labs, got {flag_count}"


class TestReproducibility:
    """Same seed produces identical reports."""

    def test_deterministic_output(self):
        a = generate_report("abnormal", seed=42)
        b = generate_report("abnormal", seed=42)
        assert a == b

    def test_different_seeds_differ(self):
        a = generate_report("normal", seed=1)
        b = generate_report("normal", seed=2)
        # Names or ages should differ
        assert a != b


class TestFileOutput:
    """Writing to file produces the same text."""

    def test_write_to_file(self, tmp_path: Path):
        path = tmp_path / "report.txt"
        text = generate_report_to_file(str(path), "normal", seed=5)
        assert Path(path).exists()
        written = Path(path).read_text(encoding="utf-8")
        assert text == written
        assert "Patient:" in written


class TestEdgeCases:
    """Edge-case handling."""

    def test_invalid_variant_fallback(self):
        """An unknown variant should use 'normal' defaults."""
        report = generate_report("unknown_variant")  # type: ignore[arg-type]
        assert "(high" not in report and "(low" not in report