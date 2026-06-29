# -*- coding: utf-8 -*-
"""FastAPI main entry for the AI research terminal."""

import os
import sys
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import alerts, dashboard, datahub, fundflow, news, research, review, sector, stock, watchlist
from backend.config import DEBUG, HOST, PORT
from backend.datahub import datahub_service
from backend.models.database import init_db
from backend.tasks.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Server] Initializing database...")
    init_db()
    print("[Server] Starting DataHub refresh...")
    datahub_service.refresh(force=True)
    print("[Server] Starting scheduler...")
    start_scheduler()
    print("[Server] Platform started")
    yield
    print("[Server] Stopping scheduler...")
    stop_scheduler()
    print("[Server] Platform stopped")


app = FastAPI(
    title="AI智能投研分析平台 Professional Edition",
    description="A股全栈数据 · 七层架构 · V3.2.4 | mootdx/腾讯优先 | 东财限流防封",
    version="3.2.4",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datahub.router, prefix="/api/datahub", tags=["DataHub"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["Watchlist"])
app.include_router(stock.router, prefix="/api/stock", tags=["Stock"])
app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(sector.router, prefix="/api/sector", tags=["Sector"])
app.include_router(fundflow.router, prefix="/api/fundflow", tags=["FundFlow"])
app.include_router(review.router, prefix="/api/review", tags=["Review"])
app.include_router(research.router, prefix="/api/research", tags=["Research"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])


@app.get("/api/health")
async def health_check():
    return datahub_service.health()


@app.get("/api/data/latest")
async def latest_alias():
    return datahub_service.latest()


@app.post("/api/data/refresh")
async def refresh_alias():
    return datahub_service.refresh(force=True)


@app.get("/api/data/snapshots")
async def snapshots_alias(kind: str | None = None):
    return {
        "source": "datahub_snapshots",
        "updatedAt": datahub_service.state().get("last_update_time"),
        "freshness": "local-cache",
        "stale": True,
        "unavailable": False,
        "errors": [],
        "data": {"items": datahub_service.snapshot_list(kind)},
        "items": datahub_service.snapshot_list(kind),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=DEBUG)

