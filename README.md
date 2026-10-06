# Adaptive Python Learning Engine

A small app for learning Python through short lessons and multiple-choice practice. Create a learner, see which concepts are available, and work through the recommended topic. Each answer updates progress and refreshes the study plan.

I kept the learning rules in the backend. Groq or OpenAI generates lessons and feedback; FastAPI handles prerequisites, recommendations, grading, and mastery. The React frontend displays the results returned by the API.

Built with **Python, FastAPI, PostgreSQL, SQLAlchemy, React, TypeScript, and Vite**. Database migrations use Alembic, and Python dependencies are managed with uv.

<!-- frontend-screenshots:start -->
## Screenshots

### 1. Study plan

Alice starts with Variables. The plan shows her progress, the next recommended concept, and the topics that are still locked.

![Alice's study plan and recommended Python concept](docs/screenshots/01-study-plan.png)

### 2. Lesson and practice

Each lesson includes an explanation, examples, and three questions with four options each.

![Generated Python lesson and multiple-choice practice](docs/screenshots/02-lesson-and-practice.png)

### 3. Answer result

This answer was correct, bringing Alice's mastery to 10%. After a submission, the app reloads progress and the study plan. Incorrect answers also receive feedback about the mistake.

![Correct answer and updated learner progress](docs/screenshots/03-feedback-and-progress.png)
<!-- frontend-screenshots:end -->

## Run with Docker

Docker Compose starts PostgreSQL, the API, and the frontend. This example uses Groq:

```bash
cd LearningGraph
export LLM_PROVIDER=groq
export GROQ_API_KEY='your-groq-key'
export GROQ_MODEL='openai/gpt-oss-20b'
docker compose up --build -d
```

Open:

- **Frontend:** <http://localhost:5173>
- **API docs:** <http://localhost:8000/docs>

The API runs migrations and seeds the curriculum on startup. Learner data stays in a named PostgreSQL volume.

If your settings are in an `.env` file one directory above the project, use:

```bash
docker compose --env-file ../.env up --build -d
```

For OpenAI, set `LLM_PROVIDER=openai`, `OPENAI_API_KEY`, and `OPENAI_MODEL` instead. The selected model must support strict Structured Outputs. Check the provider's model support before changing it: [Groq](https://console.groq.com/docs/structured-outputs), [OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

Provider keys stay in the backend. Never put them in `VITE_*` variables or commit them.

### Common setup issues

If a service fails to start:

```bash
docker compose ps -a
docker compose logs --tail=80 api db
```

- Port `8000` serves the API. Open port `5173` for the learner interface.
- PostgreSQL uses host port `5433` by default. If it is occupied, run `POSTGRES_PORT=5437 docker compose up --build -d`.
- After changing provider settings, recreate the API container. For an external env file, run `docker compose --env-file ../.env up -d --force-recreate api`. Add `--build` if the code also changed.
- If the error mentions OpenAI while you intended to use Groq, check `LLM_PROVIDER` in the running container with `docker compose exec -T api printenv LLM_PROVIDER GROQ_MODEL`. Exported shell variables override values from the env file.

## Run for development

Use Python 3.12+, uv, Docker, and Node.js 22.12+. From `LearningGraph/`, start PostgreSQL and the backend:

```bash
export DATABASE_URL='postgresql+psycopg://learning:learning@localhost:5433/learning'
export LLM_PROVIDER=groq
export GROQ_API_KEY='your-groq-key'
export GROQ_MODEL='openai/gpt-oss-20b'
uv sync
docker compose up -d db
uv run alembic upgrade head
uv run python -m app.db.seed
uv run uvicorn app.main:app --reload
```

In another terminal, from `LearningGraph/`:

```bash
cd frontend
npm install
npm run dev
```

The app reads process environment variables; it does not load `.env` files automatically. If you change the database's host port, update `DATABASE_URL` too. Seeding can be repeated without clearing learner progress.

Vite proxies `/api` to `http://127.0.0.1:8000`. Set `API_PROXY_TARGET` if the local backend is elsewhere. For a separately hosted backend, set `VITE_API_BASE_URL` to its base URL and configure `CORS_ORIGINS` on the API. See [DEPLOYMENT.md](DEPLOYMENT.md) for the Vercel, Render, and Neon setup.

## How it works

### Curriculum and recommendations

The curriculum has 11 concepts and 13 prerequisite edges. I used PostgreSQL for both the graph and learner data, with a join table for prerequisites.

The planner uses a topological sort with slug ordering to break ties. A concept is available when all its prerequisites meet the mastery threshold and the concept itself is below it. The first available concept is recommended. The same progress and curriculum always produce the same recommendation, and cycles are rejected.

### Lessons and answers

The LLM returns structured lesson content. Pydantic and application checks validate the concept, required text, three questions, four distinct options per question, answer indices, and misconception tags for the incorrect options. An invalid draft gets one retry; a second invalid draft is discarded.

Validated lessons are saved before being shown. The lesson API leaves out answer keys and misconception mappings. When an answer is submitted, the backend compares it with the stored key and uses the selected option's misconception tag to request feedback if needed.

The frontend uses native `fetch` and plain CSS. It does not calculate eligibility, recommendations, correctness, or mastery. Python examples are displayed as text and never executed.

### Mastery

I used a simple score so progression is easy to follow:

| Rule | Value |
|---|---|
| Starting score | `0.00` |
| Correct answer | `+0.10` |
| Incorrect answer | `−0.05` |
| Score bounds | `0.00` to `1.00` |
| Default mastery threshold | `0.70` |

Scores use decimal arithmetic. A learner can generate more practice sets for the same concept until they reach the threshold. Set `MASTERY_THRESHOLD` to change it.

For example, eight correct answers and one incorrect answer give Alice a score of `0.75` in Variables, making Data Types the next recommendation.

### Saving progress

An attempt and its mastery update commit in the same transaction. A learner-row lock serializes submissions, and a unique constraint on learner/question pairs prevents the same question from being graded twice. Duplicate submissions return `409`.

Feedback is requested after the attempt is saved. If that request fails, the backend returns fallback feedback and keeps the recorded result.

## Project layout

```text
app/
  api/          REST endpoints
  services/     Planning, generation, grading, and feedback
  db/           Database setup and curriculum seed
  graph.py      Topological sorting
  models.py     SQLAlchemy models
  schemas.py    Request, response, and generation schemas
alembic/        Database migrations
frontend/       React UI and API client
scripts/        Developer demo
tests/          Backend tests
```

The database stores learners, concepts, prerequisites, per-concept mastery, lessons, questions, and attempts. Alembic manages schema changes.

## API

Swagger at `/docs` has the request and response schemas.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/learners` | Create a learner |
| GET | `/learners` | List learners |
| GET | `/learners/{id}` | Get a learner |
| GET | `/concepts` | List the curriculum and prerequisites |
| GET | `/concepts/{id}` | Get a concept |
| GET | `/learners/{id}/study-plan` | Get available, locked, mastered, and recommended concepts |
| GET | `/learners/{id}/next-concept` | Get the recommendation and completion status |
| GET | `/learners/{id}/progress` | Get mastery scores and attempt counts |
| POST | `/learners/{id}/lessons/generate` | Generate and save a lesson |
| GET | `/lessons/{id}` | Get a lesson and its questions |
| POST | `/attempts` | Submit an answer |

Once all concepts are mastered, the plan returns `completed: true` and no next concept. Lesson generation then returns `409`.

## Tests

```bash
uv run pytest
```

The regular tests use SQLite and mocked LLM calls. They cover graph ordering, prerequisites, mastery updates, lesson validation, duplicate attempts, rollback, feedback failures, and API responses. No provider key is needed.

There is also an optional PostgreSQL test for migrations and concurrent submissions:

```bash
export TEST_DATABASE_URL='postgresql+psycopg://learning:learning@localhost:5433/learning'
uv run pytest -m postgres
```

Use a development database with permission to create schemas. The test creates and removes its own schema. Recorded results and checks still to complete are in [VERIFICATION.md](VERIFICATION.md).

For a scripted walkthrough against the running API:

```bash
uv run python -m scripts.demo
```

It creates Alice and Bob, submits correct and incorrect answers, and checks that Alice moves on to Data Types while Bob stays on Variables. This developer script reads stored answer keys to choose its demo answers, so `DATABASE_URL` must point to the API's database. It makes live provider requests.

## Limitations

This is a demo with no authentication: learner IDs are trusted, so it is not suitable for private learner data. Lessons and answer results stay in the frontend's current session; learner records and progress persist in PostgreSQL.

Validation checks the shape of generated content, not whether every explanation or answer key is correct. Grading follows the stored key. Content review would be needed before using this for real teaching.

The mastery score is a simple practice rule, not a validated measure of learning. The project currently covers Python Fundamentals and multiple-choice questions only.
