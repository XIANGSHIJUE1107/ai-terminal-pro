# -*- coding: utf-8 -*-
"""
信号层 —— 同花顺 + 东财
强势股 + 题材归因 + 北向资金 + 板块归属
+ 资金流向(push2) + 龙虎榜 + 全市场龙虎榜 + 解禁 + 行业对比
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from backend.data_sources.base import (
    to_float, with_prefix, code6, now_text, now_dt, get_session,
)
from backend.data_sources.rate_limiter import rate_limiter


class SignalDataSource:
    """信号数据源：同花顺 > 东财"""

    # ==================== 强势股（同花顺） ====================
    @staticmethod
    def tonghuashun_strong_stocks(sort: str = "change_pct", limit: int = 50) -> dict[str, Any]:
        """同花顺强势股排行"""
        try:
            session = get_session()
            resp = session.get(
                f"https://q.10jqka.com.cn/index/index/board/all/field/zdf/order/desc/page/1/ajax/1/",
                timeout=15,
                headers={"Referer": "https://q.10jqka.com.cn/"},
            )
            resp.raise_for_status()
            html = resp.text
            import re
            rows = []
            # 匹配表格行
            trs = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S)
            for tr in trs[1:]:  # 跳过表头
                tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)
                if len(tds) < 10:
                    continue
                code = re.sub(r'<[^>]+>', '', tds[0]).strip()
                name = re.sub(r'<[^>]+>', '', tds[1]).strip()
                change_pct = re.sub(r'<[^>]+>', '', tds[2]).strip()
                current = re.sub(r'<[^>]+>', '', tds[3]).strip()
                rows.append({
                    "code": code,
                    "name": name,
                    "changePct": to_float(change_pct),
                    "current": to_float(current),
                    "source": "同花顺强势股",
                })
            return {"items": rows[:limit], "source": "同花顺", "total": len(rows)}
        except Exception as e:
            return {"items": [], "source": "同花顺", "error": str(e)}

    # ==================== 题材归因（同花顺概念板块） ====================
    @staticmethod
    def tonghuashun_concept_attribution(symbol: str) -> dict[str, Any]:
        """同花顺个股题材归因"""
        sym6 = code6(symbol)
        try:
            session = get_session()
            resp = session.get(
                f"https://basic.10jqka.com.cn/{sym6}/",
                timeout=15,
                headers={"Referer": "https://www.10jqka.com.cn/"},
            )
            resp.raise_for_status()
            html = resp.text
            import re
            # 概念板块
            concepts = re.findall(r'<a[^>]*?href="[^"]*?concept[^"]*?"[^>]*?>([^<]+)</a>', html)
            # 行业归属
            industry = re.findall(r'行业[：:]\s*<[^>]*?>([^<]*)<', html)
            return {
                "symbol": sym6,
                "concepts": list(set(c.strip() for c in concepts if c.strip()))[:20],
                "industry": industry[0].strip() if industry else "",
                "source": "同花顺",
            }
        except Exception as e:
            return {"symbol": sym6, "concepts": [], "industry": "", "source": "同花顺", "error": str(e)}

    # ==================== 北向资金（东财 push2） ====================
    @staticmethod
    def eastmoney_north_bound(days: int = 20) -> dict[str, Any]:
        """北向资金流向（东财 push2）"""
        url = (
            "https://push2his.eastmoney.com/api/qt/kamt.kline/get?"
            "fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56&"
            f"klt=101&lmt={days}&"
            f"ut=bd7d9b23aecb96f728aa525fc2c0e468&"
            f"_={int(datetime.now().timestamp() * 1000)}"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"items": [], "error": "circuit_open", "source": "东财北向资金"}
            session = get_session()
            resp = session.get(url, timeout=15, headers={"Referer": "https://data.eastmoney.com/"})
            resp.raise_for_status()
            data = resp.json()
            rate_limiter.record_success(url)
            items = []
            rows = (data.get("data") or {}).get("klines") or []
            for row in rows:
                parts = row.split(",")
                if len(parts) >= 6:
                    items.append({
                        "date": parts[0],
                        "netInflow": round(to_float(parts[1]) / 1e8, 2),  # 亿
                        "balance": round(to_float(parts[2]) / 1e8, 2),
                        "shNetInflow": round(to_float(parts[3]) / 1e8, 2),
                        "shBalance": round(to_float(parts[4]) / 1e8, 2),
                        "szNetInflow": round(to_float(parts[5]) / 1e8, 2),
                        "source": "东财北向资金",
                    })
            return {"items": items, "source": "东财北向资金"}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "source": "东财北向资金", "error": str(e)}

    # ==================== 东财资金流向（push2） ====================
    @staticmethod
    def eastmoney_stock_fundflow(symbol: str, days: int = 120) -> dict[str, Any]:
        """东财个股资金流向（push2 - 120日）"""
        sym6 = code6(symbol)
        market = 1 if sym6.startswith(("5", "6", "9")) else 0
        url = (
            f"https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?"
            f"lmt={days}&klt=101&secid={market}.{sym6}&"
            f"fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63&"
            f"_={int(datetime.now().timestamp() * 1000)}"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"items": [], "error": "circuit_open", "source": "东财资金流"}
            session = get_session()
            resp = session.get(url, timeout=15, headers={"Referer": "https://data.eastmoney.com/"})
            resp.raise_for_status()
            data = resp.json()
            rate_limiter.record_success(url)
            items = []
            klines = (data.get("data") or {}).get("klines") or []
            for row in klines:
                parts = row.split(",")
                if len(parts) >= 12:
                    items.append({
                        "date": parts[0],
                        "mainNetInflow": to_float(parts[1]),  # 主力净流入
                        "smallNetInflow": to_float(parts[2]),  # 小单净流入
                        "midNetInflow": to_float(parts[3]),  # 中单净流入
                        "largeNetInflow": to_float(parts[4]),  # 大单净流入
                        "superLargeNetInflow": to_float(parts[5]),  # 超大单净流入
                        "source": "东财资金流",
                    })
            return {"items": items, "source": "东财个股资金流", "symbol": symbol}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "source": "东财个股资金流", "error": str(e)}

    # ==================== 东财分钟资金流 ====================
    @staticmethod
    def eastmoney_stock_fundflow_minute(symbol: str) -> dict[str, Any]:
        """东财个股分钟级资金流"""
        sym6 = code6(symbol)
        market = 1 if sym6.startswith(("5", "6", "9")) else 0
        url = (
            f"https://push2.eastmoney.com/api/qt/stock/fflow/kline/get?"
            f"lmt=1&klt=1&secid={market}.{sym6}&"
            f"fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63&"
            f"_={int(datetime.now().timestamp() * 1000)}"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"items": [], "error": "circuit_open", "source": "东财分钟资金流"}
            session = get_session()
            resp = session.get(url, timeout=15, headers={"Referer": "https://data.eastmoney.com/"})
            resp.raise_for_status()
            data = resp.json()
            rate_limiter.record_success(url)
            items = []
            klines = (data.get("data") or {}).get("klines") or []
            for row in klines:
                parts = row.split(",")
                if len(parts) >= 12:
                    items.append({
                        "time": parts[0],
                        "mainNetInflow": to_float(parts[1]),
                        "smallNetInflow": to_float(parts[2]),
                        "midNetInflow": to_float(parts[3]),
                        "largeNetInflow": to_float(parts[4]),
                        "superLargeNetInflow": to_float(parts[5]),
                        "source": "东财分钟资金流",
                    })
            return {"items": items, "source": "东财分钟资金流", "symbol": symbol}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "source": "东财分钟资金流", "error": str(e)}

    # ==================== 龙虎榜（东财） ====================
    @staticmethod
    def eastmoney_dragon_tiger(date: str = "", top: int = 50) -> dict[str, Any]:
        """东财龙虎榜个股"""
        if not date:
            date = now_dt().strftime("%Y%m%d")
        url = (
            f"https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?"
            f"lmt=0&klt=101&secid=0.000300&"
            f"fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56&"
            f"_={int(datetime.now().timestamp() * 1000)}"
        )
        try:
            # 使用东财龙虎榜专用接口
            import akshare as ak
            df = ak.stock_lhb_detail_em(date=date)
            if df is not None and not df.empty:
                items = []
                for _, row in df.head(top).iterrows():
                    items.append({
                        "code": str(row.get("代码", "")),
                        "name": str(row.get("名称", "")),
                        "close": to_float(row.get("收盘价")),
                        "changePct": to_float(row.get("涨跌幅")),
                        "turnoverRate": to_float(row.get("换手率")),
                        "lhbNetBuy": to_float(row.get("龙虎榜净买额")),
                        "lhbBuyAmount": to_float(row.get("龙虎榜买入额")),
                        "lhbSellAmount": to_float(row.get("龙虎榜卖出额")),
                        "lhbTotalAmount": to_float(row.get("龙虎榜成交额")),
                        "reason": str(row.get("上榜原因", "")),
                        "date": date,
                        "source": "东财龙虎榜",
                    })
                return {"items": items, "date": date, "source": "东财龙虎榜"}
        except Exception as e:
            pass

        # 备用：东财龙虎榜接口
        try:
            url2 = (
                f"https://datacenter.eastmoney.com/securities/api/data/v1/get?"
                f"reportName=RPT_DAILYBILLBOARD_DETAILSNEW&columns=ALL&"
                f"filter=(TRADE_DATE>='{date[:4]}-{date[4:6]}-{date[6:]}')&"
                f"pageNumber=1&pageSize={top}&sortTypes=-1&sortColumns=TRADE_DATE"
            )
            rate_limiter.wait(url2)
            session = get_session()
            resp = session.get(url2, timeout=15, headers={"Referer": "https://data.eastmoney.com/"})
            resp.raise_for_status()
            data = resp.json()
            rate_limiter.record_success(url2)
            result = data.get("result") or {}
            rows = result.get("data") or []
            items = []
            for row in rows:
                items.append({
                    "code": row.get("SECURITY_CODE", ""),
                    "name": row.get("SECURITY_NAME_ABBR", ""),
                    "close": to_float(row.get("CLOSE_PRICE")),
                    "changePct": to_float(row.get("CHANGE_RATE")),
                    "turnoverRate": to_float(row.get("TURNOVERRATE")),
                    "lhbNetBuy": to_float(row.get("LHB_NET_BUY")),
                    "lhbBuyAmount": to_float(row.get("LHB_BUY_AMOUNT")),
                    "lhbSellAmount": to_float(row.get("LHB_SELL_AMOUNT")),
                    "reason": row.get("LHB_REASON", ""),
                    "date": row.get("TRADE_DATE", ""),
                    "source": "东财龙虎榜",
                })
            return {"items": items, "date": date, "source": "东财龙虎榜"}
        except Exception as e:
            rate_limiter.record_failure(url2) if 'url2' in dir() else None
            return {"items": [], "date": date, "source": "东财龙虎榜", "error": str(e)}

    # ==================== 解禁数据（东财） ====================
    @staticmethod
    def eastmoney_lockup_expiry(days: int = 30) -> dict[str, Any]:
        """东财限售解禁"""
        start = now_dt().strftime("%Y-%m-%d")
        end = (now_dt() + timedelta(days=days)).strftime("%Y-%m-%d")
        url = (
            f"https://datacenter.eastmoney.com/securities/api/data/v1/get?"
            f"reportName=RPT_LIFT_STOCKDETAIL&columns=ALL&"
            f"filter=(LIFT_DATE>='{start}')(LIFT_DATE<='{end}')&"
            f"pageNumber=1&pageSize=100&sortTypes=1&sortColumns=LIFT_DATE&"
            f"source=HSF10&client=PC"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"items": [], "error": "circuit_open", "source": "东财解禁"}
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
                    "code": row.get("SECURITY_CODE", ""),
                    "name": row.get("SECURITY_NAME_ABBR", ""),
                    "liftDate": row.get("LIFT_DATE", ""),
                    "liftShares": to_float(row.get("LIFT_SHARES")),
                    "liftMarketCap": to_float(row.get("LIFT_MARKET_CAP")),
                    "liftRatio": to_float(row.get("LIFT_RATIO")),
                    "source": "东财解禁",
                })
            return {"items": items, "source": "东财限售解禁", "start": start, "end": end}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "source": "东财限售解禁", "error": str(e)}

    # ==================== 行业对比（东财） ====================
    @staticmethod
    def eastmoney_sector_compare(sector_name: str, top: int = 20) -> dict[str, Any]:
        """东财行业板块内个股对比"""
        try:
            import akshare as ak
            df = ak.stock_board_industry_cons_em(symbol=sector_name)
            if df is not None and not df.empty:
                items = []
                for _, row in df.head(top).iterrows():
                    items.append({
                        "code": str(row.get("代码", "")),
                        "name": str(row.get("名称", "")),
                        "current": to_float(row.get("最新价")),
                        "changePct": to_float(row.get("涨跌幅")),
                        "volume": to_float(row.get("成交量")),
                        "amount": to_float(row.get("成交额")),
                        "source": "东财行业对比",
                    })
                return {"items": items, "sector": sector_name, "source": "东财行业对比"}
        except Exception as e:
            return {"items": [], "sector": sector_name, "source": "东财行业对比", "error": str(e)}

    # ==================== 综合信号 ====================
    @classmethod
    def get_stock_signals(cls, symbol: str) -> dict[str, Any]:
        """获取个股综合信号"""
        return {
            "symbol": symbol,
            "attribution": cls.tonghuashun_concept_attribution(symbol),
            "fundflow": cls.eastmoney_stock_fundflow(symbol, days=5),
            "source": "同花顺+东财",
            "updatedAt": now_text(),
        }


signal_source = SignalDataSource()