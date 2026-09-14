# Issue 04: Results Display + Synthetic Report Loader

**Type:** task
**Status:** resolved

## Goal

Display pipeline results in a readable format and allow generating synthetic reports from the UI.

## Files

| File | Action | Lines |
|------|--------|-------|
| `src/ui/app.py` | edit | ~30 |
| `src/ui/templates/index.html` | edit | ~50 |
| `src/ui/templates/status.html` | edit | ~20 |

## Done

- `/synthetic` GET endpoint generates synthetic reports (normal/abnormal/critical) and pre-fills the form
- `raw=1` query param returns plain text for XHR
- Results page shows Analysis, Summary, Recommendations in styled sections
- Summary of pipeline flow (Analysis → Classification → Summary → Recommendations)