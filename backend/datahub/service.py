# -*- coding: utf-8 -*-
"""
A 股全栈数据 · 七层架构 · V3.2.4
DataHub 核心服务 —— 集成全部七层数据源
优先级：mootdx/腾讯 不封IP 优先用；东财仅用于独有数据，已内置限流防封
"""

from __future__ import annotations

import json
import os
import threading
from copy import deepcopy
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from backend.config import A_INDEX_CODES, ETF_LIST, PORTFOLIO, GLOBAL_INDEX_CODES
from backend.services.market_service import market_service

# 七层数据源
from backend.data_sources.market import market_source
from backend.data_sources.research import research_source
from backend.data_sources.signal import signal_source
from backend.data_sources.fundflow import fundflow_source
from backend.data_sources.news import news_source
from backend.data_sources.fundamental import fundamental_source
from backend.data_sources.announcement import announcement_source
from backend.data_sources.base import (
    to_float, with_prefix, code6, now_text, now_dt,
    TDX_SERVERS, probe_tdx,
)
from backend.data_sources.rate_limiter import rate_limiter


BASE_DIR = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = BASE_DIR / "datahub_snapshots"
LATEST_DIR = SNAPSHOT_DIR / "latest"
HISTORY_DIR = SNAPSHOT_DIR / "history"
STATE_FILE = SNAPSHOT_DIR / "state.json"
LATEST_FILE = SNAPSHOT_DIR / "latest.json"
REFRESH_INTERVAL_SECONDS = int(os.getenv("DATAHUB_REFRESH_INTERVAL", "600"))
DEFAULT_AS_OF = os.getenv("DATAHUB_AS_OF_DATE", "2026-06-23")

TERMINAL_INDEXES = {
    "sh000001": "上证指数",
    "sh000300": "沪深300",
    "sh000688": "科创50",
    "sz399001": "深证成指",
    "sz399006": "创业板指",
}

NEWS_KEYWORDS = [
    "机器人", "AI", "算力", "半导体", "低空", "航天", "通信", "ETF", "资金流",
]

for directory in (SNAPSHOT_DIR, LATEST_DIR, HISTORY_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def read_json_file(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def snapshot_key() -> str:
    return now_dt().strftime("%Y%m%d_%H%M%S")


def calc_ma(values: list[float], period: int) -> list[float | None]:
    items: list[float | None] = []
    for idx in range(len(values)):
        if idx + 1 < period:
            items.append(None)
            continue
        window = values[idx + 1 - period : idx + 1]
        items.append(sum(window) / period)
    return items


def calc_ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    factor = 2 / (period + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append(value * factor + result[-1] * (1 - factor))
    return result


def calc_rsi(values: list[float], period: int = 14) -> list[float | None]:
    if len(values) < 2:
        return [None for _ in values]
    result: list[float | None] = [None]
    avg_gain = 0.0
    avg_loss = 0.0
    for idx in range(1, len(values)):
        delta = values[idx] - values[idx - 1]
        gain = max(delta, 0)
        loss = max(-delta, 0)
        if idx < period:
            avg_gain += gain
            avg_loss += loss
            result.append(None)
            continue
        if idx == period:
            avg_gain = (avg_gain + gain) / period
            avg_loss = (avg_loss + loss) / period
        else:
            avg_gain = ((avg_gain * (period - 1)) + gain) / period
            avg_loss = ((avg_loss * (period - 1)) + loss) / period
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100 - (100 / (1 + rs)))
    return result


def calc_indicators(kline: list[dict]) -> dict[str, Any]:
    if not kline:
        return {}
    closes = [to_float(item.get("close")) for item in kline]
    ma5 = calc_ma(closes, 5)
    ma10 = calc_ma(closes, 10)
    ma20 = calc_ma(closes, 20)
    ma60 = calc_ma(closes, 60)
    ema12 = calc_ema(closes, 12)
    ema26 = calc_ema(closes, 26)
    dif = [a - b for a, b in zip(ema12, ema26)]
    dea = calc_ema(dif, 9) if dif else []
    macd = [(a - b) * 2 for a, b in zip(dif, dea)] if dif and dea else []
    rsi14 = calc_rsi(closes, 14)
    latest = kline[-1]
    previous = kline[-2] if len(kline) > 1 else latest
    close = to_float(latest.get("close"))
    prev_close = to_float(previous.get("close"), close)
    change_pct = ((close - prev_close) / prev_close * 100) if prev_close else 0
    boll_upper = boll_mid = boll_lower = None
    if len(closes) >= 20:
        window = closes[-20:]
        mean = sum(window) / 20
        variance = sum((item - mean) ** 2 for item in window) / 20
        std = variance ** 0.5
        boll_upper = mean + 2 * std
        boll_mid = mean
        boll_lower = mean - 2 * std
    return {
        "latestPrice": round(close, 2),
        "changePct": round(change_pct, 2),
        "ma5": round(ma5[-1], 2) if ma5 and ma5[-1] is not None else None,
        "ma10": round(ma10[-1], 2) if ma10 and ma10[-1] is not None else None,
        "ma20": round(ma20[-1], 2) if ma20 and ma20[-1] is not None else None,
        "ma60": round(ma60[-1], 2) if ma60 and ma60[-1] is not None else None,
        "dif": round(dif[-1], 4) if dif else None,
        "dea": round(dea[-1], 4) if dea else None,
        "macd": round(macd[-1], 4) if macd else None,
        "rsi14": round(rsi14[-1], 2) if rsi14 and rsi14[-1] is not None else None,
        "bollUpper": round(boll_upper, 2) if boll_upper is not None else None,
        "bollMid": round(boll_mid, 2) if boll_mid is not None else None,
        "bollLower": round(boll_lower, 2) if boll_lower is not None else None,
    }


def read_stock_snapshot() -> dict[str, dict]:
    raw = read_json_file(BASE_DIR / "stock_data.json", {})
    rows: dict[str, dict] = {}
    for code, item in raw.items():
        sym = with_prefix(code)
        prev_close = to_float(item.get("昨收") or item.get("前收"))
        current = to_float(item.get("现价") or item.get("今收"))
        rows[sym] = {
            "symbol": sym,
            "name": item.get("简称") or code,
            "prevClose": prev_close,
            "current": current,
            "open": to_float(item.get("今开")),
            "high": to_float(item.get("最高")),
            "low": to_float(item.get("最低")),
            "volume": to_float(item.get("成交量")),
            "amount": to_float(item.get("成交额")),
            "changePct": to_float(item.get("涨跌幅"), ((current - prev_close) / prev_close * 100) if prev_close else 0),
            "source": "local-stock-snapshot",
            "updatedAt": now_text(),
            "asOf": DEFAULT_AS_OF,
            "freshness": "stale-cache",
            "stale": True,
            "unavailable": False,
            "errors": [],
        }
    return rows


def read_sector_snapshot() -> dict[str, dict]:
    raw = read_json_file(BASE_DIR / "sector_data.json", {})
    rows: dict[str, dict] = {}
    for code, item in raw.items():
        rows[code] = {
            "code": code,
            "name": item.get("简称") or code,
            "price": to_float(item.get("现价")),
            "changePct": to_float(item.get("涨跌幅")),
            "amount": to_float(item.get("成交额")),
            "netInflow": to_float(item.get("当日净流入额")),
            "netInflowRate": to_float(item.get("当日净流入率")),
            "institutionNetInflow": to_float(item.get("机构资金净流入")),
            "source": "local-sector-snapshot",
            "updatedAt": now_text(),
            "asOf": DEFAULT_AS_OF,
            "freshness": "stale-cache",
            "stale": True,
            "unavailable": False,
            "errors": [],
        }
    return rows


# ==================== 写快照 ====================
def write_snapshot(kind: str, payload: dict) -> None:
    history_path = HISTORY_DIR / kind / f"{snapshot_key()}.json"
    latest_path = LATEST_DIR / f"{kind}.json"
    write_json_file(history_path, payload)
    write_json_file(latest_path, payload)


@dataclass
class RefreshState:
    last_update_time: str | None = None
    next_update_time: str | None = None
    refresh_interval_seconds: int = REFRESH_INTERVAL_SECONDS
    status: str = "idle"
    last_error: str | None = None
    is_refreshing: bool = False


class DataHubService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest_result: dict[str, Any] | None = None
        self._state = RefreshState()

    def _persist_state(self) -> None:
        write_json_file(STATE_FILE, asdict(self._state))

    def state(self) -> dict[str, Any]:
        persisted = read_json_file(STATE_FILE, {})
        state = asdict(self._state)
        if persisted:
            state.update({key: value for key, value in persisted.items() if key in state})
        return state

    def health(self) -> dict[str, Any]:
        state = self.state()
        rate_stats = rate_limiter.get_stats()
        return {
            "status": "ok" if state.get("status") != "error" else "degraded",
            "platform": "AI智能投研分析平台",
            "version": "V3.2.4",
            "service": "DataHub 七层架构",
            "source": "mootdx/TDX > Tencent > 百度K线 > 东财(限流) > 同花顺 > 新浪 > 巨潮cninfo",
            "updatedAt": state.get("last_update_time"),
            "asOf": DEFAULT_AS_OF,
            "freshness": "scheduled-cache",
            "stale": False,
            "unavailable": False,
            "errors": [] if not state.get("last_error") else [{"source": "scheduler", "message": state["last_error"]}],
            "refresh": state,
            "last_update_time": state.get("last_update_time"),
            "next_update_time": state.get("next_update_time"),
            "refresh_interval_seconds": state.get("refresh_interval_seconds"),
            "last_error": state.get("last_error"),
            "rate_limiter": rate_stats,
            "data_sources": {
                "行情层": {"mootdx": True, "tencent": True, "baidu": True},
                "研报层": {"eastmoney_report": True, "tonghuashun": True, "iwencai": True},
                "信号层": {"tonghuashun": True, "eastmoney": True},
                "资金面": {"eastmoney_datacenter": True, "eastmoney_push2": True},
                "新闻层": {"eastmoney_http": True, "sina": True, "tonghuashun": True},
                "基础数据": {"mootdx_f10": True, "eastmoney": True, "sina": True},
                "公告层": {"cninfo": True, "mootdx": True, "eastmoney": True},
            },
        }

    # ==================== 行情获取（使用新数据源） ====================
    def normalize_quotes(self, symbols: list[str]) -> dict[str, dict]:
        local_snapshot = read_stock_snapshot()
        rows: dict[str, dict] = {}
        for symbol in symbols:
            sym = with_prefix(symbol)
            errors: list[dict] = []
            quote = None

            # 全球指数：走 AKShare 实时行情，不使用 A 股行情源
            raw_code = str(symbol).strip().upper()
            if raw_code in GLOBAL_INDEX_CODES or raw_code in {"KS11", "N225", "HSI", "HSTECH", "GDAXI", "VIX"}:
                try:
                    item = market_service._fetch_global_index_spot(raw_code)
                    if item and item.get("close") is not None:
                        quote = {
                            "symbol": raw_code,
                            "name": item.get("name", raw_code),
                            "current": item.get("close"),
                            "prevClose": item.get("prev_close"),
                            "open": item.get("open"),
                            "high": item.get("high"),
                            "low": item.get("low"),
                            "volume": item.get("volume", 0),
                            "amount": item.get("amount", 0),
                            "changePct": item.get("change_pct"),
                            "source": item.get("source", "akshare"),
                        }
                except Exception as exc:
                    errors.append({"source": "akshare-global", "symbol": raw_code, "message": str(exc)})
                if quote and quote.get("current") is not None:
                    as_of = DEFAULT_AS_OF
                    try:
                        daily = market_service._fetch_global_index_kline(raw_code, days=5)
                        if daily:
                            as_of = daily[-1].get("date") or DEFAULT_AS_OF
                    except Exception:
                        pass
                    quote.update({
                        "updatedAt": now_text(),
                        "asOf": as_of,
                        "freshness": "realtime",
                        "stale": False,
                        "unavailable": False,
                        "errors": errors,
                    })
                    rows[raw_code] = quote
                    continue

            # 使用新行情数据源（mootdx 含五档盘口 > 腾讯 含PE/PB/市值）
            try:
                quote = market_source.get_quote(sym)
                if quote.get("current") is None:
                    quote = None
            except Exception as exc:
                errors.append({"source": "Mootdx/TDX > Tencent", "symbol": sym, "message": str(exc)})

            as_of = DEFAULT_AS_OF
            try:
                daily = self.get_kline(sym, 240, 5)
                if daily:
                    as_of = daily[-1].get("date") or DEFAULT_AS_OF
            except Exception:
                pass

            if quote and quote.get("current"):
                quote.update({
                    "updatedAt": now_text(),
                    "asOf": as_of,
                    "freshness": "realtime",
                    "stale": False,
                    "unavailable": False,
                    "errors": errors,
                })
                rows[sym] = quote
                continue

            cached = deepcopy(local_snapshot.get(sym))
            if cached:
                cached["updatedAt"] = now_text()
                cached["asOf"] = cached.get("asOf") or DEFAULT_AS_OF
                cached["errors"] = errors + [{"source": "snapshot", "message": "live quote unavailable, using local snapshot"}]
                rows[sym] = cached
            else:
                rows[sym] = {
                    "symbol": sym,
                    "name": sym,
                    "current": None,
                    "prevClose": None,
                    "changePct": None,
                    "source": "unavailable",
                    "updatedAt": now_text(),
                    "asOf": as_of,
                    "freshness": "unavailable",
                    "stale": True,
                    "unavailable": True,
                    "errors": errors,
                }
        return rows

    def get_kline(self, symbol: str, scale: int, length: int) -> list[dict]:
        """K线获取：腾讯 > 百度 > AKShare"""
        try:
            data = market_source.get_kline(symbol, length)
            if data:
                return data
        except Exception:
            pass
        # Fallback: local DB
        try:
            detail = market_service.get_stock_detail(code6(symbol), days=max(length, 60))
            data = detail.get("kline", [])
            if data:
                return data[-length:]
        except Exception:
            pass
        return []

    def _etf_symbol_map(self) -> dict[str, str]:
        merged = dict(ETF_LIST)
        return merged

    # ==================== 构建最新快照 ====================
    def build_latest(self) -> dict[str, Any]:
        portfolio_quotes = self.normalize_quotes(list(PORTFOLIO.values()))
        index_quotes = self.normalize_quotes(list(TERMINAL_INDEXES.keys()))
        etf_quotes = self.normalize_quotes(list(self._etf_symbol_map().values()))

        # 行业资金流（东财直连，失败时回落本地快照）
        sector_result = fundflow_source.eastmoney_sector_fundflow()
        sector_live = sector_result.get("items", [])
        sector_errors = [{"source": sector_result["source"], "message": sector_result.get("error", "")}] if sector_result.get("error") else []
        sector_snapshot = read_sector_snapshot()

        # 新闻（东财直连HTTP）
        news_result = news_source.get_news(limit=40)
        news_items = news_result.get("items", [])
        news_errors = [{"source": news_result["source"], "message": news_result.get("error", "")}] if news_result.get("error") else []

        # 市场数据
        market = market_service.get_index_overview()
        breadth = market_service.get_market_breadth()
        fund_flow = market_service.get_sector_flow_data()[:20]

        sectors = sector_live[:] if sector_live else list(sector_snapshot.values())
        sectors = sorted(sectors, key=lambda item: to_float(item.get("netInflow") or item.get("mainNetInflow")), reverse=True)
        portfolio_items = list(portfolio_quotes.values())
        index_items = list(index_quotes.values())
        etf_items = list(etf_quotes.values())

        technicals = {
            symbol: calc_indicators(self.get_kline(symbol, 240, 80))
            for symbol in list(PORTFOLIO.values())[:8]
        }
        as_of_candidates = []
        for symbol in list(PORTFOLIO.values())[:3]:
            kline = self.get_kline(symbol, 240, 3)
            if kline:
                as_of_candidates.append(kline[-1].get("date"))
        as_of = max([item for item in as_of_candidates if item], default=DEFAULT_AS_OF)

        risk_notes = []
        if any(item.get("stale") for item in portfolio_items + index_items + etf_items):
            risk_notes.append("部分实时源失败，当前展示含本地快照兜底，请结合 stale 标记判断。")
        if any(item.get("sentiment") == "negative" for item in news_items[:10]):
            risk_notes.append("新闻中存在负面事件，请关注盘后公告与行业资金流变化。")
        if not risk_notes:
            risk_notes.append("核心链路正常，七层数据源运行中。")

        analytics = {
            "indexStatus": "up" if sum((item.get("changePct") or 0) for item in index_items[:3]) >= 0 else "down",
            "portfolioStatus": [
                {"symbol": item.get("symbol"), "name": item.get("name"), "changePct": item.get("changePct"), "source": item.get("source"), "asOf": item.get("asOf")}
                for item in portfolio_items
            ],
            "etfStatus": [
                {"symbol": item.get("symbol"), "name": item.get("name"), "changePct": item.get("changePct"), "source": item.get("source"), "asOf": item.get("asOf")}
                for item in etf_items
            ],
            "sectorRankings": sectors[:10],
            "newsSummary": news_items[:12],
            "riskNotes": risk_notes,
            "techIndicators": technicals,
            "breadth": breadth,
            "fundFlowTop": fund_flow[:10],
        }

        real_count = sum(1 for item in portfolio_items + index_items + etf_items if not item.get("stale") and not item.get("unavailable"))
        refresh_state = self.state()
        payload = {
            "source": "mootdx/TDX > Tencent > 百度K线 > 东财(限流) > 同花顺 > 新浪 > 巨潮cninfo",
            "updatedAt": now_text(),
            "asOf": as_of,
            "freshness": "realtime" if real_count else "stale-cache",
            "stale": real_count == 0,
            "unavailable": False,
            "errors": sector_errors + news_errors,
            "status": "ok",
            "raw": {
                "portfolio": portfolio_items,
                "indices": index_items,
                "etfs": etf_items,
                "sectors": sectors[:20],
                "news": news_items[:20],
                "items": news_items[:20],
            },
            "normalized": {
                "portfolio": portfolio_items,
                "indices": index_items,
                "etfs": etf_items,
                "sectorRankings": sectors[:20],
                "fundFlow": fund_flow,
                "news": news_items[:20],
                "items": news_items[:20],
            },
            "analysis": analytics,
            "data": {
                "portfolio": portfolio_items,
                "indices": index_items,
                "etfs": etf_items,
                "sectorRankings": sectors[:20],
                "fundFlow": fund_flow,
                "news": news_items[:20],
                "items": news_items[:20],
                "analytics": analytics,
                "market": market,
                "refresh": refresh_state,
                "newsSource": news_result.get("source", "东财"),
                "sectorSource": sector_result.get("source", "东财"),
            },
        }
        payload["items"] = payload["data"]
        return payload

    # ==================== 研报接口 ====================
    def research_reports(self, symbol: str, page: int = 1) -> dict[str, Any]:
        return research_source.get_stock_reports(symbol, page)

    def research_industry_reports(self, industry: str = "", page: int = 1) -> dict[str, Any]:
        return research_source.get_industry_reports(industry, page)

    def research_consensus(self, symbol: str) -> dict[str, Any]:
        return research_source.eastmoney_consensus(symbol)

    def research_iwencai(self, query: str) -> dict[str, Any]:
        return research_source.iwencai_search(query)

    # ==================== 信号接口 ====================
    def signal_strong_stocks(self, sort: str = "change_pct", limit: int = 50) -> dict[str, Any]:
        return signal_source.tonghuashun_strong_stocks(sort, limit)

    def signal_stock_attribution(self, symbol: str) -> dict[str, Any]:
        return signal_source.tonghuashun_concept_attribution(symbol)

    def signal_north_bound(self, days: int = 20) -> dict[str, Any]:
        return signal_source.eastmoney_north_bound(days)

    def signal_dragon_tiger(self, date: str = "", top: int = 50) -> dict[str, Any]:
        return signal_source.eastmoney_dragon_tiger(date, top)

    def signal_lockup_expiry(self, days: int = 30) -> dict[str, Any]:
        return signal_source.eastmoney_lockup_expiry(days)

    def signal_sector_compare(self, sector_name: str, top: int = 20) -> dict[str, Any]:
        return signal_source.eastmoney_sector_compare(sector_name, top)

    def signal_stock_full(self, symbol: str) -> dict[str, Any]:
        return signal_source.get_stock_signals(symbol)

    # ==================== 资金面接口 ====================
    def fundflow_margin(self, symbol: str, days: int = 60) -> dict[str, Any]:
        return fundflow_source.eastmoney_margin_trading(symbol, days)

    def fundflow_block_trade(self, symbol: str = "", days: int = 30) -> dict[str, Any]:
        return fundflow_source.eastmoney_block_trade(symbol, days)

    def fundflow_shareholder(self, symbol: str) -> dict[str, Any]:
        return fundflow_source.eastmoney_shareholder_count(symbol)

    def fundflow_dividend(self, symbol: str) -> dict[str, Any]:
        return fundflow_source.eastmoney_dividend(symbol)

    def fundflow_stock_fundflow(self, symbol: str, days: int = 120) -> dict[str, Any]:
        return signal_source.eastmoney_stock_fundflow(symbol, days)

    def fundflow_stock_minute(self, symbol: str) -> dict[str, Any]:
        return signal_source.eastmoney_stock_fundflow_minute(symbol)

    def fundflow_stock_full(self, symbol: str) -> dict[str, Any]:
        return fundflow_source.get_stock_fundflow(symbol)

    # ==================== 新闻接口 ====================
    def news(self) -> dict[str, Any]:
        result = news_source.get_news(limit=40)
        items = result.get("items", [])
        return {
            "source": result.get("source", "东财"),
            "updatedAt": now_text(),
            "asOf": DEFAULT_AS_OF,
            "freshness": "realtime" if items else "unavailable",
            "stale": not bool(items),
            "unavailable": not bool(items),
            "errors": [{"source": result["source"], "message": result.get("error", "")}] if result.get("error") else [],
            "data": {"items": items, "news": items, "count": len(items), "total": len(items)},
            "items": items,
            "news": items,
            "count": len(items),
            "total": len(items),
        }

    def news_stock(self, symbol: str, limit: int = 30) -> dict[str, Any]:
        return news_source.get_stock_news(symbol, limit)

    def news_global(self, limit: int = 30) -> dict[str, Any]:
        return news_source.get_global_news(limit)

    # ==================== 基础数据接口 ====================
    def fundamental_f10(self, symbol: str, category: str = "cwzy") -> dict[str, Any]:
        return fundamental_source.mootdx_f10(symbol, category)

    def fundamental_f10_all(self, symbol: str) -> dict[str, Any]:
        return fundamental_source.mootdx_f10_all(symbol)

    def fundamental_quarterly(self, symbol: str) -> dict[str, Any]:
        return fundamental_source.eastmoney_quarterly_report(symbol)

    def fundamental_balance_sheet(self, symbol: str) -> dict[str, Any]:
        return fundamental_source.eastmoney_balance_sheet(symbol)

    def fundamental_cashflow(self, symbol: str) -> dict[str, Any]:
        return fundamental_source.eastmoney_cashflow(symbol)

    def fundamental_stock_full(self, symbol: str) -> dict[str, Any]:
        return fundamental_source.get_stock_fundamental(symbol)

    # ==================== 公告接口 ====================
    def announcements(self, symbol: str = "", page: int = 1, pagesize: int = 30, days: int = 7) -> dict[str, Any]:
        return announcement_source.get_announcements(symbol, page, pagesize, days)

    def announcements_stock(self, symbol: str, page: int = 1, pagesize: int = 30) -> dict[str, Any]:
        return announcement_source.get_stock_announcements(symbol, page, pagesize)

    def announcements_latest(self, days: int = 3, pagesize: int = 50) -> dict[str, Any]:
        return announcement_source.get_latest_announcements(days, pagesize)

    # ==================== 原有接口 ====================
    def latest(self) -> dict[str, Any]:
        if self._latest_result:
            return self._latest_result
        cached = read_json_file(LATEST_FILE, {})
        if cached:
            return cached
        refresh_state = self.state()
        return {
            "source": "DataHub",
            "updatedAt": now_text(),
            "asOf": DEFAULT_AS_OF,
            "freshness": "local-cache",
            "stale": True,
            "unavailable": False,
            "errors": [],
            "data": {"refresh": refresh_state},
            "items": {"refresh": refresh_state},
        }

    def snapshot_list(self, kind: str | None = None) -> list[dict]:
        if kind:
            paths = sorted((HISTORY_DIR / kind).glob("*.json"))
        else:
            paths = sorted(HISTORY_DIR.glob("*/*.json"))
        items: list[dict] = []
        for path in paths[-500:]:
            payload = read_json_file(path, None)
            if not payload:
                continue
            items.append({
                "kind": path.parent.name,
                "path": str(path),
                "updatedAt": payload.get("updatedAt"),
                "asOf": payload.get("asOf"),
                "source": payload.get("source"),
                "status": payload.get("status"),
                "stale": payload.get("stale"),
                "unavailable": payload.get("unavailable"),
            })
        return list(reversed(items))

    def refresh(self, force: bool = False) -> dict[str, Any]:
        if not self._lock.acquire(blocking=False):
            busy_state = self.state()
            return {
                "source": "DataHub",
                "updatedAt": now_text(),
                "asOf": DEFAULT_AS_OF,
                "freshness": "busy",
                "stale": True,
                "unavailable": False,
                "errors": [{"source": "refresh", "message": "refresh already running"}],
                "data": {"refresh": busy_state},
                "items": {"refresh": busy_state},
            }
        try:
            self._state.status = "running"
            self._state.is_refreshing = True
            self._state.last_error = None
            self._persist_state()
            latest = self.build_latest()
            self._latest_result = latest
            self._state.last_update_time = latest["updatedAt"]
            self._state.next_update_time = (now_dt() + timedelta(seconds=self._state.refresh_interval_seconds)).strftime("%Y-%m-%d %H:%M:%S")
            self._state.status = "ok"
            self._state.is_refreshing = False
            latest["data"]["refresh"] = self.state()
            latest["items"] = latest["data"]
            write_json_file(LATEST_FILE, latest)
            write_snapshot("latest", latest)
            write_snapshot(
                "refresh",
                {
                    "source": latest["source"],
                    "updatedAt": latest["updatedAt"],
                    "asOf": latest["asOf"],
                    "status": self._state.status,
                    "raw": {},
                    "normalized": {"refresh": self.state()},
                    "analysis": {},
                    "errors": [],
                },
            )
            self._persist_state()
            return latest
        except Exception as exc:
            self._state.status = "error"
            self._state.is_refreshing = False
            self._state.last_error = str(exc)
            self._state.next_update_time = (now_dt() + timedelta(seconds=self._state.refresh_interval_seconds)).strftime("%Y-%m-%d %H:%M:%S")
            self._persist_state()
            return {
                "source": "DataHub",
                "updatedAt": now_text(),
                "asOf": DEFAULT_AS_OF,
                "freshness": "unavailable",
                "stale": True,
                "unavailable": True,
                "errors": [{"source": "refresh", "message": str(exc)}],
                "data": {"refresh": self.state()},
                "items": {"refresh": self.state()},
            }
        finally:
            self._lock.release()

    def portfolio(self) -> dict[str, Any]:
        items = list(self.normalize_quotes(list(PORTFOLIO.values())).values())
        as_of = max((item.get("asOf") for item in items if item.get("asOf")), default=DEFAULT_AS_OF)
        payload = {
            "source": "mootdx/TDX > Tencent > local-stock-snapshot",
            "updatedAt": now_text(),
            "asOf": as_of,
            "freshness": "realtime" if any(not item.get("stale") for item in items) else "stale-cache",
            "stale": not any(not item.get("stale") for item in items),
            "unavailable": False,
            "errors": [],
            "data": {"items": items},
            "items": items,
        }
        write_snapshot("portfolio", payload)
        return payload

    def quotes(self, symbols: list[str]) -> dict[str, Any]:
        rows = self.normalize_quotes(symbols)
        as_of = max((item.get("asOf") for item in rows.values() if item.get("asOf")), default=DEFAULT_AS_OF)
        payload = {
            "source": "mootdx/TDX > Tencent > 百度K线 > 东财(限流) > 同花顺 > 新浪 > 巨潮cninfo",
            "updatedAt": now_text(),
            "asOf": as_of,
            "freshness": "realtime" if any(not item.get("stale") for item in rows.values()) else "stale-cache",
            "stale": not any(not item.get("stale") for item in rows.values()),
            "unavailable": False,
            "errors": [],
            "data": {"quotes": rows},
            "items": {"quotes": rows},
        }
        write_snapshot("quotes", payload)
        return payload

    def sectors(self, refresh: bool = False) -> dict[str, Any]:
        if refresh:
            self.refresh(force=True)
        latest = self.latest()
        items = latest.get("data", {}).get("sectorRankings", [])
        payload = {
            "source": latest.get("data", {}).get("sectorSource") or "东财行业资金流 > local-sector-snapshot",
            "updatedAt": latest.get("updatedAt") or now_text(),
            "asOf": latest.get("asOf") or DEFAULT_AS_OF,
            "freshness": latest.get("freshness", "stale-cache"),
            "stale": latest.get("stale", True),
            "unavailable": False,
            "errors": latest.get("errors", []),
            "data": {"items": items},
            "items": items,
        }
        write_snapshot("sectors", payload)
        return payload

    def kline(self, symbol: str, scale: int = 240, length: int = 120) -> dict[str, Any]:
        items = self.get_kline(symbol, scale, length)
        indicators = calc_indicators(items)
        as_of = items[-1]["date"] if items else DEFAULT_AS_OF
        payload = {
            "source": "腾讯K线 > 百度K线 > AKShare > local-db",
            "updatedAt": now_text(),
            "asOf": as_of,
            "freshness": "realtime" if items else "unavailable",
            "stale": not bool(items),
            "unavailable": not bool(items),
            "errors": [],
            "data": {
                "symbol": with_prefix(symbol),
                "scale": scale,
                "items": items,
                "kline": items,
                "indicators": indicators,
            },
            "items": items,
        }
        write_snapshot(f"kline-{code6(symbol)}-{scale}", payload)
        return payload

    def sector_history(self, name: str, days: int = 30) -> dict[str, Any]:
        snapshot = read_sector_snapshot()
        matched = None
        for item in snapshot.values():
            title = item.get("name", "")
            if name and (name in title or title in name):
                matched = item
                break
        history = []
        if matched:
            for offset in range(days - 1, -1, -1):
                date = (now_dt() - timedelta(days=offset)).strftime("%Y-%m-%d")
                history.append({
                    "date": date,
                    "sector_name": matched.get("name") or name,
                    "main_net_inflow": matched.get("netInflow", 0),
                    "super_large_net": 0,
                    "large_net": matched.get("institutionNetInflow", 0),
                    "mid_net": 0,
                    "small_net": 0,
                    "change_pct": matched.get("changePct", 0),
                    "snapshot": True,
                })
        payload = {
            "source": "local-sector-snapshot",
            "updatedAt": now_text(),
            "asOf": DEFAULT_AS_OF,
            "freshness": "snapshot" if history else "unavailable",
            "stale": True,
            "unavailable": not bool(history),
            "errors": [] if history else [{"source": "sector-history", "message": f"sector not found: {name}"}],
            "data": {"name": name, "history": history},
            "items": history,
        }
        write_snapshot("sector-history", payload)
        return payload


datahub_service = DataHubService()
