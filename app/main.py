from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse

from app.api import attempts, concepts, learners, learning, lessons
from app.errors import ApplicationError

app = FastAPI(
    title="Adaptive Python Learning Engine",
    version="0.1.0",
    description="Deterministic progression through a Python prerequisite graph; "
    "LLMs draft lessons and explain mistakes.",
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
