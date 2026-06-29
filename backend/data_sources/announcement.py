# -*- coding: utf-8 -*-
"""
公告层 —— 巨潮 cninfo + mootdx
沪深北全量公告
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from backend.data_sources.base import (
    to_float, with_prefix, code6, now_text, now_dt, get_session,
    TDX_SERVERS, probe_tdx,
)
from backend.data_sources.rate_limiter import rate_limiter


class AnnouncementDataSource:
    """公告数据源：巨潮 cninfo > mootdx"""

    # ==================== 巨潮 cninfo 公告 ====================
    CNINFO_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
    CNINFO_DETAIL = "https://www.cninfo.com.cn/new/announcement/bulletinDetail"

    @staticmethod
    def cninfo_announcements(
        symbol: str = "",
        start_date: str = "",
        end_date: str = "",
        page: int = 1,
        pagesize: int = 30,
    ) -> dict[str, Any]:
        """巨潮公告查询（沪深北全量）"""
        if not start_date:
            start_date = (now_dt() - timedelta(days=7)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = now_dt().strftime("%Y-%m-%d")

        stock_str = f"{code6(symbol)},ORGID" if symbol else ""
        data = {
            "pageNum": page,
            "pageSize": pagesize,
            "column": "szse",
            "tabName": "fulltext",
            "plate": "",
            "stock": stock_str,
            "searchkey": "",
            "secid": "",
            "category": "",
            "trade": "",
            "seDate": f"{start_date}~{end_date}",
            "sortName": "declaredate",
            "sortType": "desc",
        }
        try:
            session = get_session()
            resp = session.post(
                AnnouncementDataSource.CNINFO_URL,
                data=data,
                timeout=20,
                headers={
                    "Referer": "https://www.cninfo.com.cn/",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                },
            )
            resp.raise_for_status()
            result = resp.json()
            rows = (result.get("announcements") or result.get("data") or [])
            items = []
            for row in rows:
                code = row.get("secCode", row.get("stockCode", ""))
                name = row.get("secName", row.get("stockName", ""))
                title = row.get("announcementTitle", row.get("title", ""))
                ann_id = row.get("announcementId", row.get("id", ""))
                items.append({
                    "id": str(ann_id),
                    "code": code,
                    "name": name,
                    "title": title,
                    "date": row.get("announcementTime", "") or row.get("declaredate", ""),
                    "url": f"https://www.cninfo.com.cn/new/announcement/bulletinDetail?announcementId={ann_id}",
                    "type": row.get("announcementType", ""),
                    "source": "巨潮cninfo",
                })
            total = result.get("totalRecordNum", len(items)) or len(items)
            return {
                "items": items,
                "total": total,
                "page": page,
                "start": start_date,
                "end": end_date,
                "source": "巨潮cninfo",
            }
        except Exception as e:
            return {
                "items": [],
                "total": 0,
                "page": page,
                "start": start_date,
                "end": end_date,
                "source": "巨潮cninfo",
                "error": str(e),
            }

    # ==================== mootdx 公告 ====================
    @staticmethod
    def mootdx_announcements(symbol: str, start: int = 0, limit: int = 30) -> dict[str, Any]:
        """mootdx 公告数据"""
        try:
            from mootdx.reader import Reader
        except Exception:
            return {"items": [], "source": "mootdx公告", "error": "mootdx not installed"}

        sym6 = code6(symbol)
        market = 1 if sym6.startswith(("5", "6", "9")) else 0
        for ip, port in TDX_SERVERS:
            if not probe_tdx(ip, port):
                continue
            try:
                reader = Reader.factory(market="std", server=ip, port=port)
                result = reader.report(symbol=sym6, market=market, start=start, offset=limit)
                if result:
                    items = []
                    for row in (result if isinstance(result, list) else [result]):
                        if isinstance(row, dict):
                            items.append({
                                "title": row.get("title", ""),
                                "date": row.get("date", ""),
                                "url": row.get("url", ""),
                                "type": row.get("type", ""),
                                "source": "mootdx公告",
                            })
                    return {"items": items, "symbol": sym6, "source": "mootdx公告"}
            except Exception:
                continue
        return {"items": [], "symbol": sym6, "source": "mootdx公告", "error": "all servers failed"}

    # ==================== 东财公告（备用） ====================
    @staticmethod
    def eastmoney_announcements(symbol: str, page: int = 1, pagesize: int = 30) -> dict[str, Any]:
        """东财公告（备用）"""
        sym6 = code6(symbol)
        url = (
            f"https://np-anotice-stock.eastmoney.com/api/security/annv2/"
            f"getAnnList?page_size={pagesize}&page_index={page}&"
            f"stock_list={sym6}&ann_type=A&client_source=web&"
            f"_={int(datetime.now().timestamp() * 1000)}"
        )
        try:
            rate_limiter.wait(url)
            if rate_limiter.is_circuit_open(url):
                return {"items": [], "error": "circuit_open", "source": "东财公告"}
            session = get_session()
            resp = session.get(url, timeout=15, headers={"Referer": "https://np-anotice-stock.eastmoney.com/"})
            resp.raise_for_status()
            data = resp.json()
            rate_limiter.record_success(url)
            items = []
            rows = (data.get("data") or {}).get("list") or []
            for row in rows:
                items.append({
                    "id": str(row.get("art_code", "")),
                    "code": row.get("security_code", ""),
                    "name": row.get("security_name", ""),
                    "title": row.get("title", ""),
                    "date": row.get("notice_date", ""),
                    "url": row.get("url", ""),
                    "type": row.get("ann_type", ""),
                    "source": "东财公告",
                })
            total = (data.get("data") or {}).get("total_hits", len(items)) or len(items)
            return {"items": items, "total": total, "page": page, "source": "东财公告"}
        except Exception as e:
            rate_limiter.record_failure(url)
            return {"items": [], "total": 0, "page": page, "source": "东财公告", "error": str(e)}

    # ==================== 综合公告查询 ====================
    @classmethod
    def get_announcements(
        cls, symbol: str = "", page: int = 1, pagesize: int = 30, days: int = 7
    ) -> dict[str, Any]:
        """综合公告：巨潮 > 东财 > mootdx"""
        start = (now_dt() - timedelta(days=days)).strftime("%Y-%m-%d")
        end = now_dt().strftime("%Y-%m-%d")

        # 优先巨潮（沪深北全量）
        result = cls.cninfo_announcements(symbol, start, end, page, pagesize)
        if result.get("items"):
            return result

        # 备用东财
        if symbol:
            result = cls.eastmoney_announcements(symbol, page, pagesize)
            if result.get("items"):
                return result

        # 最后 mootdx
        if symbol:
            result = cls.mootdx_announcements(symbol, (page - 1) * pagesize, pagesize)
            return result

        return {"items": [], "total": 0, "page": page, "source": "无可用公告源", "error": "all sources failed"}

    @classmethod
    def get_stock_announcements(cls, symbol: str, page: int = 1, pagesize: int = 30) -> dict[str, Any]:
        """个股公告"""
        return cls.get_announcements(symbol, page, pagesize)

    @classmethod
    def get_latest_announcements(cls, days: int = 3, pagesize: int = 50) -> dict[str, Any]:
        """最新全市场公告"""
        return cls.get_announcements("", 1, pagesize, days)


announcement_source = AnnouncementDataSource()