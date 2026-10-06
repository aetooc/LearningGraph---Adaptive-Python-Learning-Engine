# Frontend screenshots

From the project root, with Docker Compose and lesson generation working:

```bash
uv run scripts/capture_frontend.py
```

The script opens the real React UI in an isolated browser, creates a fresh Alice
demo learner, generates one lesson, submits one answer, and waits for the
backend's progress/study-plan refresh. It saves three PNGs here and inserts them
into the main README only after the complete capture succeeds.

It uses an installed Chromium, Chrome, or Brave when available. To install a
Playwright browser instead:

```bash
uv run --with playwright python -m playwright install chromium
uv run scripts/capture_frontend.py
```

Use `--headed` to watch the capture or `--url http://localhost:5174` for a
different frontend port. Each run creates its own learner and makes one live
lesson request; an incorrect answer also requests feedback. Existing learner
progress is preserved.

Generated files: `01-study-plan.png`, `02-lesson-and-practice.png`, and
`03-feedback-and-progress.png`. Review the images before committing them.
