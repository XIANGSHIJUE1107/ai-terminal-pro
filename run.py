# -*- coding: utf-8 -*-
"""
一键启动脚本
- 无参数：启动 Streamlit 看板
- --scheduler：启动定时调度器
- --update：运行一次收盘后全量更新
"""

import sys
import os

# 禁用系统代理，避免代理连接失败
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduler":
        print("启动定时调度器...")
        from stock_platform.scheduler import start_scheduler
        start_scheduler()
    elif len(sys.argv) > 1 and sys.argv[1] == "--update":
        print("运行一次性全量更新...")
        from stock_platform.data.database import init_db
        from stock_platform.data.fetcher import run_daily_update
        from stock_platform.indicator.calculator import batch_update
        from stock_platform.signal.detector import scan_all
        from stock_platform.prediction.engine import run_predictions
        from stock_platform.prediction.verify import verify_expired_predictions, print_win_rate

        init_db()
        run_daily_update()
        batch_update()
        scan_all()
        run_predictions()
        verify_expired_predictions()
        print_win_rate()
    else:
        # 默认启动 Streamlit 看板
        print("启动 Streamlit 看板...")
        os.system(f"{sys.executable} -m streamlit run stock_platform/dashboard.py")


if __name__ == "__main__":
    main()