from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from src.app.server.routers.patient import router as patient_router
from src.app.server.routers.staff import router as staff_router
from src.utils.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(
    title="SalleQ",
    description="Quebec-first CTAS-informed virtual waiting room built on Databricks Apps.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"] if os.getenv("ENV", "development") == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patient_router, prefix="/api")
app.include_router(staff_router, prefix="/api")


@app.get("/api/health")
async def health() -> dict[str, object]:
    return {
        "ok": True,
        "catalog": settings.catalog,
        "schema": settings.schema,
        "warehouse_id": settings.warehouse_id,
    }


_project_root = Path(__file__).resolve().parents[3]
_build_candidates = [
    _project_root / "app/client/dist",
    _project_root / "app/client/out",
    _project_root / "src/app/client/out",
    Path("/app/python/source_code/src/app/client/out"),
]
_build_path = next((path for path in _build_candidates if path.exists()), None)

if _build_path:
    index_html = _build_path / "index.html"

    @app.exception_handler(StarletteHTTPException)
    async def spa_fallback(_, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return FileResponse(index_html)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    app.mount("/", StaticFiles(directory=str(_build_path), html=True), name="static")
