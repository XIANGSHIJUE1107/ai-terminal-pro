# -*- coding: utf-8 -*-
"""
定时任务调度器
使用 APScheduler 实现交易日自动运行
"""

import sys
import os
import time
from datetime import datetime

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from stock_platform.config import SCHEDULE_CONFIG
from stock_platform.data.fetcher import run_daily_update, run_morning_snapshot, run_intraday
from stock_platform.data.database import init_db
from stock_platform.indicator.calculator import batch_update
from stock_platform.signal.detector import scan_all
from stock_platform.prediction.engine import run_predictions
from stock_platform.prediction.verify import verify_expired_predictions, print_win_rate


def after_close_pipeline():
    """
    收盘后完整流水线：
    数据更新 → 指标计算 → 信号扫描 → 预测生成 → 验证回测
    """
    print(f"\n{'#'*60}")
    print(f"# 收盘后自动化流水线启动 {datetime.now()}")
    print(f"{'#'*60}")

    # Step 1: 数据更新
    run_daily_update()

    # Step 2: 技术指标计算
    batch_update()

    # Step 3: 信号扫描
    scan_all()

    # Step 4: 预测生成
    run_predictions()

    # Step 5: 验证过期预测
    verify_expired_predictions()
    print_win_rate()

    print(f"\n{'#'*60}")
    print(f"# 收盘后流水线完成 {datetime.now()}")
    print(f"{'#'*60}\n")


def start_scheduler():
    """
    启动定时任务调度器
    """
    print("[Scheduler] 初始化数据库...")
    init_db()

    scheduler = BackgroundScheduler()

    # 早间板块资金快照
    morning_time = SCHEDULE_CONFIG["morning_snapshot"]  # "09:00"
    morning_hour, morning_min = morning_time.split(":")
    scheduler.add_job(
        run_morning_snapshot,
        trigger=CronTrigger(day_of_week="mon-fri", hour=int(morning_hour), minute=int(morning_min)),
        id="morning_snapshot",
        name="早间快照",
    )
    print(f"[Scheduler] 早间快照: 每个工作日 {morning_time}")

    # 盘中更新
    intraday_time = SCHEDULE_CONFIG["intraday_start"]  # "09:30"
    intraday_hour, intraday_min = intraday_time.split(":")
    scheduler.add_job(
        run_intraday,
        trigger=CronTrigger(day_of_week="mon-fri", hour=int(intraday_hour), minute=int(intraday_min)),
        id="intraday_update",
        name="盘中更新",
    )
    print(f"[Scheduler] 盘中更新: 每个工作日 {intraday_time}")

    # 收盘后完整流水线
    close_time = SCHEDULE_CONFIG["after_close"]  # "15:30"
    close_hour, close_min = close_time.split(":")
    scheduler.add_job(
        after_close_pipeline,
        trigger=CronTrigger(day_of_week="mon-fri", hour=int(close_hour), minute=int(close_min)),
        id="after_close",
        name="收盘后流水线",
    )
    print(f"[Scheduler] 收盘后流水线: 每个工作日 {close_time}")

    scheduler.start()
    print("[Scheduler] 调度器已启动，等待定时任务...")

    try:
        # 保持运行
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        print("[Scheduler] 调度器停止")
        scheduler.shutdown()


if __name__ == "__main__":
    print("股票分析平台定时调度器")
    print("-" * 40)
    print("按 Ctrl+C 停止")
    print("-" * 40)
    start_scheduler()