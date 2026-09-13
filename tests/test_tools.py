"""Tests for clinical calculation tools and report parsing.

All pure Python assertions — no API key or external deps needed.
"""

from __future__ import annotations

from src.pipeline.agents.analysis import _compute_tools_from_report
from src.pipeline.tools.clinical import (
    calculate_bmi,
    calculate_eGFR,
    classify_bmi,
    classify_blood_pressure,
)


class TestBMI:
    def test_golden_numbers(self):
        assert calculate_bmi(85, 1.75) == 27.8
        assert calculate_bmi(70, 1.80) == 21.6
        assert calculate_bmi(50, 1.60) == 19.5

    def test_zero_guard(self):
        assert calculate_bmi(0, 1.75) == 0.0
        assert calculate_bmi(85, 0) == 0.0

    def test_classification(self):
        assert classify_bmi(16.0) == "underweight"
        assert classify_bmi(21.6) == "normal"
        assert classify_bmi(27.8) == "overweight"
        assert classify_bmi(32.0) == "obese"
        assert classify_bmi(0) == "invalid"


class TestEGFR:
    def test_golden_numbers(self):
        assert calculate_eGFR(1.1, 45, "M") == 77
        assert calculate_eGFR(0.9, 35, "F") == 76

    def test_monotonic(self):
        """Higher creatinine → lower eGFR."""
        assert calculate_eGFR(2.0, 60, "M") < calculate_eGFR(1.0, 60, "M")

    def test_gender_factor(self):
        """Female gets 0.742 multiplier → lower eGFR."""
        assert calculate_eGFR(1.0, 25, "F") < calculate_eGFR(1.0, 25, "M")

    def test_guards(self):
        assert calculate_eGFR(1.0, 17, "M") == 0.0  # age < 18
        assert calculate_eGFR(0, 45, "M") == 0.0  # Cr <= 0


class TestBPClassification:
    def test_all_stages(self):
        cases = [
            (115, 75, "normal"),
            (125, 79, "elevated"),
            (125, 80, "stage_1_hypertension"),
            (135, 85, "stage_1_hypertension"),
            (150, 95, "stage_2_hypertension"),
            (185, 120, "hypertensive_crisis"),
        ]
        for sys, dia, expected in cases:
            assert classify_blood_pressure(sys, dia) == expected

    def test_invalid(self):
        assert classify_blood_pressure(0, 75) == "invalid"
        assert classify_blood_pressure(120, 0) == "invalid"


class TestReportParsing:
    """_compute_tools_from_report extracts values and returns tool blocks."""

    def test_all_tools_triggered(self):
        """Report with all data fields triggers BMI + eGFR + BP."""
        report = "Patient: John, M/45\nWeight: 85kg, Height: 1.75m\nCreatinine: 1.1\nBP: 145/92"
        block = _compute_tools_from_report(report)
        assert "BMI" in block
        assert "eGFR" in block
        assert "BP classification" in block

    def test_partial_data(self):
        """BP-only report triggers only BP tool."""
        report = "Patient: Jane\nBP: 120/80"
        block = _compute_tools_from_report(report)
        assert "BMI" not in block
        assert "eGFR" not in block
        assert "BP classification" in block

    def test_no_tool_data(self):
        """Report without tool data returns empty string."""
        block = _compute_tools_from_report("Glucose: 180 mg/dL")
        assert block == ""

    def test_height_cm_conversion(self):
        """Height > 3 is assumed to be cm and converted to meters."""
        report = "Patient: A\nWeight: 70 kg\nHeight: 165 cm"
        block = _compute_tools_from_report(report)
        assert "BMI" in block
        assert "25" in block  # 70 / (1.65^2) ≈ 25.7

    def test_embedded_age_gender(self):
        """M/45 or F/30 in patient line is parsed for age and gender."""
        report = "Patient: Bob, M/60\nCreatinine: 1.2"
        block = _compute_tools_from_report(report)
        assert "eGFR" in block
        assert "age=60" in block