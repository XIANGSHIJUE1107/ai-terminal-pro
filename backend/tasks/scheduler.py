# -*- coding: utf-8 -*-
"""Shared APScheduler for DataHub refresh."""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from backend.datahub import datahub_service


_scheduler: BackgroundScheduler | None = None


def run_refresh_job():
    try:
        result = datahub_service.refresh(force=True)
        status = result.get("freshness")
        print(f"[Scheduler] refresh completed: {status} @ {result.get('updatedAt')}")
    except Exception as exc:
        print(f"[Scheduler] refresh failed: {exc}")
        import traceback
        traceback.print_exc()


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    _scheduler.add_job(
        run_refresh_job,
        "interval",
        seconds=datahub_service.state().get("refresh_interval_seconds", 600),
        id="datahub_refresh",
        name="DataHub 10min refresh",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120,
    )
    _scheduler.start()
    print("[Scheduler] started")
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        print("[Scheduler] stopped")

