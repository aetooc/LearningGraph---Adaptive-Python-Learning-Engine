# Free résumé demo deployment

Deploy the production React build on Vercel, the FastAPI Docker image on Render,
and PostgreSQL on Neon. The public résumé link will be the Vercel frontend URL.

| Part | Host | Configuration |
|---|---|---|
| React frontend | [Vercel](https://vercel.com/docs/frameworks/frontend/vite) | Vite build, `frontend/dist` |
| FastAPI backend | [Render](https://render.com/docs/docker) | Docker web service, Free plan |
| PostgreSQL | [Neon](https://neon.com/blog/neon-free-plan-1-gb-per-project) | Free project, database connection string |

These services have free plans with usage limits. Render's Free web service
sleeps after 15 minutes without traffic; the next request can take about a
minute to wake it. This is a tradeoff of the free backend plan.
[Render Free limits](https://render.com/docs/free),
[Vercel Hobby plan](https://vercel.com/docs/plans/hobby).

## 1. Put the project on GitHub

Push the project, including `uv.lock`, `frontend/`, and the deployment changes,
to your GitHub repository. Provider keys will be entered in the hosting
dashboard. `.gitignore` excludes environment files.

The instructions below assume the contents of `LearningGraph/` are at the
repository root. If your repository contains the outer `LearningGraph/` folder,
use `LearningGraph` as Render's Root Directory and `LearningGraph/frontend` as
Vercel's Root Directory instead.

## 2. Create the Neon database

1. Sign in to [Neon](https://neon.com/) and create a project on the Free plan.
2. Choose a region near your Render service.
3. Copy the direct/unpooled PostgreSQL connection string from the connection
   dialog, keeping its SSL parameters.

It will have a shape like this; use the real value only in Render's settings:

```text
postgresql://USER:PASSWORD@HOST/neondb?sslmode=require
```

The backend converts standard `postgresql://` and `postgres://` URLs to the
installed psycopg driver while preserving credentials and query parameters.
Use Neon for this setup: Render's Free PostgreSQL database expires after 30
days. [Render database limits](https://render.com/docs/free#free-postgres).

## 3. Deploy FastAPI on Render

In [Render](https://dashboard.render.com/), create **New → Web Service**, connect
your GitHub repository, and configure:

| Setting | Value |
|---|---|
| Language/runtime | Docker |
| Root Directory | Blank, if `app/` and `Dockerfile` are at the repository root |
| Dockerfile Path | `./Dockerfile` |
| Instance type | Free |
| Health Check Path | `/openapi.json` |
| Docker Command | Leave blank; use the Dockerfile's command |

Set these environment variables in Render:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Your Neon connection string |
| `LLM_PROVIDER` | `groq` |
| `GROQ_API_KEY` | Your actual Groq key |
| `GROQ_MODEL` | `openai/gpt-oss-20b` |
| `MASTERY_THRESHOLD` | `0.70` |
| `CORS_ORIGINS` | `[]` initially; update after obtaining the frontend URL |

Your local `.env` is not the cloud configuration. Enter the selected provider
and its credentials explicitly in Render's environment settings.

Create the service and wait for its deploy to finish. The Docker command runs
migrations, seeds the curriculum, and starts Uvicorn on Render's `PORT`.
[Render deployment and port settings](https://render.com/docs/web-services).

Open the resulting API address with `/docs` appended and confirm Swagger loads,
for example `https://YOUR-API.onrender.com/docs`. Keep the API base URL for the
next step.

## 4. Deploy React on Vercel

In [Vercel](https://vercel.com/), choose **Add New → Project**, import the same
GitHub repository, and configure:

| Setting | Value |
|---|---|
| Root Directory | `frontend` |
| Framework Preset | Vite |
| Node.js version | 24.x |
| Build Command | `npm run build` |
| Output Directory | `dist` |

Add this environment variable for **Production**, replacing the example with
your actual Render API address:

```text
VITE_API_BASE_URL=https://YOUR-API.onrender.com
```

Use the backend's base address without `/docs` or `/api`. The cloud frontend
calls the backend directly; the local Vite `/api` proxy is not used here.
Provider keys belong in Render's backend variables.

Click **Deploy**. Vercel serves the compiled frontend, so the local Vite Docker
container is not deployed. Copy the frontend's production URL, such as
`https://YOUR-PROJECT.vercel.app`.
[Vite deployment on Vercel](https://vercel.com/docs/frameworks/frontend/vite).

## 5. Allow the frontend to call the API

In the Render API's environment settings, replace `CORS_ORIGINS` with a JSON
array containing your exact Vercel production origin:

```json
["https://YOUR-PROJECT.vercel.app"]
```

Include `https://`, omit a trailing slash, and save/redeploy the API. This
enables the frontend's GET and POST requests from that origin.
[FastAPI CORS configuration](https://fastapi.tiangolo.com/tutorial/cors/).

If you later change `VITE_API_BASE_URL`, redeploy the frontend because Vite
embeds that value during the build.

## 6. Verify the public demo

Open the Vercel production URL in an incognito window and complete the flow:

1. Create or select Alice.
2. Confirm the study plan and recommended concept load.
3. Generate a lesson and inspect its examples and three questions.
4. Submit an answer and confirm grading and progress refresh.
5. Submit an incorrect answer on another question to check feedback.

Use this **frontend production URL** for the résumé's **Live Demo** link, with
your GitHub repository as **Source Code**. A custom domain is optional.

## If deployment fails

| Symptom | Check |
|---|---|
| OpenAI key error | Render has `LLM_PROVIDER=groq`, then redeploy |
| Database startup failure | Neon URL and SSL parameters are copied correctly; inspect Render deploy logs |
| CORS error in the browser | `CORS_ORIGINS` matches the exact frontend production origin; redeploy Render |
| Frontend calls `/api/learners` on Vercel | Set `VITE_API_BASE_URL` to the Render base URL and redeploy Vercel |
| First load is slow | The Render Free service may be waking from sleep |
