# Verification status

Implementation date: 2026-10-06.

The backend, migrations, required React/TypeScript/Vite frontend, Docker files,
focused tests, README, and developer demo are written. The full definition of
done is **not yet verified**.

## Checks completed

- 47 core pytest cases pass using installed Python 3.14, SQLAlchemy, Pydantic, and settings support.
- Graph seeding is idempotent, produces 11 concepts and 13 edges, and rejects cycles.
- Recorded attempts demonstrate Alice reaching 0.75 after eight correct answers
  and one incorrect answer; Alice is recommended data-types while Bob remains on variables.
- Tests cover prerequisite thresholds, stable ordering, completion, decimal
  arithmetic, validation, one retry, grading, misconception mapping, unique
  attempts, atomic rollback, and fallback feedback preserving committed progress.
- All Python files compile successfully.
- `docker compose config --no-interpolate --quiet` succeeds.
- Groq provider selection, endpoint/key/model forwarding, missing settings,
  SDK failure sanitization, and absent structured outputs pass mocked SDK tests.
- Provider failures distinguish authentication, permissions, missing models,
  rejected requests, rate limits/quota, connection failures, and timeouts. Tests
  verify safe diagnostics exclude SDK messages, credentials, response bodies,
  and generated answer keys. The user's configured Groq model is
  `openai/gpt-oss-20b`; the live provider failure still needs the rebuilt API's
  diagnostic output to identify its cause.
- The user subsequently reported the OpenAI-specific rejected-key message,
  establishing that their running API selected OpenAI despite their intended
  Groq settings. Compose configuration with an explicit `LLM_PROVIDER=groq`
  override and dummy credentials resolves to Groq with the requested model;
  API recreation and successful live generation remain to be confirmed.
- Compose Groq environment forwarding passes a check using dummy credentials.
- Compose exposes PostgreSQL on configurable host port 5433 by default, with
  port 5432 retained inside Docker. Default and overridden port mappings pass
  configuration checks; runtime verification remains pending.
- The user generated `uv.lock` and reported a successful image build and healthy PostgreSQL.
- User-provided startup logs identified root-owned `/tmp/uv-cache` as the API's
  exit-code-2 failure. The Dockerfile now gives the runtime user ownership of
  both `/app` and `/tmp/uv-cache`; restarting the rebuilt image still needs verification.
- Subsequent user-provided logs confirm the rebuilt API is running: all four
  migrations completed, the curriculum was seeded, and Uvicorn started on port
  8000. Requests to `/` returned 404; a redirect from `/` to `/docs` now makes
  the API's documentation discoverable at the base URL. The redirect still
  requires the API image to be rebuilt.
- Ten distinct TypeScript/TSX files pass syntax/transpilation checks using
  TypeScript 6.0.3 bundled with the installed editor. This is not a complete
  dependency-based typecheck or Vite build.
- Native-fetch client contract checks pass with mocked fetch: REST paths and
  JSON bodies, unchanged server grading/mastery values, duplicate error handling,
  network failures, and cancellation. No frontend learning decisions are calculated.
- Three-service Compose configuration passes: PostgreSQL, API, frontend on
  port 5173, API readiness check, `/api` proxy target, configurable DB host port
  (including the user's 5437), and provider keys confined to the backend.
- A learner-list endpoint and its API test are added for selecting existing learners.
  The HTTP test still belongs to the skipped FastAPI module in this environment.

The available-package test command was run through uv, without installing or
modifying the system environment:

```bash
cd /tmp
UV_CACHE_DIR=/tmp/learninggraph-uv-cache \
PYTHONPATH=/home/aetooc/Project/LearningGraph \
uv run --no-project --python /home/aetooc/anaconda3/bin/python3 \
  python -m pytest /home/aetooc/Project/LearningGraph/tests -q -ra
```

Result: **47 passed, 3 skipped**. Two module-level skips are the HTTP API tests
and OpenAPI smoke test because FastAPI is unavailable; the third skip is the
opt-in PostgreSQL test because `TEST_DATABASE_URL` is unset. This result does
not establish that the complete locked application runs.

## Environment blockers

`uv add` and `uv lock`, including elevated attempts, failed because this
workspace could not resolve `pypi.org`. `uv run pytest` also failed when uv tried
to download Python 3.12. Dependencies were initially recorded through
`uv add --frozen`. The user has since generated a real `uv.lock`, which is now
present in the workspace.

Docker daemon access returned permission denied, including an elevated check.
The image build also encountered read-only Docker build-cache directories.
No PostgreSQL runtime, migration execution, row-lock concurrency check, or
live provider request has therefore been verified by the agent here. The user's
reported image build and healthy database establish those steps in their local environment.

Frontend `npm install`, including an elevated attempt, fails with
`EAI_AGAIN registry.npmjs.org`. Consequently `npm run build` reports `tsc: not
found`, and `npm run dev` reports `vite: not found`. A direct backend run reports
that FastAPI is unavailable in the agent's local environment. No browser is
available through the enabled browser-control tools, and the user's local Docker
API remains inaccessible. Neither a frontend lockfile nor a successful live
frontend/backend browser flow was fabricated.

## Remaining acceptance checks

Once network and Docker access are available, from the project directory:

```bash
uv lock
uv sync --locked
uv run pytest
docker compose up -d db
export DATABASE_URL='postgresql+psycopg://learning:learning@localhost:5433/learning'
uv run alembic upgrade head
uv run python -m app.db.seed
uv run python -m app.db.seed
uv run alembic check
export TEST_DATABASE_URL="$DATABASE_URL"
uv run pytest -m postgres
```

Include `uv.lock` in version control. Configure `OPENAI_API_KEY` and
`OPENAI_MODEL`, or `LLM_PROVIDER=groq`, `GROQ_API_KEY`, and `GROQ_MODEL`, then
complete the Docker/live slice. If using the root `.env` from `LearningGraph/`:

```bash
docker compose --env-file ../.env up --build
# In another terminal, with the same provider settings exported:
uv run python -m scripts.demo
```

Fix any failures, verify Swagger and the generated lesson/feedback responses,
and update this report and the README build-status note.

## Required frontend acceptance

From `frontend/`, once npm access is available:

```bash
npm install
npm run build
```

Include the generated `package-lock.json` in version control. Rebuild all three
services so the backend includes `GET /learners`. For the user's existing DB
host mapping and root environment file, from `LearningGraph/`:

```bash
POSTGRES_PORT=5437 docker compose --env-file ../.env up --build -d
docker compose ps -a
docker compose logs --tail=100 frontend api
```

Open <http://localhost:5173>, then manually verify the required flow:

1. Create Alice or select her from the existing-learner list.
2. Check that study plan and mastery load from the actual API.
3. Generate a lesson, inspect its explanation/examples/three questions, and
   confirm the lesson network response omits answer keys and misconception mappings.
4. Submit an answer. Confirm the result and mastery match the API response;
   submit a different question incorrectly to inspect personalized feedback.
5. Confirm fresh progress/study-plan requests run after each saved answer and
   the UI reflects those responses. An answered question should stay disabled.
6. Generate new practice sets until the backend changes Alice's recommendation;
   select Bob and confirm his recommendation reflects his own progress.

Also check a failed generation, a completed learner, and the explicit refresh
path. The browser must never receive provider credentials. Run the full backend
test suite once its dependencies are installed. Stop only when both the backend
acceptance scenario and this frontend flow pass; add no further frontend features.
