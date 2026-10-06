# Adaptive Python Learning Engine

A small FastAPI backend for learning Python fundamentals. Eleven concepts form a controlled prerequisite graph stored in PostgreSQL. The application tracks each learner's progress and recommends a concept using an inspectable, deterministic algorithm.

An LLM drafts short lessons, examples, three multiple-choice questions, and explanations of diagnosed mistakes. Generated content is parsed into Pydantic models, checked against application rules, and saved before it is used. A minimal React + TypeScript + Vite frontend demonstrates the learner flow; Swagger at `/docs` provides API documentation.

This portfolio project demonstrates REST APIs, relational modeling, graph traversal, transactions, and structured LLM integration within a modular monolith. It deliberately uses a simple learner model that can be explained in an interview.

**Build verification:** see [VERIFICATION.md](VERIFICATION.md). The Python lockfile is present; full frontend build, browser flow, and API/PostgreSQL checks remain pending in the restricted agent environment.

## Why it exists

LLMs are useful for drafting educational material, while progression benefits from reproducible rules. Given the same curriculum, mastery scores, and threshold, this backend returns the same recommendation. A provider failure cannot rewrite grading or erase a committed attempt.

## Architecture

```mermaid
flowchart TD
    Client[React frontend / Swagger] --> API[FastAPI]
    API --> Planner[Deterministic planner]
    Graph[Concepts + prerequisite edges] --> Planner
    Mastery[Learner mastery] --> Planner
    Planner --> Next[Next concept / study plan]
    API --> Generation[Lesson generation service]
    Next --> Generation
    Generation --> LLM[OpenAI or Groq structured output]
    LLM --> Validation[Pydantic + application validation]
    Validation --> Lesson[Persist lesson + questions]
    API --> Attempt[Answer submission]
    Lesson --> Grading[Compare with stored answer key]
    Attempt --> Grading
    Grading --> Transaction[Commit attempt + mastery update]
    Transaction --> Mastery
    Transaction --> Mistake[Structured misconception diagnosis]
    Mistake --> Feedback[LLM feedback / deterministic fallback]
```

The deterministic system controls curriculum, prerequisite eligibility, study plans, recommendation, grading against stored answer keys, misconception lookup, mastery, and progression. The LLM drafts educational content and explains mistakes; it has no database access and never updates progress.

Code is split into `app/api/` for HTTP, `app/services/` for focused logic, `app/db/` for database setup and seeding, `app/graph.py` for traversal, and two readable files for models and schemas. There are no repository layers or generic service hierarchies.

`frontend/` contains five small React components, a typed native-fetch client, and plain CSS. It reads recommendations, availability, mastery, correctness, and feedback from the backend. It only formats scores as percentages and manages form/loading state; no grading, mastery formula, prerequisite traversal, or planning algorithm exists in TypeScript. Vite proxies `/api/*` requests to FastAPI, using a [standard Vite proxy](https://vite.dev/config/server-options#server-proxy).

## Key engineering decisions

**PostgreSQL rather than Neo4j.** The graph has eleven nodes and thirteen edges. A join table plus application traversal is enough, and the same database holds progress and attempts transactionally. Neo4j could help if graph operations become substantially more complex.

**The LLM does not choose the next lesson.** Kahn's topological-sort algorithm uses a heap: whenever multiple nodes are ready, the smallest slug is processed first. A concept is eligible only if its score is below the threshold and every prerequisite's score meets it. The first eligible concept in that ordering is recommended. Mastered roots are excluded. A cycle is rejected during seeding and traversal.

**Structured outputs and validation.** The [official OpenAI SDK's Pydantic parsing helper](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses) supplies the schema. `services/llm.py` makes calls; `services/validation.py` checks content; `services/generation.py` orchestrates one validation retry. An invalid second draft returns `502` and persists nothing. Provider failures return a clean `502`; missing configuration returns `503`. SDK transport retries are disabled.

`LLM_PROVIDER` selects `openai` (default) or `groq`. Groq uses the same SDK and validation pipeline at its [OpenAI-compatible Responses endpoint](https://console.groq.com/docs/responses-api). Set `GROQ_API_KEY` and `GROQ_MODEL` for Groq; OpenAI uses `OPENAI_API_KEY` and `OPENAI_MODEL`. The selected provider's credentials are used explicitly, and model names remain configuration values.

Validation checks nonempty content, the requested concept slug, exactly three questions, exactly four distinct options, valid answer indices, and exactly one misconception tag per incorrect option. Misconceptions use a list of `{option_index, tag}` objects in the strict generation schema and a JSON mapping in storage. Learner-facing lesson schemas expose question IDs, prompts, snippets, and options. They omit answer keys and misconception mappings; the submitted question's grading information is returned after submission.

**Educational correctness is a limitation.** Structural validation does not establish that an explanation, answer key, or misconception is educationally correct. Grading is deterministic against the stored, LLM-drafted answer key. Human review and content evaluation would be future work.

**Multiple choice.** Comparing an option index allows deterministic grading and misconception lookup. Python snippets are display text; the application never executes them.

**Simple mastery.** An unseen score is `0.00`. A distinct correct submission adds `0.10`; an incorrect submission subtracts `0.05`; the result is clamped to `[0, 1]`. Attempts always increase, including an incorrect answer at zero. Decimal arithmetic and `NUMERIC(3, 2)` keep the threshold boundary exact. The default threshold is `0.70`. Three correct answers yield only `0.30`, so learners can generate additional sets for the same concept. This is an architecture demonstration, not a scientifically validated knowledge-tracing model.

**Transactions and duplicate protection.** A learner-row lock serializes their submissions, including the first attempt when no mastery row exists. An attempt and its mastery update commit together. A database uniqueness constraint on `(learner_id, question_id)` prevents repeated grading; duplicates return `409` before any feedback call. Feedback runs after commit, and any provider or parsing failure returns fallback feedback with the saved attempt. Questions belong to the learner whose lesson generated them.

**uv.** One `pyproject.toml` and a generated `uv.lock` describe the environment used locally and in Docker. uv manages Python, dependencies, and command execution. No separate dependency workflow is needed for the container.

## Data model

| Table | Purpose |
|---|---|
| `learners` | Name, fixed Python Fundamentals goal, creation time |
| `concepts` | Controlled concept slug, name, description |
| `prerequisites` | Composite-key edge: concept depends on prerequisite |
| `learner_mastery` | Composite-key learner/concept score, count, update time |
| `lessons` | Generated content belonging to a learner and concept |
| `questions` | Ordered options, private answer key and misconception mapping |
| `attempts` | One immutable grading result per learner/question pair |

Foreign keys preserve relationships. Check constraints bound scores and option indices. Four small Alembic revisions build the schema; application startup does not use `create_all`.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/learners` | Create a learner; optional goal must be `Python Fundamentals` |
| GET | `/learners` | List existing learners for the frontend selector |
| GET | `/learners/{id}` | Read learner |
| GET | `/concepts` | Curriculum with prerequisite IDs |
| GET | `/concepts/{id}` | Read concept |
| GET | `/learners/{id}/progress` | All scores, including unseen concepts at zero |
| GET | `/learners/{id}/study-plan` | Mastered, available, locked, recommended next |
| GET | `/learners/{id}/next-concept` | Recommendation and explicit completion flag |
| POST | `/learners/{id}/lessons/generate` | Generate and store a validated three-question set |
| GET | `/lessons/{id}` | Learner-facing lesson without private grading metadata |
| POST | `/attempts` | Grade once, update mastery, explain an incorrect answer |

When all concepts are mastered, plan endpoints return `completed: true` and `recommended_next: null`. Lesson generation returns `409` without calling the LLM. Unknown resources return `404`; invalid requests return `422`. An unseeded curriculum returns `503` for learning operations.

## Run locally

Install uv and Docker. Use Python 3.12 or newer; `.python-version` selects 3.12. All configuration comes from environment variables; the app does not read environment files automatically.

```bash
cd LearningGraph
export DATABASE_URL='postgresql+psycopg://learning:learning@localhost:5433/learning'
export OPENAI_API_KEY='your-key'
export OPENAI_MODEL='your-available-structured-output-model'
export MASTERY_THRESHOLD='0.70'
uv sync
docker compose up -d db
uv run alembic upgrade head
uv run python -m app.db.seed
uv run uvicorn app.main:app --reload
```

Open <http://localhost:8000/docs>. Creating learners, inspecting the curriculum, and planning do not require an API key. Lesson generation requires the configured model to support Structured Outputs. Feedback can fall back when generation is unavailable.

Opening <http://localhost:8000/> redirects to Swagger at `/docs`.

For Groq, replace the two OpenAI exports with:

```bash
export LLM_PROVIDER='groq'
export GROQ_API_KEY='your-groq-key'
export GROQ_MODEL='your-available-strict-structured-output-model'
```

Choose a Groq model supporting strict Structured Outputs, such as `openai/gpt-oss-20b` or `openai/gpt-oss-120b`; confirm availability in your account and the [supported-model list](https://console.groq.com/docs/structured-outputs). A Groq key is not an OpenAI key.

The seed script is idempotent: it inserts missing curriculum rows and preserves existing learner progress. It checks the whole stored graph for cycles within its transaction.

To run the React frontend alongside that backend, in another terminal:

```bash
cd LearningGraph/frontend
npm install
npm run build
npm run dev
```

Open <http://localhost:5173>. Node 22.12+ is required; Docker uses Node 24. `npm install` creates `package-lock.json`, which should be included in version control. Direct dependencies use the versions from the current official Vite React TypeScript template. Registry access was unavailable in the agent environment, so a frontend lockfile could not be generated there.

The browser-facing API base URL defaults to `/api`; set `VITE_API_BASE_URL` to change it. `API_PROXY_TARGET` selects the actual backend address and defaults locally to `http://127.0.0.1:8000`:

```bash
API_PROXY_TARGET=http://127.0.0.1:8000 npm run dev
```

Keep the default `/api` browser base for this backend: the proxy keeps requests on the frontend's origin and avoids CORS configuration. Absolute browser API URLs require that destination to allow the frontend origin. Provider keys belong only in the backend environment, never in `VITE_*` variables.

## Run with Docker

The image installs dependencies from `uv.lock`. With OpenAI credentials exported:

```bash
export OPENAI_API_KEY='your-key'
export OPENAI_MODEL='your-available-structured-output-model'
docker compose up --build
```

If your `.env` is in `/home/aetooc/Project/.env`, use it explicitly from the `LearningGraph/` directory. For Groq, put these settings in that file:

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-key
GROQ_MODEL=your-available-strict-structured-output-model
```

```bash
cd /home/aetooc/Project/LearningGraph
docker compose --env-file ../.env up --build -d
docker compose --env-file ../.env logs --tail=100 api
```

Compose uses that file for configuration and forwards the selected provider settings to the API; the file is not copied into the image. The application itself still reads process environment variables. The non-root runtime user owns both `/app` and uv's cache, including files created during the image build.

If lesson generation fails, the UI reports the provider error category: rejected
API key, denied model access, missing model, rejected structured-output request,
rate limit/quota, connection failure, timeout, or provider outage. The API logs
the provider, upstream HTTP status, and SDK exception type without logging
credentials, provider response bodies, or generated answer keys. A 400/422
indicates a rejected request; check model support and investigate the request
before treating it as a temporary outage.

After editing provider settings, recreate the API container; `restart` alone
does not load changed environment variables. For the existing host DB port 5437:

```bash
POSTGRES_PORT=5437 docker compose --env-file ../.env up --build -d api
```

Retry **Generate Lesson** in the UI, then inspect the diagnostic line:

```bash
docker compose --env-file ../.env logs --no-color --tail=50 api
```

If the error names **OpenAI** while you configured Groq, the running API has
selected OpenAI. An exported shell variable takes precedence over `--env-file`,
and an existing container retains its old environment. Select Groq explicitly,
recreate the API, and wait for database/API health checks:

```bash
export LLM_PROVIDER=groq
export GROQ_MODEL=openai/gpt-oss-20b
POSTGRES_PORT=5437 docker compose --env-file ../.env up -d --force-recreate --wait api
docker compose exec -T api printenv LLM_PROVIDER GROQ_MODEL
```

The check should print `groq` and `openai/gpt-oss-20b`; it does not print API
keys. `printenv` only checks the existing container; it does not apply settings.
Retry **Generate Lesson** once the API is healthy. If startup fails or the check
says the service is not running, capture the failure before retrying:

```bash
docker compose ps -a
docker compose logs --no-color --tail=80 api db
```

Compose runs PostgreSQL, FastAPI, and the React frontend. The frontend image checks TypeScript and builds the bundle, then serves the demo with Vite. It waits for the API health check. Open **<http://localhost:5173> for the learner UI**, or <http://localhost:8000/docs> for Swagger. `FRONTEND_PORT` can change the frontend host port; the API stays on port 8000. In Docker, `/api` proxies to `http://api:8000`; this internal address is never sent to the browser.

PostgreSQL is exposed on `127.0.0.1:5433` by default, so it can coexist with another database on host port `5432`. The API connects to `db:5432` inside Docker. Set `POSTGRES_PORT` to change the host port; local commands and the demo script must use the matching port in `DATABASE_URL`.

Compose starts PostgreSQL, waits for its health check, then runs migrations, seeds the curriculum, and starts the API. `Dockerfile` installs runtime dependencies with `uv sync --locked --no-dev`; it copies neither keys nor environment files. Data persists in a named PostgreSQL volume. To seed again explicitly:

```bash
docker compose exec api uv run --no-sync python -m app.db.seed
```

## Tests

```bash
uv run pytest
```

Fast tests use SQLite, with foreign keys enabled, and mocked LLM calls. They cover traversal, threshold checks, deterministic recommendations, decimal mastery, draft validation, retries, grading, misconception lookup, uniqueness, atomic rollback, feedback failure, completion, and API answer-key visibility. No real API key is needed.

An optional PostgreSQL test runs migrations in a temporary schema and exercises concurrent duplicate submissions and distinct answers. It drops only that test schema afterward:

```bash
docker compose up -d db
export TEST_DATABASE_URL='postgresql+psycopg://learning:learning@localhost:5433/learning'
uv run pytest -m postgres
```

Use a development database whose user may create schemas. SQLite tests do not prove PostgreSQL row-lock behavior; the opt-in test checks that boundary explicitly.

## Example user flow

Starting state: seeded curriculum, two newly created learners, no mastery rows. Both start at zero and receive `variables`.

The complete learner flow is available in the React UI without Swagger:

1. Open <http://localhost:5173> and create Alice, or choose her in the existing-learner selector.
2. Read her recommended concept, progress percentages, and available/locked concepts, all loaded from FastAPI.
3. Click **Generate lesson / practice set** to load a lesson, examples, and three questions. No answer keys or misconception mappings are included in the lesson response.
4. Choose an option and click **Submit answer**. The server's correct/incorrect result, updated mastery, and personalized feedback appear under that question.
5. The UI automatically reads fresh progress and the study plan after recording the answer. Answer another question or generate another set; mastered concepts change the recommendation according to the backend planner.

Submitted questions are disabled in the current lesson. Duplicate responses are handled without recalculating mastery. If progress cannot refresh after a saved answer, the recorded result stays visible and **Refresh** retries the read. The completion state comes from the backend and disables generation. Switching learners clears the displayed lesson and cancels obsolete reads.

The requests below remain useful for inspecting the same API directly:

```bash
curl -X POST http://localhost:8000/learners \
  -H 'Content-Type: application/json' -d '{"name":"Alice"}'
curl -X POST http://localhost:8000/learners \
  -H 'Content-Type: application/json' -d '{"name":"Bob"}'
```

Use the IDs returned by those requests. For a fresh database they are 1 and 2:

```bash
curl http://localhost:8000/learners/1/study-plan
curl http://localhost:8000/learners/2/study-plan
curl -X POST http://localhost:8000/learners/1/lessons/generate
```

In Swagger, submit one correct answer using its question ID and option index. Alice's score becomes `0.10`. Submit a different question incorrectly: the deterministic comparison selects a misconception and reduces her score to `0.05`; structured feedback explains it. The request shape is:

```json
{"learner_id": 1, "question_id": 1, "selected_option_index": 0}
```

Actual generated question IDs and correct indices vary; this JSON shows the request format. Resubmitting an answered question returns `409` and leaves the score unchanged. Alice's recommendation remains `variables` until she reaches the threshold.

For a repeatable automated demonstration against the running application:

```bash
uv run python -m scripts.demo
```

The developer script creates fresh Alice and Bob, prints its HTTP requests, generates live lessons, and submits one correct and one incorrect answer followed by seven additional distinct correct answers. It reads private answer keys directly from the local database to select these demonstration answers; answer keys are never added to learner-facing lesson APIs. `DATABASE_URL` must point to the API's database. The run makes three lesson requests and one feedback request to the configured provider.

Alice ends with eight correct answers and one incorrect answer: `8 × 0.10 − 0.05 = 0.75`, nine attempts, and recommendation `data-types`. Bob stays at `0.00` and receives `variables`. Both recommendations come exclusively from the graph and recorded progress. The API integration test repeats this flow with a mocked provider.

## Trade-offs and future work

This MVP trusts learner IDs and is intended for a local portfolio demo. Feedback is returned with the submission response rather than stored. Lesson structure is validated, but educational quality is not certified. Each extra set contains new question records; repeated question text across sets is possible.

The frontend keeps lessons and submission results in memory for the current session. Learners, attempts, and mastery persist in PostgreSQL; after a page refresh, select the learner and generate a fresh practice set. The Vite container is a local demo server, not a separate production hosting design.

Future work could evaluate and review generated content, introduce instructor-authored material and graph versions, improve question types, and research more sophisticated learner models. These are deliberately unimplemented. Authentication, code execution, distributed infrastructure, and retrieval systems are outside the MVP.
