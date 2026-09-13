"""Clinical calculation tools for the Report Analysis Agent.

Each function is a pure computation with a clear docstring — designed to
be used as a tool by ``create_react_agent`` (LangGraph prebuilt).  The
LLM reads the docstring to decide when to invoke the tool.

All calculations return floats and accept basic numeric/string inputs.
"""

from __future__ import annotations


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculate Body Mass Index from weight (kg) and height (m).

    Formula: weight / height².

    Classification (WHO standard):
    - <18.5  → underweight
    - 18.5–24.9 → normal
    - 25.0–29.9 → overweight
    - ≥30.0  → obese

    Parameters
    ----------
    weight_kg : float
        Patient weight in kilograms.
    height_m : float
        Patient height in meters.

    Returns
    -------
    float
        BMI rounded to 1 decimal place.
    """
    if weight_kg <= 0 or height_m <= 0:
        return 0.0
    return round(weight_kg / (height_m**2), 1)


def classify_bmi(bmi: float) -> str:
    """Classify a BMI value into a WHO weight category.

    Parameters
    ----------
    bmi : float
        Body Mass Index value.

    Returns
    -------
    str
        One of ``"underweight"``, ``"normal"``, ``"overweight"``,
        ``"obese"``, or ``"invalid"``.
    """
    if bmi <= 0:
        return "invalid"
    if bmi < 18.5:
        return "underweight"
    if bmi < 25.0:
        return "normal"
    if bmi < 30.0:
        return "overweight"
    return "obese"


def calculate_eGFR(creatinine: float, age: int, gender: str) -> float:
    """Estimate Glomerular Filtration Rate using the MDRD formula.

    Indicates kidney function.  Lower values mean worse function.

    Formula (MDRD):
      eGFR = 186 × (creatinine⁻¹·¹⁵⁴) × (age⁻⁰·²⁰³)
             × 0.742 (if female)

    CKD stages:
    - ≥90          → Stage 1 (normal)
    - 60–89        → Stage 2 (mild)
    - 30–59        → Stage 3 (moderate)
    - 15–29        → Stage 4 (severe)
    - <15          → Stage 5 (kidney failure)

    Parameters
    ----------
    creatinine : float
        Serum creatinine in mg/dL (range ~0.4-10.0).
    age : int
        Patient age in years (≥18).
    gender : str
        ``"M"`` or ``"F"``.

    Returns
    -------
    float
        eGFR rounded to nearest integer (mL/min/1.73m²).
    """
    if creatinine <= 0 or age < 18:
        return 0.0

    egfr = 186.0 * (creatinine ** -1.154) * (age ** -0.203)

    if gender.upper() == "F":
        egfr *= 0.742

    return round(egfr)


def classify_blood_pressure(systolic: float, diastolic: float) -> str:
    """Classify blood pressure reading into AHA/ACC stages.

    Parameters
    ----------
    systolic : float
        Systolic pressure in mmHg.
    diastolic : float
        Diastolic pressure in mmHg.

    Returns
    -------
    str
        One of ``"normal"``, ``"elevated"``, ``"stage_1_hypertension"``,
        ``"stage_2_hypertension"``, ``"hypertensive_crisis"``, or
        ``"invalid"``.
    """
    if systolic <= 0 or diastolic <= 0:
        return "invalid"

    if systolic >= 180 or diastolic >= 120:
        return "hypertensive_crisis"
    if systolic >= 140 or diastolic >= 90:
        return "stage_2_hypertension"
    if systolic >= 130 or diastolic >= 80:
        return "stage_1_hypertension"
    if systolic >= 120:
        return "elevated"
    return "normal"