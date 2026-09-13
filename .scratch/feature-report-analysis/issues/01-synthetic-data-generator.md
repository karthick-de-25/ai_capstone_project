# 01 — Create synthetic clinical report data generator

**Type:** task
**Status:** open

## Description

Create a Python script that generates realistic synthetic clinical reports with configurable abnormalities. Each report should look like a real lab results document.

## Requirements

- Generate patient demographics (name, age, gender)
- Generate lab results with configurable normal/abnormal/critical values
- Include at least: glucose, HbA1c, LDL, HDL, blood pressure
- Support templates: `normal`, `abnormal`, `critical`
- Output: plain text string and optionally a PDF file

## File location

`src/data/synthetic/report_generator.py`

## Dependencies

- None (pure Python)

## Acceptance

```python
report = generate_report(variant="critical")
assert "glucose" in report.lower()
assert "180" in report or "high" in report
```