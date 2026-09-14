# Issue 01: Scaffold Flask App, Routes & Templates

**Type:** task
**Status:** resolved
**Blocked by:**

## Goal

Get Flask serving the index page with a report input form. No pipeline integration yet — just the web server skeleton.

## Tasks

1. Add `flask>=3.0` to `requirements.txt`.
2. Create `src/ui/__init__.py` (empty package marker).
3. Create `src/ui/app.py` with a Flask app factory:
   - `create_app()` → `Flask(__name__)`
   - Route `GET /` → renders `index.html`
   - Route `POST /run` → stub that returns `{"status": "not_implemented"}`
4. Create `src/ui/templates/index.html`:
   - Basic HTML5 page
   - Title: "AI Clinical Report Summarization"
   - Big `<textarea>` for report text
   - Submit button labeled "Run Pipeline"
   - Placeholder for displaying status/errors
5. Verify `flask run` starts and the index page renders.

## Files

| File | Action | Est. lines |
|------|--------|------------|
| `requirements.txt` | edit | +1 |
| `src/ui/__init__.py` | create | 0 |
| `src/ui/app.py` | create | ~35 |
| `src/ui/templates/index.html` | create | ~45 |

## Review

- Does `flask run` start without errors?
- Does `GET /` return HTML with a textarea and submit button?
- Does `POST /run` return a JSON response?