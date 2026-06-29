# -*- coding: utf-8 -*-
"""
资金面 —— 东财 datacenter + push2
融资融券 + 大宗交易 + 股东户数 + 分红送转 + 资金流(分钟+120日)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.data_sources.base import (
    to_float, with_prefix, code6, now_text, now_dt, get_session,
)
from backend.data_sources.rate_limiter import rate_limiter


class FundFlowDataSource:
    """资金面数据源：东财 datacenter + push2"""

    # ==================== 融资融券（东财 datacenter） ====================
    @staticmethod
    def eastmoney_margin_trading(symbol: str, days: int = 60) -> dict[str, Any]:
        """个股融资融券数据"""
        sym6 = code6(symbol)
        market = 1 if sym6.startswith(("5", "6", "9")) else 0
        url = (
            f"https://datacenter.eastmoney.com/securities/api/data/v1/get?"
            f"reportName=RPT_MARGIN_DETAIL&columns=ALL&"
            f"filter=(SECURITY_CODE=%22{sym6}%22)(MARKET=%22{market}%22)&"
            f"pageNumber=1&pageSize={days}&sortTypes=-1&sortColumns=TRADE_DATE&"
            f"source=HSF10&client=PC"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"items": [], "error": "circuit_open", "source": "东财融资融券"}
            session = get_session()
            resp = session.get(url, timeout=15, headers={"Referer": "https://data.eastmoney.com/"})
            resp.raise_for_status()
            data = resp.json()
            rate_limiter.record_success(url)
            result = data.get("result") or {}
            rows = result.get("data") or []
            items = []
            for row in rows:
                items.append({
                    "date": row.get("TRADE_DATE", ""),
                    "rzye": to_float(row.get("FIN_BALANCE")),  # 融资余额
                    "rqye": to_float(row.get("MARGIN_BALANCE")),  # 融券余额
                    "rzmre": to_float(row.get("FIN_BUY_AMT")),  # 融资买入额
                    "rqyl": to_float(row.get("MARGIN_VOL")),  # 融券余量
                    "rzrqjyzl": to_float(row.get("FIN_MARGIN_BALANCE")),  # 融资融券余额
                    "source": "东财融资融券",
                })
            return {"items": items, "symbol": symbol, "source": "东财融资融券"}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "symbol": symbol, "source": "东财融资融券", "error": str(e)}

    # ==================== 大宗交易（东财） ====================
    @staticmethod
    def eastmoney_block_trade(symbol: str = "", days: int = 30) -> dict[str, Any]:
        """大宗交易数据"""
        sym6 = code6(symbol) if symbol else ""
        start = (now_dt() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        end = now_dt().strftime("%Y-%m-%d")
        filter_str = f"(TRADE_DATE>='{start}')(TRADE_DATE<='{end}')"
        if sym6:
            filter_str = f"(SECURITY_CODE=%22{sym6}%22){filter_str}"
        url = (
            f"https://datacenter.eastmoney.com/securities/api/data/v1/get?"
            f"reportName=RPT_BLOCKTRADE_DETAILS&columns=ALL&"
            f"filter={filter_str}&"
            f"pageNumber=1&pageSize=100&sortTypes=-1&sortColumns=TRADE_DATE&"
            f"source=HSF10&client=PC"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"items": [], "error": "circuit_open", "source": "东财大宗交易"}
            session = get_session()
            resp = session.get(url, timeout=15, headers={"Referer": "https://data.eastmoney.com/"})
            resp.raise_for_status()
            data = resp.json()
            rate_limiter.record_success(url)
            result = data.get("result") or {}
            rows = result.get("data") or []
            items = []
            for row in rows:
                items.append({
                    "date": row.get("TRADE_DATE", ""),
                    "code": row.get("SECURITY_CODE", ""),
                    "name": row.get("SECURITY_NAME_ABBR", ""),
                    "price": to_float(row.get("TRADE_PRICE")),
                    "volume": to_float(row.get("TRADE_VOLUME")),
                    "amount": to_float(row.get("TRADE_AMOUNT")),
                    "buyer": row.get("BUYER_NAME", ""),
                    "seller": row.get("SELLER_NAME", ""),
                    "source": "东财大宗交易",
                })
            return {"items": items, "source": "东财大宗交易", "start": start, "end": end}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "source": "东财大宗交易", "error": str(e)}

    # ==================== 股东户数（东财） ====================
    @staticmethod
    def eastmoney_shareholder_count(symbol: str) -> dict[str, Any]:
        """股东户数变化"""
        sym6 = code6(symbol)
        url = (
            f"https://datacenter.eastmoney.com/securities/api/data/v1/get?"
            f"reportName=RPT_F10_EQUITY_HOLDER&columns=ALL&"
            f"filter=(SECURITY_CODE=%22{sym6}%22)&"
            f"pageNumber=1&pageSize=10&sortTypes=-1&sortColumns=END_DATE&"
            f"source=HSF10&client=PC"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"items": [], "error": "circuit_open", "source": "东财股东户数"}
            session = get_session()
            resp = session.get(url, timeout=15, headers={"Referer": "https://emweb.securities.eastmoney.com/"})
            resp.raise_for_status()
            data = resp.json()
            rate_limiter.record_success(url)
            result = data.get("result") or {}
            rows = result.get("data") or []
            items = []
            for row in rows:
                items.append({
                    "endDate": row.get("END_DATE", ""),
                    "holderCount": int(row.get("TOTAL_SHAREHOLDERS", 0) or 0),
                    "avgShares": to_float(row.get("AVG_SHARES")),
                    "avgMarketCap": to_float(row.get("AVG_MARKET_CAP")),
                    "changeCount": int(row.get("HOLDER_CHANGE", 0) or 0),
                    "changeRatio": to_float(row.get("HOLDER_CHANGE_RATIO")),
                    "source": "东财股东户数",
                })
            return {"items": items, "symbol": symbol, "source": "东财股东户数"}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "symbol": symbol, "source": "东财股东户数", "error": str(e)}

    # ==================== 分红送转（东财） ====================
    @staticmethod
    def eastmoney_dividend(symbol: str) -> dict[str, Any]:
        """分红送转记录"""
        sym6 = code6(symbol)
        url = (
            f"https://datacenter.eastmoney.com/securities/api/data/v1/get?"
            f"reportName=RPT_F10_DIVIDEND&columns=ALL&"
            f"filter=(SECURITY_CODE=%22{sym6}%22)&"
            f"pageNumber=1&pageSize=20&sortTypes=-1&sortColumns=EX_DIVIDEND_DATE&"
            f"source=HSF10&client=PC"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"items": [], "error": "circuit_open", "source": "东财分红送转"}
            session = get_session()
            resp = session.get(url, timeout=15, headers={"Referer": "https://emweb.securities.eastmoney.com/"})
            resp.raise_for_status()
            data = resp.json()
            rate_limiter.record_success(url)
            result = data.get("result") or {}
            rows = result.get("data") or []
            items = []
            for row in rows:
                items.append({
                    "exDate": row.get("EX_DIVIDEND_DATE", ""),  # 除权除息日
                    "divDate": row.get("DIVIDEND_DATE", ""),  # 股息发放日
                    "cashDiv": to_float(row.get("CASH_DIVIDEND")),  # 每股现金分红
                    "bonusShare": to_float(row.get("BONUS_SHARE_RATIO")),  # 送股比例
                    "rightShare": to_float(row.get("RIGHTS_SHARE_RATIO")),  # 转增比例
                    "recordDate": row.get("RECORD_DATE", ""),  # 股权登记日
                    "planExplain": row.get("PLAN_EXPLAIN", ""),  # 分红方案
                    "source": "东财分红送转",
                })
            return {"items": items, "symbol": symbol, "source": "东财分红送转"}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "symbol": symbol, "source": "东财分红送转", "error": str(e)}

    # ==================== 行业板块资金流（东财） ====================
    @staticmethod
    def eastmoney_sector_fundflow() -> dict[str, Any]:
        """行业板块资金流向排行"""
        try:
            import akshare as ak
            df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
            if df is None or df.empty:
                return {"items": [], "source": "东财行业资金流", "error": "empty"}
            items = []
            for _, row in df.iterrows():
                items.append({
                    "name": str(row.get("名称", "")).strip(),
                    "changePct": to_float(row.get("今日涨跌幅")),
                    "mainNetInflow": to_float(row.get("今日主力净流入-净额")),
                    "mainNetInflowRate": to_float(row.get("今日主力净流入-净占比")) / 100,
                    "superLargeNet": to_float(row.get("今日超大单净流入-净额")),
                    "largeNet": to_float(row.get("今日大单净流入-净额")),
                    "midNet": to_float(row.get("今日中单净流入-净额")),
                    "smallNet": to_float(row.get("今日小单净流入-净额")),
                    "leader": str(row.get("今日主力净流入最大股", "")),
                    "source": "东财行业资金流",
                })
            return {"items": items, "source": "东财行业资金流"}
        except Exception as e:
            return {"items": [], "source": "东财行业资金流", "error": str(e)}

    # ==================== 个股资金流（综合） ====================
    @classmethod
    def get_stock_fundflow(cls, symbol: str, days: int = 120) -> dict[str, Any]:
        """个股资金面综合数据"""
        from backend.data_sources.signal import signal_source

        return {
            "symbol": symbol,
            "fundflow": signal_source.eastmoney_stock_fundflow(symbol, days),
            "margin": cls.eastmoney_margin_trading(symbol, min(days, 60)),
            "shareholder": cls.eastmoney_shareholder_count(symbol),
            "dividend": cls.eastmoney_dividend(symbol),
            "source": "东财资金面",
            "updatedAt": now_text(),
        }


fundflow_source = FundFlowDataSource()