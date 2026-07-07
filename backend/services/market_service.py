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

    # 全球指数 AKShare 名称映射（index_global_hist_sina 使用中文名称作为 symbol）
    _GLOBAL_HIST_NAME_MAP = {
        "KS11": "首尔综合指数",
        "N225": "日经225指数",
        "TWII": "台湾加权指数",
        "AS51": "澳大利亚标准普尔200指数",
        "SENSEX": "印度孟买SENSEX指数",
        "IBOV": "巴西BOVESPA股票指数",
        "MXX": "墨西哥BOLSA指数",
        "GSPTSE": "加拿大S&P/TSX综合指数",
        "UKX": "英国富时100指数",
        "DAX": "德国DAX 30种股价指数",
        "CAC": "法CAC40指数",
        "SX5E": "欧洲Stoxx50指数",
    }

    @classmethod
    def _fetch_global_index_spot(cls, code: str) -> dict | None:
        """通过 AKShare 获取全球指数实时行情"""
        try:
            import akshare as ak
            df = ak.index_global_spot_em()
            if df is None or df.empty:
                return None
            mask = df["代码"] == code
            if not mask.any():
                mask = df["名称"].str.contains(code, case=False, na=False)
            if not mask.any():
                return None
            row = df.loc[mask].iloc[0]
            close = float(row.get("最新价", 0) or 0)
            prev_close = float(row.get("昨收价", close) or close)
            change_pct = float(row.get("涨跌幅", 0) or 0)
            return {
                "code": code,
                "name": str(row.get("名称", GLOBAL_INDEX_CODES.get(code, code))).strip(),
                "close": round(close, 2),
                "open": round(float(row.get("开盘价", close) or close), 2),
                "high": round(float(row.get("最高价", close) or close), 2),
                "low": round(float(row.get("最低价", close) or close), 2),
                "prev_close": round(prev_close, 2),
                "change_pct": round(change_pct, 2),
                "volume": 0,
                "amount": 0,
                "source": "akshare-spot",
                "time": str(row.get("最新行情时间", "")),
            }
        except Exception as e:
            print(f"[MarketService] AKShare 获取 {code} 实时行情失败: {e}")
            return None

    @classmethod
    def _fetch_global_index_kline(cls, code: str, days: int = 120) -> list[dict]:
        """通过 AKShare 获取全球指数历史 K 线"""
        hist_name = cls._GLOBAL_HIST_NAME_MAP.get(code)
        if not hist_name:
            return []
        try:
            import akshare as ak
            import pandas as pd
            df = ak.index_global_hist_sina(symbol=hist_name)
            if df is None or df.empty:
                return []
            col_map = {"date": "date", "open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"}
            df = df.rename(columns=col_map)
            keep = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in df.columns]
            df = df[keep].tail(days)
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            rows = []
            for _, row in df.iterrows():
                rows.append({
                    "date": str(row["date"]),
                    "open": round(float(row["open"]), 2),
                    "high": round(float(row["high"]), 2),
                    "low": round(float(row["low"]), 2),
                    "close": round(float(row["close"]), 2),
                    "volume": int(row.get("volume", 0)) if not pd.isna(row.get("volume")) else 0,
                    "amount": 0,
                })
            return rows
        except Exception as e:
            print(f"[MarketService] AKShare 获取 {code} K线失败: {e}")
            return []

    @staticmethod
    def _index_row_from_db(conn, code: str, name: str) -> dict | None:
        rows = conn.execute(
            "SELECT * FROM index_daily WHERE code=? ORDER BY date DESC LIMIT 2",
            (code,)
        ).fetchall()
        if not rows:
            return None
        latest = dict(rows[0])
        prev = dict(rows[1]) if len(rows) > 1 else latest
        change_pct = ((latest["close"] - prev["close"]) / prev["close"] * 100) if prev["close"] else 0
        return {
            "code": code, "name": name or latest.get("name", code),
            "close": round(latest["close"], 2),
            "open": round(latest.get("open", latest["close"]), 2),
            "high": round(latest.get("high", latest["close"]), 2),
            "low": round(latest.get("low", latest["close"]), 2),
            "prev_close": round(prev["close"], 2),
            "change_pct": round(change_pct, 2),
            "volume": int(latest.get("volume", 0) or 0),
            "amount": round(float(latest.get("amount", 0) or 0), 0),
            "source": "db",
        }

    # ============ 市场概览 ============

    @staticmethod
    def get_index_overview() -> dict:
        """获取所有指数最新数据"""
        result = {"a_shares": [], "hk": [], "us": [], "global": []}
        conn = get_connection()

        # A股指数
        for code, name in A_INDEX_CODES.items():
            row = MarketService._index_row_from_db(conn, code, name)
            if row:
                result["a_shares"].append(row)

        # 全球指数（DB 优先，缺失/陈旧时通过 AKShare 补全）
        for code, name in GLOBAL_INDEX_CODES.items():
            row = MarketService._index_row_from_db(conn, code, name)
            if not row:
                row = MarketService._fetch_global_index_spot(code)
            result["global"].append(row or {
                "code": code, "name": name, "close": None, "change_pct": None,
                "source": "unavailable",
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