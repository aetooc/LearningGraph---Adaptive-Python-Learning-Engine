from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.api import attempts, concepts, learners, learning, lessons
from app.config import get_settings
from app.errors import ApplicationError

app = FastAPI(
    title="Adaptive Python Learning Engine",
    version="0.1.0",
    description="Deterministic progression through a Python prerequisite graph; "
    "LLMs draft lessons and explain mistakes.",
)

cors_origins = get_settings().cors_origins
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )


@app.exception_handler(ApplicationError)
async def application_error_handler(request, error: ApplicationError):
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})


@app.get("/", include_in_schema=False)
def open_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")


app.include_router(learners.router)
app.include_router(concepts.router)
app.include_router(learning.router)
app.include_router(lessons.router)
app.include_router(attempts.router)
