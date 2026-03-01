from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import (
    attendance, lms_activity, coding_activity,
    predict_risk, notifications, dashboard,
    platform, bulk_ingest, auth,
)
from backend.clients.mongo_client import connect_mongo, close_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ─────────────────────────────────────────────
    await connect_mongo()
    yield
    # ── Shutdown ────────────────────────────────────────────
    await close_mongo()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Academic Risk Backend",
        version="0.4.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Auth (signup / login — no token required) ────────────
    app.include_router(auth.router, prefix="/api")

    # ── Single-event ingest ─────────────────────────────────
    app.include_router(attendance.router, prefix="/api")
    app.include_router(lms_activity.router, prefix="/api")
    app.include_router(coding_activity.router, prefix="/api")

    # ── Bulk ingest (up to 10k events per call) ─────────────
    app.include_router(bulk_ingest.router, prefix="/api")

    # ── Platform config & student profile linking ───────────
    app.include_router(platform.router, prefix="/api")

    # ── ML + notifications + dashboards ─────────────────────
    app.include_router(predict_risk.router, prefix="/api")
    app.include_router(notifications.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
    return app


app = create_app()

