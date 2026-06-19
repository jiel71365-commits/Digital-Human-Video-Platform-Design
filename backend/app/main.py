from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.api.routes import router
from app.config import get_settings
from app.database import create_db_and_tables, engine
from app.seed import seed_defaults


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if app.state.run_startup_db:
        create_db_and_tables()
        with Session(engine) as session:
            seed_defaults(session)
    yield


def create_app(run_startup_db: bool = True) -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Digital Human Video Platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.run_startup_db = run_startup_db
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
