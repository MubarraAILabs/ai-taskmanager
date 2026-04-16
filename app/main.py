from fastapi import FastAPI

from app.api.routes import router as task_router, ai_router
from app.core.database import init_db


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Task Manager",
        description="A production-ready FastAPI task manager with clean architecture and SQLite persistence.",
        version="1.0.0",
    )
    app.include_router(task_router)
    app.include_router(ai_router)

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    return app


app = create_app()
