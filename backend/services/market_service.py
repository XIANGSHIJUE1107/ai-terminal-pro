# -*- coding: utf-8 -*-
"""市场数据服务 - 整合现有 stock_platform 数据层"""
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd

from stock_platform.data.database import (
    get_connection, get_stock_daily, get_index_daily,
    get_sector_flow, get_latest_news, get_tech_indicator, get_signals,
)
from backend.config import PORTFOLIO, A_INDEX_CODES, GLOBAL_INDEX_CODES


class MarketService:
    """市场数据查询服务"""

    # ============ 市场概览 ============

    @staticmethod
    def get_index_overview() -> dict:
        """获取所有指数最新数据"""
        result = {"a_shares": [], "hk": [], "us": [], "global": []}
        conn = get_connection()

        # A股指数
        for code, name in A_INDEX_CODES.items():
            row = conn.execute(
                "SELECT * FROM index_daily WHERE code=? ORDER BY date DESC LIMIT 2",
                (code,)
            ).fetchall()
            if row:
                latest = dict(row[0])
                prev = dict(row[1]) if len(row) > 1 else latest
                change_pct = ((latest["close"] - prev["close"]) / prev["close"] * 100) if prev["close"] else 0
                result["a_shares"].append({
                    "code": code, "name": name,
                    "close": round(latest["close"], 2),
                    "change_pct": round(change_pct, 2),
                })

        conn.close()
        return result

    @staticmethod
    def get_portfolio_summary() -> list[dict]:
        """获取持仓股票概览"""
        result = []
        conn = get_connection()
        for name, symbol in PORTFOLIO.items():
            rows = conn.execute(
                "SELECT * FROM stock_daily WHERE symbol=? ORDER BY date DESC LIMIT 2",
                (symbol,)
            ).fetchall()
            if rows:
                latest = dict(rows[0])
                prev = dict(rows[1]) if len(rows) > 1 else latest
                change_pct = ((latest["close"] - prev["close"]) / prev["close"] * 100) if prev["close"] else 0
                result.append({
                    "symbol": symbol, "name": name,
                    "close": round(latest["close"], 2),
                    "change_pct": round(change_pct, 2),
                    "volume": latest.get("volume", 0),
                    "amount": latest.get("amount", 0),
                })
        conn.close()
        return result

    @staticmethod
    def get_sector_flow_data(date: str = None) -> list[dict]:
        """获取板块资金流向"""
        conn = get_connection()
        if date:
            rows = conn.execute(
                "SELECT * FROM sector_fund_flow WHERE date=? ORDER BY main_net_inflow DESC LIMIT 20",
                (date,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sector_fund_flow ORDER BY date DESC, main_net_inflow DESC LIMIT 20"
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_market_breadth() -> dict:
        """获取市场宽度（涨跌家数等）"""
        # 从板块数据估算
        conn = get_connection()
        latest_date = conn.execute("SELECT MAX(date) FROM sector_fund_flow").fetchone()[0]
        rows = conn.execute(
            "SELECT change_pct FROM sector_fund_flow WHERE date=?",
            (latest_date,)
        ).fetchall()
        conn.close()

        up_count = sum(1 for r in rows if r[0] and r[0] > 0)
        down_count = sum(1 for r in rows if r[0] and r[0] < 0)
        return {
            "up_sectors": up_count,
            "down_sectors": down_count,
            "total": len(rows),
            "date": latest_date,
        }

    @staticmethod
    def get_stock_detail(symbol: str, days: int = 120) -> dict:
        """获取个股详细数据（K线 + 技术指标）"""
        df_kline = get_stock_daily(symbol)
        if df_kline.empty:
            return {}

        df_kline = df_kline.sort_values("date").tail(days)
        df_tech = get_tech_indicator(symbol)
        if not df_tech.empty:
            df_tech = df_tech.sort_values("date").tail(days)

        kline_data = []
        for _, row in df_kline.iterrows():
            kline_data.append({
                "date": row["date"],
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2),
                "volume": int(row.get("volume", 0)),
                "amount": round(float(row.get("amount", 0)), 0),
            })

        # 最新技术指标
        latest_tech = {}
        if not df_tech.empty:
            latest = df_tech.iloc[-1]
            latest_tech = {
                "ma5": round(float(latest.get("ma5", 0)), 2),
                "ma10": round(float(latest.get("ma10", 0)), 2),
                "ma20": round(float(latest.get("ma20", 0)), 2),
                "ma60": round(float(latest.get("ma60", 0)), 2),
                "ma120": round(float(latest.get("ma120", 0)), 2),
                "dif": round(float(latest.get("dif", 0)), 4),
                "dea": round(float(latest.get("dea", 0)), 4),
                "macd": round(float(latest.get("macd", 0)), 4),
                "k": round(float(latest.get("k", 0)), 2),
                "d": round(float(latest.get("d", 0)), 2),
                "j": round(float(latest.get("j", 0)), 2),
                "rsi6": round(float(latest.get("rsi6", 0)), 2),
                "rsi12": round(float(latest.get("rsi12", 0)), 2),
                "rsi24": round(float(latest.get("rsi24", 0)), 2),
                "boll_upper": round(float(latest.get("boll_upper", 0)), 2),
                "boll_mid": round(float(latest.get("boll_mid", 0)), 2),
                "boll_lower": round(float(latest.get("boll_lower", 0)), 2),
            }

        # 信号
        signals = get_signals(symbol=symbol)
        signal_list = []
        if not signals.empty:
            for _, s in signals.tail(20).iterrows():
                signal_list.append({
                    "date": s["date"],
                    "type": s["signal_type"],
                    "detail": s["detail"],
                })

        latest_price = kline_data[-1]["close"] if kline_data else 0
        prev_price = kline_data[-2]["close"] if len(kline_data) > 1 else latest_price
        change_pct = ((latest_price - prev_price) / prev_price * 100) if prev_price else 0

        return {
            "symbol": symbol,
            "latest_price": latest_price,
            "change_pct": round(change_pct, 2),
            "kline": kline_data,
            "indicators": latest_tech,
            "signals": signal_list,
            "ma_data": [{
                "date": row["date"],
                "ma5": round(float(row.get("ma5", 0)), 2),
                "ma10": round(float(row.get("ma10", 0)), 2),
                "ma20": round(float(row.get("ma20", 0)), 2),
                "ma60": round(float(row.get("ma60", 0)), 2),
            } for _, row in (df_tech.tail(days).iterrows() if not df_tech.empty else [])],
        }


market_service = MarketService()