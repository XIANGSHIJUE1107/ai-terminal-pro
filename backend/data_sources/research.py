# -*- coding: utf-8 -*-
"""
研报层 —— 东财 reportapi + 同花顺 + iwencai
个股研报 / 行业研报 / PDF下载 / 一致预期 / NL搜索
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.data_sources.base import (
    to_float, with_prefix, code6, now_text, now_dt, get_session,
)
from backend.data_sources.rate_limiter import rate_limiter


class ResearchDataSource:
    """研报数据源：东财 reportapi > 同花顺 > iwencai"""

    EASTMONEY_REPORT_URL = "https://reportapi.eastmoney.com/report/list"
    EASTMONEY_REPORT_DETAIL = "https://data.eastmoney.com/report/zw"

    # ==================== 东财个股研报 ====================
    @staticmethod
    def eastmoney_stock_report(symbol: str, page: int = 1, pagesize: int = 20) -> dict[str, Any]:
        """东财个股研报列表"""
        url = (
            f"{ResearchDataSource.EASTMONEY_REPORT_URL}?"
            f"cb=datatable&industryCode=*&pageSize={pagesize}&pageNo={page}"
            f"&rating=*&ratingchange=*&reportdatefrom=&reportdateto=&"
            f"beginTime=&endTime=&sortfield=datetime&sorttype=desc&"
            f"stockCode={code6(symbol)}&"
            f"_={int(datetime.now().timestamp() * 1000)}"
        )
        try:
            session = get_session()
            resp = session.get(url, timeout=15, headers={"Referer": "https://data.eastmoney.com/"})
            resp.raise_for_status()
            text = resp.text
            if text.startswith("datatable("):
                import json
                data = json.loads(text[len("datatable("):-1])
                items = []
                for row in (data.get("data") or []):
                    items.append({
                        "id": row.get("infoCode", ""),
                        "title": row.get("title", ""),
                        "orgName": row.get("orgName", ""),  # 机构名称
                        "author": row.get("author", ""),
                        "rating": row.get("rating", ""),  # 评级
                        "ratingChange": row.get("ratingChange", ""),  # 评级变动
                        "reportDate": row.get("reportDate", ""),
                        "stockCode": row.get("stockCode", ""),
                        "stockName": row.get("stockName", ""),
                        "industryCode": row.get("industryCode", ""),
                        "industryName": row.get("industryName", ""),
                        "pdfUrl": row.get("pdfUrl", "") or f"https://pdf.dfcfw.com/pdf/h3_{row.get('infoCode', '')}_1.pdf",
                        "digest": row.get("digest", ""),  # 摘要
                        "source": "东财研报",
                    })
                return {
                    "items": items,
                    "total": data.get("TotalCount", len(items)),
                    "page": page,
                    "source": "东方财富研报中心",
                }
        except Exception as e:
            return {"items": [], "total": 0, "page": page, "source": "东方财富研报中心", "error": str(e)}

    # ==================== 东财行业研报 ====================
    @staticmethod
    def eastmoney_industry_report(industry: str = "", page: int = 1, pagesize: int = 20) -> dict[str, Any]:
        """东财行业研报列表"""
        industry_code = industry or "*"
        url = (
            f"{ResearchDataSource.EASTMONEY_REPORT_URL}?"
            f"cb=datatable&industryCode={industry_code}&pageSize={pagesize}&pageNo={page}"
            f"&rating=*&ratingchange=*&reportdatefrom=&reportdateto=&"
            f"beginTime=&endTime=&sortfield=datetime&sorttype=desc&"
            f"stockCode=*&"
            f"_={int(datetime.now().timestamp() * 1000)}"
        )
        try:
            session = get_session()
            resp = session.get(url, timeout=15, headers={"Referer": "https://data.eastmoney.com/"})
            resp.raise_for_status()
            text = resp.text
            if text.startswith("datatable("):
                import json
                data = json.loads(text[len("datatable("):-1])
                items = []
                for row in (data.get("data") or []):
                    items.append({
                        "id": row.get("infoCode", ""),
                        "title": row.get("title", ""),
                        "orgName": row.get("orgName", ""),
                        "author": row.get("author", ""),
                        "industryName": row.get("industryName", ""),
                        "reportDate": row.get("reportDate", ""),
                        "digest": row.get("digest", ""),
                        "pdfUrl": row.get("pdfUrl", "") or f"https://pdf.dfcfw.com/pdf/h3_{row.get('infoCode', '')}_1.pdf",
                        "source": "东财行业研报",
                    })
                return {
                    "items": items,
                    "total": data.get("TotalCount", len(items)),
                    "page": page,
                    "source": "东方财富行业研报",
                }
        except Exception as e:
            return {"items": [], "total": 0, "page": page, "source": "东方财富行业研报", "error": str(e)}

    # ==================== 同花顺研报（iFind接口） ====================
    @staticmethod
    def tonghuashun_report(symbol: str, page: int = 1) -> dict[str, Any]:
        """同花顺个股研报"""
        sym6 = code6(symbol)
        try:
            session = get_session()
            resp = session.get(
                f"https://basic.10jqka.com.cn/{sym6}/research.html",
                timeout=15,
                headers={"Referer": "https://www.10jqka.com.cn/"},
            )
            resp.raise_for_status()
            html = resp.text
            # 简单解析研报标题
            import re
            titles = re.findall(r'<a[^>]*?href="[^"]*?report[^"]*?"[^>]*?title="([^"]*)"[^>]*?>', html)
            orgs = re.findall(r'<span[^>]*?class="[^"]*?org[^"]*?"[^>]*?>([^<]*)</span>', html)
            dates = re.findall(r'<span[^>]*?class="[^"]*?date[^"]*?"[^>]*?>([^<]*)</span>', html)
            items = []
            for i, title in enumerate(titles[:20]):
                items.append({
                    "title": title.strip(),
                    "orgName": orgs[i].strip() if i < len(orgs) else "",
                    "reportDate": dates[i].strip() if i < len(dates) else "",
                    "source": "同花顺研报",
                })
            return {"items": items, "total": len(items), "source": "同花顺"}
        except Exception as e:
            return {"items": [], "total": 0, "source": "同花顺", "error": str(e)}

    # ==================== iwencai NL搜索研报 ====================
    @staticmethod
    def iwencai_search(query: str, limit: int = 20) -> dict[str, Any]:
        """iWenCai 自然语言搜索研报/股票"""
        try:
            import akshare as ak
            df = ak.stock_individual_info_em(symbol=query) if query.isdigit() else None
            if df is not None and not df.empty:
                info = {}
                for _, row in df.iterrows():
                    info[str(row["item"])] = str(row["value"])
                return {"items": [info], "source": "iWenCai/东财", "query": query}
            return {"items": [], "source": "iWenCai", "query": query, "error": "未匹配到个股"}
        except Exception as e:
            return {"items": [], "source": "iWenCai", "query": query, "error": str(e)}

    # ==================== 东财一致预期 ====================
    @staticmethod
    def eastmoney_consensus(symbol: str) -> dict[str, Any]:
        """东财一致预期（分析师预测）"""
        sym6 = code6(symbol)
        url = (
            f"https://datacenter.eastmoney.com/securities/api/data/v1/get?"
            f"reportName=RPT_F10_FINANCE_MAINSTATISTICS&columns=ALL&"
            f"filter=(SECURITY_CODE=%22{sym6}%22)&pageNumber=1&pageSize=4&"
            f"sortColumns=REPORT_DATE&sortTypes=-1&source=HSF10&client=PC"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"error": "circuit_open", "source": "东财一致预期"}
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
                    "netProfit": to_float(row.get("PARENT_NETPROFIT")),  # 归母净利润
                    "revenue": to_float(row.get("TOTAL_OPERATE_INCOME")),  # 营业收入
                    "eps": to_float(row.get("BASIC_EPS")),  # 基本每股收益
                    "bps": to_float(row.get("BPS")),  # 每股净资产
                    "roe": to_float(row.get("ROE_WEIGHTED")),  # 加权ROE
                    "source": "东财一致预期",
                })
            return {"items": items, "source": "东财一致预期"}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "source": "东财一致预期", "error": str(e)}

    # ==================== 综合研报查询 ====================
    @classmethod
    def get_stock_reports(cls, symbol: str, page: int = 1) -> dict[str, Any]:
        """个股研报综合查询：东财 > 同花顺"""
        result = cls.eastmoney_stock_report(symbol, page)
        if not result.get("items"):
            result = cls.tonghuashun_report(symbol, page)
        return result

    @classmethod
    def get_industry_reports(cls, industry: str = "", page: int = 1) -> dict[str, Any]:
        """行业研报"""
        return cls.eastmoney_industry_report(industry, page)


research_source = ResearchDataSource()