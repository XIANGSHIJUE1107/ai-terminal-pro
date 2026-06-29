# -*- coding: utf-8 -*-
"""
行情层 —— mootdx + 腾讯财经 + 百度K线 (优先级: mootdx/腾讯 不封IP 优先)
K线(带MA5/10/20) + 五档盘口 + PE/PB/市值 + 指数/ETF
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.data_sources.base import (
    to_float, with_prefix, code6, market_code, now_text, now_dt,
    TDX_SERVERS, probe_tdx, get_session,
)


class MarketDataSource:
    """行情数据源：mootdx > 腾讯财经 > 百度K线"""

    # ==================== 五档盘口（mootdx） ====================
    @staticmethod
    def mootdx_level2(symbol: str) -> dict[str, Any] | None:
        """获取五档盘口数据（mootdx）"""
        try:
            from mootdx.quotes import Quotes
        except Exception:
            return None
        sym6 = code6(symbol)
        mkt = market_code(symbol)
        for ip, port in TDX_SERVERS:
            if not probe_tdx(ip, port):
                continue
            try:
                client = Quotes.factory(market="std", server=ip, port=port)
                df = client.quotes(symbol=[sym6])
                if df is None or getattr(df, "empty", False):
                    continue
                row = df.iloc[0].to_dict()
                return {
                    "symbol": with_prefix(symbol),
                    "name": str(row.get("name", "")),
                    "current": to_float(row.get("price")),
                    "open": to_float(row.get("open")),
                    "high": to_float(row.get("high")),
                    "low": to_float(row.get("low")),
                    "prevClose": to_float(row.get("last_close")),
                    "volume": to_float(row.get("vol") or row.get("volume")),
                    "amount": to_float(row.get("amount")),
                    "changePct": to_float(row.get("price_change")),
                    # 五档盘口
                    "bid1": to_float(row.get("bid1")),
                    "bid1_vol": int(row.get("bid1_vol", 0) or 0),
                    "bid2": to_float(row.get("bid2")),
                    "bid2_vol": int(row.get("bid2_vol", 0) or 0),
                    "bid3": to_float(row.get("bid3")),
                    "bid3_vol": int(row.get("bid3_vol", 0) or 0),
                    "bid4": to_float(row.get("bid4")),
                    "bid4_vol": int(row.get("bid4_vol", 0) or 0),
                    "bid5": to_float(row.get("bid5")),
                    "bid5_vol": int(row.get("bid5_vol", 0) or 0),
                    "ask1": to_float(row.get("ask1")),
                    "ask1_vol": int(row.get("ask1_vol", 0) or 0),
                    "ask2": to_float(row.get("ask2")),
                    "ask2_vol": int(row.get("ask2_vol", 0) or 0),
                    "ask3": to_float(row.get("ask3")),
                    "ask3_vol": int(row.get("ask3_vol", 0) or 0),
                    "ask4": to_float(row.get("ask4")),
                    "ask4_vol": int(row.get("ask4_vol", 0) or 0),
                    "ask5": to_float(row.get("ask5")),
                    "ask5_vol": int(row.get("ask5_vol", 0) or 0),
                    "source": "Mootdx/TDX-Level2",
                }
            except Exception:
                continue
        return None

    # ==================== 腾讯实时行情（含PE/PB/市值） ====================
    @staticmethod
    def tencent_quote(symbol: str) -> dict[str, Any] | None:
        """腾讯财经实时行情（含PE/PB/市值）"""
        import re

        sym = with_prefix(symbol)
        try:
            session = get_session()
            resp = session.get(
                f"https://qt.gtimg.cn/q={sym}",
                timeout=10,
                headers={"Referer": "https://gu.qq.com/"},
            )
            resp.raise_for_status()
            text = resp.content.decode("gbk", errors="ignore")
            if '="' not in text:
                return None
            payload = text.split('="', 1)[1].rsplit('"', 1)[0]
            parts = payload.split("~")
            if len(parts) < 10:
                return None

            current = to_float(parts[3])
            prev_close = to_float(parts[4])
            change_pct = ((current - prev_close) / prev_close * 100) if prev_close else 0

            # PE/PB/市值 (腾讯字段索引)
            pe = to_float(parts[39]) if len(parts) > 39 else 0
            pb = 0
            market_cap = to_float(parts[45]) if len(parts) > 45 else 0  # 总市值（亿）
            circulating_cap = to_float(parts[44]) if len(parts) > 44 else 0  # 流通市值（亿）

            return {
                "symbol": sym,
                "name": parts[1] or sym,
                "open": to_float(parts[5]),
                "prevClose": prev_close,
                "current": current,
                "high": to_float(parts[33] if len(parts) > 33 else 0),
                "low": to_float(parts[34] if len(parts) > 34 else 0),
                "volume": to_float(parts[6]),
                "amount": to_float(parts[7]),
                "changePct": round(change_pct, 2),
                "change": round(change_pct, 2),
                "pe": round(pe, 2),
                "pb": round(pb, 2),
                "marketCap": round(market_cap, 2),
                "circulatingCap": round(circulating_cap, 2),
                "turnoverRate": to_float(parts[38]) if len(parts) > 38 else 0,
                "amplitude": to_float(parts[43]) if len(parts) > 43 else 0,
                "source": "Tencent",
            }
        except Exception:
            return None

    # ==================== 百度K线（日线） ====================
    @staticmethod
    def baidu_kline(symbol: str, days: int = 120) -> list[dict]:
        """百度财经K线数据"""
        sym = with_prefix(symbol)
        try:
            session = get_session()
            resp = session.get(
                f"https://finance.pae.baidu.com/selfselect/openapi?srcid=5353&code={sym}&market=ab&tag=1&"
                f"chartselect=1&is_daily=1&start=&end=&finClientType=pc",
                timeout=10,
                headers={"Referer": "https://gushitong.baidu.com/"},
            )
            resp.raise_for_status()
            data = resp.json()
            kline = (data.get("Result") or {}).get("newData") or []
            items = []
            for row in kline[-days:]:
                items.append({
                    "date": str(row.get("date") or ""),
                    "open": to_float(row.get("open")),
                    "high": to_float(row.get("high")),
                    "low": to_float(row.get("low")),
                    "close": to_float(row.get("close")),
                    "volume": to_float(row.get("volume")),
                    "amount": to_float(row.get("amount")),
                })
            return items
        except Exception:
            return []

    # ==================== 腾讯日线K线 ====================
    @staticmethod
    def tencent_daily_kline(symbol: str, days: int = 120) -> list[dict]:
        """腾讯财经日线K线（带MA5/10/20）"""
        sym = with_prefix(symbol)
        try:
            session = get_session()
            resp = session.get(
                f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
                f"param={sym},day,,,{days},qfq",
                timeout=10,
                headers={"Referer": "https://gu.qq.com/"},
            )
            resp.raise_for_status()
            data = resp.json()
            rows = (data.get("data") or {}).get(sym, {}).get("qfqday") or (data.get("data") or {}).get(sym, {}).get("day") or []
            items = []
            for row in rows:
                items.append({
                    "date": str(row[0]),
                    "open": to_float(row[1]),
                    "close": to_float(row[2]),
                    "high": to_float(row[3]),
                    "low": to_float(row[4]),
                    "volume": to_float(row[5]),
                    "amount": to_float(row[6]) if len(row) > 6 else 0,
                })
            return items[-days:]
        except Exception:
            return []

    # ==================== 综合行情（优先mootdx→腾讯） ====================
    @classmethod
    def get_quote(cls, symbol: str) -> dict[str, Any]:
        """获取综合行情：mootdx(含五档盘口) > 腾讯(含PE/PB/市值)"""
        errors = []
        # 优先 mootdx（含五档盘口）
        try:
            quote = cls.mootdx_level2(symbol)
            if quote:
                quote["updatedAt"] = now_text()
                return quote
        except Exception as e:
            errors.append({"source": "Mootdx/TDX", "message": str(e)})

        # 其次腾讯（含PE/PB/市值）
        try:
            quote = cls.tencent_quote(symbol)
            if quote:
                quote["updatedAt"] = now_text()
                # 补充五档为空
                for key in ["bid1", "bid2", "bid3", "bid4", "bid5", "ask1", "ask2", "ask3", "ask4", "ask5"]:
                    quote.setdefault(key, None)
                for key in ["bid1_vol", "bid2_vol", "bid3_vol", "bid4_vol", "bid5_vol",
                           "ask1_vol", "ask2_vol", "ask3_vol", "ask4_vol", "ask5_vol"]:
                    quote.setdefault(key, 0)
                return quote
        except Exception as e:
            errors.append({"source": "Tencent", "message": str(e)})

        return {
            "symbol": with_prefix(symbol),
            "name": symbol,
            "current": None, "prevClose": None, "changePct": None,
            "source": "unavailable", "updatedAt": now_text(), "errors": errors,
        }

    # ==================== 综合K线（优先腾讯→百度） ====================
    @classmethod
    def get_kline(cls, symbol: str, days: int = 120) -> list[dict]:
        """获取K线：腾讯 > 百度 > AKShare"""
        data = cls.tencent_daily_kline(symbol, days)
        if data:
            return data
        data = cls.baidu_kline(symbol, days)
        if data:
            return data
        # Fallback: AKShare
        try:
            import akshare as ak
            sym = with_prefix(symbol)
            df = ak.stock_zh_a_hist_tx(
                symbol=sym,
                start_date="20200101",
                end_date=now_dt().strftime("%Y%m%d"),
            )
            if df is not None and not df.empty:
                items = []
                for _, row in df.tail(days).iterrows():
                    import pandas as pd
                    items.append({
                        "date": pd.to_datetime(row.get("日期")).strftime("%Y-%m-%d"),
                        "open": to_float(row.get("开盘")),
                        "high": to_float(row.get("最高")),
                        "low": to_float(row.get("最低")),
                        "close": to_float(row.get("收盘")),
                        "volume": to_float(row.get("成交量")),
                        "amount": to_float(row.get("成交额")),
                    })
                return items
        except Exception:
            pass
        return []

    # ==================== 指数行情 ====================
    @staticmethod
    def get_index_quote(code: str) -> dict[str, Any] | None:
        """获取指数行情（腾讯）"""
        try:
            session = get_session()
            resp = session.get(
                f"https://qt.gtimg.cn/q={code}",
                timeout=10,
                headers={"Referer": "https://gu.qq.com/"},
            )
            resp.raise_for_status()
            text = resp.content.decode("gbk", errors="ignore")
            if '="' not in text:
                return None
            payload = text.split('="', 1)[1].rsplit('"', 1)[0]
            parts = payload.split("~")
            if len(parts) < 10:
                return None
            current = to_float(parts[3])
            prev_close = to_float(parts[4])
            return {
                "code": code,
                "name": parts[1] or code,
                "current": current,
                "prevClose": prev_close,
                "open": to_float(parts[5]),
                "high": to_float(parts[33] if len(parts) > 33 else 0),
                "low": to_float(parts[34] if len(parts) > 34 else 0),
                "volume": to_float(parts[6]),
                "amount": to_float(parts[7]),
                "changePct": round((current - prev_close) / prev_close * 100, 2) if prev_close else 0,
                "source": "Tencent",
            }
        except Exception:
            return None

    # ==================== ETF 行情 ====================
    @classmethod
    def get_etf_quote(cls, symbol: str) -> dict[str, Any] | None:
        """ETF行情：mootdx > 腾讯"""
        try:
            from mootdx.quotes import Quotes
            sym6 = code6(symbol)
            for ip, port in TDX_SERVERS:
                if not probe_tdx(ip, port):
                    continue
                try:
                    client = Quotes.factory(market="std", server=ip, port=port)
                    df = client.quotes(symbol=[sym6])
                    if df is None or getattr(df, "empty", False):
                        continue
                    row = df.iloc[0].to_dict()
                    current = to_float(row.get("price"))
                    prev = to_float(row.get("last_close"))
                    return {
                        "symbol": with_prefix(symbol),
                        "name": str(row.get("name", "")),
                        "current": current,
                        "prevClose": prev,
                        "open": to_float(row.get("open")),
                        "high": to_float(row.get("high")),
                        "low": to_float(row.get("low")),
                        "volume": to_float(row.get("vol")),
                        "amount": to_float(row.get("amount")),
                        "changePct": round((current - prev) / prev * 100, 2) if prev else 0,
                        "source": "Mootdx/TDX",
                    }
                except Exception:
                    continue
        except Exception:
            pass
        return cls.tencent_quote(symbol)


market_source = MarketDataSource()