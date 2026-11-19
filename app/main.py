"""Punto de entrada de la aplicacion FastAPI del Parqueadero SGP-8."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import crear_pool, inicializar_esquema
from .repository import PostgresRepository
from .routes import router
from .service import ParqueaderoService

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


def create_app(enable_db: bool = True) -> FastAPI:
    """Fabrica de la app. enable_db=False se usa en tests sin PostgreSQL."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if enable_db:
            settings = get_settings()
            pool = crear_pool(settings)
            inicializar_esquema(pool)

            repositorio = PostgresRepository(pool, settings)
            repositorio.sembrar_config(settings)
            repositorio.sincronizar_celdas(settings.total_celdas)

            app.state.pool = pool
            app.state.service = ParqueaderoService(
                repositorio, settings.zona_horaria
            )
        yield
        if enable_db:
            app.state.pool.close()

    app = FastAPI(
        title="Parqueadero SGP-8",
        description="Demo de control de parqueadero con PostgreSQL en Aiven.",
        version="2.0.0",
        lifespan=lifespan,
    )
    app.include_router(router)

    @app.get("/health", tags=["salud"])
    def health() -> dict:
        return {"status": "ok"}

    if FRONTEND_DIR.exists():
        app.mount(
            "/static",
            StaticFiles(directory=str(FRONTEND_DIR)),
            name="static",
        )

        @app.get("/", include_in_schema=False)
        def index() -> FileResponse:
            return FileResponse(FRONTEND_DIR / "index.html")

    return app


app = create_app()
