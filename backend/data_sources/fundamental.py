# -*- coding: utf-8 -*-
"""
基础数据 —— mootdx + 东财 + 新浪
季报37字段 / F10九大类 / 财报三表
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.data_sources.base import (
    to_float, with_prefix, code6, now_text, now_dt, get_session,
    TDX_SERVERS, probe_tdx,
)
from backend.data_sources.rate_limiter import rate_limiter


class FundamentalDataSource:
    """基础数据源：mootdx > 东财 > 新浪"""

    # ==================== F10 九大类（mootdx） ====================
    F10_CATEGORIES = [
        "gshg",  # 公司概况
        "gdbd",  # 股东变动
        "zygc",  # 主要股东
        "cwzy",  # 财务摘要
        "jbxx",  # 基本信息
        "sdlt",  # 十大流通股东
        "sdlc",  # 十大股东
        "gqjg",  # 股权结构
        "ygbb",  # 高管变动
    ]

    @staticmethod
    def mootdx_f10(symbol: str, category: str = "cwzy") -> dict[str, Any]:
        """mootdx F10 数据"""
        try:
            from mootdx.reader import Reader
        except Exception:
            return {"error": "mootdx not installed", "source": "mootdx F10"}

        sym6 = code6(symbol)
        market = 1 if sym6.startswith(("5", "6", "9")) else 0
        for ip, port in TDX_SERVERS:
            if not probe_tdx(ip, port):
                continue
            try:
                reader = Reader.factory(market="std", server=ip, port=port)
                result = reader.f10(symbol=sym6, market=market, category=category)
                if result:
                    return {
                        "symbol": sym6,
                        "category": category,
                        "data": result,
                        "source": "mootdx F10",
                    }
            except Exception:
                continue
        return {"symbol": sym6, "category": category, "data": {}, "source": "mootdx F10", "error": "all servers failed"}

    @classmethod
    def mootdx_f10_all(cls, symbol: str) -> dict[str, Any]:
        """mootdx F10 全部九大类"""
        result = {}
        for cat in cls.F10_CATEGORIES:
            result[cat] = cls.mootdx_f10(symbol, cat)
        return {
            "symbol": code6(symbol),
            "categories": result,
            "source": "mootdx F10",
            "updatedAt": now_text(),
        }

    # ==================== 季报37字段（东财） ====================
    @staticmethod
    def eastmoney_quarterly_report(symbol: str, report_type: str = "YEAR") -> dict[str, Any]:
        """东财季报/年报37字段"""
        sym6 = code6(symbol)
        url = (
            f"https://datacenter.eastmoney.com/securities/api/data/v1/get?"
            f"reportName=RPT_DMSK_FN_MAININCOMESTATEMENT&columns=ALL&"
            f"filter=(SECURITY_CODE=%22{sym6}%22)&"
            f"pageNumber=1&pageSize=20&sortTypes=-1&sortColumns=REPORT_DATE&"
            f"source=HSF10&client=PC"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"items": [], "error": "circuit_open", "source": "东财季报"}
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
                    "reportDate": row.get("REPORT_DATE", ""),
                    "reportType": row.get("REPORT_TYPE", ""),
                    # 利润表核心字段
                    "revenue": to_float(row.get("TOTAL_OPERATE_INCOME")),  # 营业总收入
                    "operateCost": to_float(row.get("TOTAL_OPERATE_COST")),  # 营业总成本
                    "operateProfit": to_float(row.get("OPERATE_PROFIT")),  # 营业利润
                    "totalProfit": to_float(row.get("TOTAL_PROFIT")),  # 利润总额
                    "netProfit": to_float(row.get("NET_PROFIT")),  # 净利润
                    "parentNetProfit": to_float(row.get("PARENT_NETPROFIT")),  # 归母净利润
                    "deductedNetProfit": to_float(row.get("DEDUCTED_PARENT_NETPROFIT")),  # 扣非归母净利润
                    "eps": to_float(row.get("BASIC_EPS")),  # 基本每股收益
                    "dilutedEps": to_float(row.get("DILUTED_EPS")),  # 稀释每股收益
                    "bps": to_float(row.get("BPS")),  # 每股净资产
                    "roe": to_float(row.get("ROE_WEIGHTED")),  # 加权ROE
                    "grossMargin": to_float(row.get("GROSS_PROFIT_RATIO")),  # 毛利率
                    "netMargin": to_float(row.get("NET_PROFIT_RATIO")),  # 净利率
                    "operateIncomeGrowth": to_float(row.get("OPERATE_INCOME_YOY")),  # 营收同比
                    "netProfitGrowth": to_float(row.get("NET_PROFIT_YOY")),  # 净利同比
                    "parentNetProfitGrowth": to_float(row.get("PARENT_NETPROFIT_YOY")),  # 归母净利同比
                    "source": "东财季报",
                })
            return {"items": items, "symbol": symbol, "source": "东财季报"}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "symbol": symbol, "source": "东财季报", "error": str(e)}

    # ==================== 财报三表（东财） ====================
    @staticmethod
    def eastmoney_balance_sheet(symbol: str) -> dict[str, Any]:
        """资产负债表"""
        sym6 = code6(symbol)
        url = (
            f"https://datacenter.eastmoney.com/securities/api/data/v1/get?"
            f"reportName=RPT_DMSK_FN_BALANCE&columns=ALL&"
            f"filter=(SECURITY_CODE=%22{sym6}%22)&"
            f"pageNumber=1&pageSize=10&sortTypes=-1&sortColumns=REPORT_DATE&"
            f"source=HSF10&client=PC"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"items": [], "error": "circuit_open", "source": "东财资产负债表"}
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
                    "reportDate": row.get("REPORT_DATE", ""),
                    "totalAssets": to_float(row.get("TOTAL_ASSETS")),  # 总资产
                    "totalLiabilities": to_float(row.get("TOTAL_LIABILITIES")),  # 总负债
                    "totalEquity": to_float(row.get("TOTAL_EQUITY")),  # 所有者权益
                    "currentAssets": to_float(row.get("TOTAL_CURRENT_ASSETS")),  # 流动资产
                    "currentLiabilities": to_float(row.get("TOTAL_CURRENT_LIAB")),  # 流动负债
                    "cash": to_float(row.get("MONEY_CAPITAL")),  # 货币资金
                    "receivables": to_float(row.get("ACCOUNTS_RECEI")),  # 应收账款
                    "inventory": to_float(row.get("INVENTORY")),  # 存货
                    "fixedAssets": to_float(row.get("FIXED_ASSETS")),  # 固定资产
                    "intangibleAssets": to_float(row.get("INTANGIBLE_ASSETS")),  # 无形资产
                    "goodwill": to_float(row.get("GOODWILL")),  # 商誉
                    "shortBorrow": to_float(row.get("SHORT_TERM_BORROW")),  # 短期借款
                    "longBorrow": to_float(row.get("LONG_TERM_BORROW")),  # 长期借款
                    "source": "东财资产负债表",
                })
            return {"items": items, "symbol": symbol, "source": "东财资产负债表"}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "symbol": symbol, "source": "东财资产负债表", "error": str(e)}

    @staticmethod
    def eastmoney_cashflow(symbol: str) -> dict[str, Any]:
        """现金流量表"""
        sym6 = code6(symbol)
        url = (
            f"https://datacenter.eastmoney.com/securities/api/data/v1/get?"
            f"reportName=RPT_DMSK_FN_CASHFLOW&columns=ALL&"
            f"filter=(SECURITY_CODE=%22{sym6}%22)&"
            f"pageNumber=1&pageSize=10&sortTypes=-1&sortColumns=REPORT_DATE&"
            f"source=HSF10&client=PC"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"items": [], "error": "circuit_open", "source": "东财现金流量表"}
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
                    "reportDate": row.get("REPORT_DATE", ""),
                    "operateCashFlow": to_float(row.get("OPERATE_CASH_FLOW")),  # 经营活动现金流
                    "investCashFlow": to_float(row.get("INVEST_CASH_FLOW")),  # 投资活动现金流
                    "financeCashFlow": to_float(row.get("FINANCE_CASH_FLOW")),  # 筹资活动现金流
                    "netCashFlow": to_float(row.get("NET_CASH_FLOW")),  # 净现金流
                    "operateCashFlowPs": to_float(row.get("OPERATE_CF_PS")),  # 每股经营现金流
                    "source": "东财现金流量表",
                })
            return {"items": items, "symbol": symbol, "source": "东财现金流量表"}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "symbol": symbol, "source": "东财现金流量表", "error": str(e)}

    # ==================== 新浪财务数据（备用） ====================
    @staticmethod
    def sina_financial(symbol: str) -> dict[str, Any]:
        """新浪财务数据"""
        sym = with_prefix(symbol)
        try:
            session = get_session()
            resp = session.get(
                f"https://finance.sina.com.cn/realstock/company/{sym}/nc.shtml",
                timeout=15,
                headers={"Referer": "https://finance.sina.com.cn/"},
            )
            resp.raise_for_status()
            html = resp.text
            import re
            # 提取关键财务指标
            name = re.findall(r'<title>([^(]+)', html)
            pe = re.findall(r'市盈率[：:]\s*([\d.]+)', html)
            pb = re.findall(r'市净率[：:]\s*([\d.]+)', html)
            roe = re.findall(r'ROE[：:]\s*([\d.]+)', html)
            return {
                "symbol": sym,
                "name": name[0].strip() if name else "",
                "pe": to_float(pe[0] if pe else 0),
                "pb": to_float(pb[0] if pb else 0),
                "roe": to_float(roe[0] if roe else 0),
                "source": "新浪财经",
            }
        except Exception as e:
            return {"symbol": sym, "source": "新浪财经", "error": str(e)}

    # ==================== 公司基本信息（mootdx） ====================
    @staticmethod
    def mootdx_company_info(symbol: str) -> dict[str, Any]:
        """mootdx 公司概况信息"""
        try:
            from mootdx.reader import Reader
            sym6 = code6(symbol)
            market = 1 if sym6.startswith(("5", "6", "9")) else 0
            for ip, port in TDX_SERVERS:
                if not probe_tdx(ip, port):
                    continue
                try:
                    reader = Reader.factory(market="std", server=ip, port=port)
                    result = reader.xdxr(symbol=sym6, market=market)
                    return {
                        "symbol": sym6,
                        "data": result,
                        "source": "mootdx",
                    }
                except Exception:
                    continue
        except Exception:
            pass
        return {"symbol": code6(symbol), "data": {}, "source": "mootdx", "error": "unavailable"}

    # ==================== 综合基础数据 ====================
    @classmethod
    def get_stock_fundamental(cls, symbol: str) -> dict[str, Any]:
        """个股综合基础数据"""
        return {
            "symbol": code6(symbol),
            "quarterly": cls.eastmoney_quarterly_report(symbol),
            "balanceSheet": cls.eastmoney_balance_sheet(symbol),
            "cashflow": cls.eastmoney_cashflow(symbol),
            "f10Summary": cls.mootdx_f10(symbol, "cwzy"),  # 财务摘要
            "companyInfo": cls.mootdx_company_info(symbol),
            "source": "mootdx + 东财 + 新浪",
            "updatedAt": now_text(),
        }


fundamental_source = FundamentalDataSource()