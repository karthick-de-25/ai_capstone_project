"""Synthetic clinical report generator.

Generates realistic-but-fabricated patient reports with configurable
abnormality levels.  Includes weight, height, and combined BP values
that trigger the pipeline's clinical tooling (BMI, eGFR, BP stage).

Pure Python — no dependencies beyond the standard library.
"""

from __future__ import annotations

import random
from typing import Literal

Variant = Literal["normal", "abnormal", "critical"]

# ── Patient name pool ────────────────────────────────────────────────
_FIRST_NAMES = [
    "Jane Smith", "John Doe", "Maria Garcia", "James Wilson",
    "Emily Chen", "Robert Patel", "Sarah Thompson", "David Kim",
    "Linda Brown", "Michael Davis",
]

# ── Vitals (triggers the BMI + BP tools) ──────────────────────────
# weight_kg, height_m, (systolic, diastolic)
_VITALS: dict[Variant, tuple[float, float, tuple[int, int]]] = {
    "normal":   (70, 1.75, (115, 75)),    # BMI 22.9 → normal, BP normal
    "abnormal": (85, 1.75, (145, 92)),    # BMI 27.8 → overweight, BP stage 2
    "critical": (100, 1.75, (200, 120)),  # BMI 32.7 → obese, BP crisis
}

# ── Lab value templates ──────────────────────────────────────────────
# Each entry: (display_name, unit, (normal_min, normal_max), values_by_variant)
LabDef = tuple[str, str, tuple[float, float], dict[Variant, float]]

_LABS: list[LabDef] = [
    (
        "Glucose (fasting)", "mg/dL", (70, 110),
        {"normal": 92, "abnormal": 180, "critical": 350},
    ),
    (
        "HbA1c", "%", (4.0, 5.6),
        {"normal": 5.2, "abnormal": 8.2, "critical": 11.5},
    ),
    (
        "LDL", "mg/dL", (0, 99),
        {"normal": 85, "abnormal": 160, "critical": 220},
    ),
    (
        "HDL", "mg/dL", (40, 60),
        {"normal": 52, "abnormal": 35, "critical": 28},
    ),
    (
        "Creatinine", "mg/dL", (0.6, 1.2),
        {"normal": 0.9, "abnormal": 1.5, "critical": 2.8},
    ),
]

# ── Assessment templates ─────────────────────────────────────────────
_ASSESSMENTS: dict[Variant, str] = {
    "normal": "All lab values within normal range. Patient appears healthy.",
    "abnormal": (
        "Uncontrolled type 2 diabetes with hyperlipidemia and "
        "hypertension. Medication adjustment recommended."
    ),
    "critical": (
        "LIFE-THREATENING: Severe hyperglycemia, hypertensive crisis, "
        "and acute kidney injury risk. Immediate medical intervention required."
    ),
}

# ── Medication templates ─────────────────────────────────────────────
_MEDICATIONS: dict[Variant, str] = {
    "normal": "None",
    "abnormal": "Metformin 1000mg BID, Atorvastatin 20mg QD, Lisinopril 10mg QD",
    "critical": "IV insulin, IV fluids, ICU monitoring required",
}


def _format_range(lo: float, hi: float) -> str:
    """Format a lab range, stripping unnecessary trailing zeros."""
    def _fmt(v: float) -> str:
        s = f"{v:.1f}"
        return s.rstrip("0").rstrip(".")
    return f"{_fmt(lo)}-{_fmt(hi)}"


def _flag(value: float, lo: float, hi: float) -> str:
    """Return a flag suffix for out-of-range values."""
    if value > hi:
        return f"  (high, normal: {_format_range(lo, hi)})"
    if value < lo:
        return f"  (low, normal: {_format_range(lo, hi)})"
    return ""


def generate_report(
    variant: Variant = "normal",
    seed: int | None = None,
) -> str:
    """Generate a synthetic clinical report.

    The report includes ``Weight``, ``Height``, and a combined ``BP``
    line so that the pipeline's ``_compute_tools_from_report`` can
    extract them and compute BMI, eGFR, and BP stage.

    Parameters
    ----------
    variant:
        Severity level — ``"normal"``, ``"abnormal"``, or ``"critical"``.
    seed:
        Random seed for reproducible output (optional).

    Returns
    -------
    str
        A plain-text clinical report.
    """
    if variant not in ("normal", "abnormal", "critical"):
        variant = "normal"

    if seed is not None:
        random.seed(seed)

    patient_name = random.choice(_FIRST_NAMES)
    age = random.randint(25, 75)
    gender = random.choice(["M", "F"])

    weight, height, (sys_bp, dia_bp) = _VITALS[variant]

    lines = [
        f"Patient: {patient_name}, {gender}/{age}",
        f"Date: 2026-03-15",
        f"Weight: {weight:.0f} kg, Height: {height:.2f} m",
        f"BP: {sys_bp}/{dia_bp} mmHg",
        "",
        "Lab Results:",
    ]

    for name, unit, (nlo, nhi), values in _LABS:
        val = values[variant]
        flag = _flag(val, nlo, nhi)
        lines.append(f"- {name}: {val:.1f} {unit}{flag}")

    lines.append("")
    lines.append("Assessment:")
    lines.append(f"  {_ASSESSMENTS[variant]}")
    lines.append("")
    lines.append(f"Current medications: {_MEDICATIONS[variant]}")

    return "\n".join(lines)


def generate_report_to_file(
    path: str,
    variant: Variant = "normal",
    seed: int | None = None,
) -> str:
    """Generate a report and write it to ``path``.

    Returns the report text (same as ``generate_report``).
    """
    text = generate_report(variant, seed)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return text