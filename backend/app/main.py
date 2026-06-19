from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session

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
    app = FastAPI(
        title="Digital Human Video Platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.run_startup_db = run_startup_db

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
