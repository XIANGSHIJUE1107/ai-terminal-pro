# -*- coding: utf-8 -*-
"""
新闻数据源聚合

真实来源:
- 新浪财经
- 东方财富个股新闻
- 东方财富全球快讯
- 财联社电报
- 财新新闻
- 金十数据页面快讯

输出为统一 DTO，供 DataHub 和前端直接消费。
"""

from __future__ import annotations

import json
import re
import queue
import threading
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

import pandas as pd
import requests

from backend.data_sources.base import code6, now_dt, now_text
from backend.data_sources.rate_limiter import rate_limiter

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
SINA_HEADERS = {**HEADERS, "Referer": "https://finance.sina.com.cn/"}
EM_HEADERS = {**HEADERS, "Referer": "https://so.eastmoney.com/"}
CLS_HEADERS = {**HEADERS, "Referer": "https://www.cls.cn/telegraph"}
CX_HEADERS = {**HEADERS, "Referer": "https://cxdata.caixin.com/index/newsTab?tab=latest"}
JIN10_HEADERS = {**HEADERS, "Referer": "https://www.jin10.com/"}

NEWS_KEYWORDS = [
    "AI", "算力", "芯片", "半导体", "机器人", "新能源", "光模块", "CPO", "6G",
    "低空", "航天", "军工", "通信", "汽车", "医药", "消费电子", "锂电", "光伏",
    "黄金", "原油", "美元", "人民币", "利率", "降息", "加息", "GDP", "CPI",
    "PPI", "PMI", "财政", "货币", "贸易", "出口", "进口", "关税", "地缘",
    "上证", "深证", "创业板", "沪深300", "科创50",
]
POSITIVE_WORDS = [
    "利好", "上涨", "涨停", "突破", "增长", "盈利", "回升", "扩张", "创新高", "中标",
    "获批", "签约", "合作", "投产", "落地", "改善", "提振", "增持", "回购", "放量",
]
NEGATIVE_WORDS = [
    "利空", "下跌", "跌停", "回落", "下降", "亏损", "承压", "减持", "调查", "处罚",
    "停牌", "爆雷", "裁员", "违约", "暴跌", "风险", "警告", "不及预期", "冲突", "撤回",
]
IMPORTANT_WORDS = [
    "涨停", "跌停", "新高", "重大", "签约", "合作", "公告", "业绩", "财报", "减持",
    "回购", "分红", "融资", "政策", "央行", "美联储", "降息", "加息", "通胀", "地缘",
    "停牌", "复牌", "中标", "投产", "落地", "扩产", "开工", "并购", "重组",
]
SOURCE_WEIGHT = {
    "新浪财经": 1.05,
    "东方财富": 1.0,
    "财联社": 1.15,
    "财新": 0.95,
    "金十数据": 1.08,
}

_session: requests.Session | None = None
_cache: dict[str, dict[str, Any]] = {}
_news_cache: dict[str, dict[str, Any]] = {}


def _session_obj() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.trust_env = False
        _session.headers.update(HEADERS)
    return _session


def _fetch_json(url: str, *, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None, timeout: int = 15) -> Any:
    sess = _session_obj()
    resp = sess.get(url, headers=headers or HEADERS, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _fetch_text(url: str, *, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None, timeout: int = 15) -> str:
    sess = _session_obj()
    resp = sess.get(url, headers=headers or HEADERS, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_dt(value: Any) -> tuple[int | None, str]:
    if value is None:
        return None, ""
    if isinstance(value, (int, float)):
        ts = int(value)
        if ts > 10_000_000_000:
            ts //= 1000
        try:
            dt = datetime.fromtimestamp(ts)
            return ts, dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None, ""
    text = _safe_str(value)
    if not text:
        return None, ""
    text = text.replace("/", "-")
    try:
        dt = datetime.fromisoformat(text[:19])
        return int(dt.timestamp()), dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    try:
        dt = datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
        return int(dt.replace(tzinfo=timezone.utc).timestamp()), dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None, text


def _sentiment(text: str) -> str:
    t = text or ""
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def _tags(text: str) -> list[str]:
    t = text or ""
    tags: list[str] = []
    for kw in NEWS_KEYWORDS:
        if kw in t and kw not in tags:
            tags.append(kw)
    return tags[:6]


def _category(text: str) -> str:
    t = text or ""
    mapping = [
        ("macro", ["利率", "降息", "加息", "通胀", "CPI", "PPI", "PMI", "GDP", "央行", "财政", "货币", "贸易", "关税", "美元", "人民币", "原油", "黄金"]),
        ("global", ["美国", "欧洲", "日本", "韩国", "印度", "俄罗斯", "以色列", "中东", "国际", "海外", "全球"]),
        ("tech", ["AI", "算力", "芯片", "半导体", "机器人", "光模块", "CPO", "6G", "低空", "航天", "军工", "汽车", "消费电子", "新能源", "光伏", "锂电", "医药"]),
        ("finance", ["融资", "回购", "分红", "减持", "增持", "财报", "业绩", "估值", "市值", "银行", "券商", "基金", "保险", "上市"]),
    ]
    for cat, kws in mapping:
        if any(k in t for k in kws):
            return cat
    return "important"


def _importance(text: str, source: str = "") -> float:
    t = text or ""
    score = 10.0
    if any(w in t for w in IMPORTANT_WORDS):
        score += 10
    if any(w in t for w in ["涨停", "跌停", "新高", "突破", "暴涨", "暴跌"]):
        score += 10
    if any(w in t for w in ["公告", "业绩", "中标", "签约", "合作", "并购", "重组", "投产", "落地"]):
        score += 8
    if any(w in t for w in ["央行", "美联储", "利率", "降息", "加息", "CPI", "PPI", "PMI", "GDP"]):
        score += 12
    if any(w in t for w in ["美国", "欧洲", "日本", "韩国", "中东", "地缘", "冲突"]):
        score += 6
    if source in SOURCE_WEIGHT:
        score *= SOURCE_WEIGHT[source]
    return round(min(score, 100.0), 2)


def _freshness_score(ts: int | None) -> float:
    if not ts:
        return 0.0
    age_min = max((datetime.now().timestamp() - ts) / 60.0, 0.0)
    if age_min <= 5:
        return 100.0
    if age_min <= 30:
        return round(95 - age_min, 2)
    if age_min <= 180:
        return round(85 - age_min / 4, 2)
    if age_min <= 720:
        return round(55 - age_min / 24, 2)
    return 10.0


def _normalize_item(
    *,
    title: str,
    summary: str = "",
    url: str = "",
    source: str = "",
    published_at: Any = None,
    raw: dict[str, Any] | None = None,
    source_category: str | None = None,
) -> dict[str, Any]:
    raw = raw or {}
    ts, time_str = _parse_dt(published_at)
    text = f"{title} {summary} {source}"
    item = {
        "id": _safe_str(raw.get("id") or raw.get("docid") or raw.get("code") or f"{source}:{title}:{url}"),
        "title": _safe_str(title),
        "summary": _safe_str(summary) or _safe_str(title),
        "url": _safe_str(url),
        "source": _safe_str(source) or "未知",
        "time": ts or int(datetime.now().timestamp()),
        "timeStr": time_str or now_text(),
        "sentiment": _sentiment(text),
        "tags": _tags(text),
        "category": source_category or _category(text),
        "importance": _importance(text, source),
        "freshness": "realtime" if (ts and (datetime.now().timestamp() - ts) < 1800) else "stale",
        "stale": False if (ts and (datetime.now().timestamp() - ts) < 7200) else True,
        "errors": [],
    }
    if raw.get("impactedSector"):
        item["impactedSector"] = raw.get("impactedSector")
    if raw.get("impactedEtf"):
        item["impactedEtf"] = raw.get("impactedEtf")
    if raw.get("market"):
        item["market"] = raw.get("market")
    item["freshnessScore"] = _freshness_score(ts)
    return item


def _dedup(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        title_key = re.sub(r"\s+", "", _safe_str(item.get("title"))).lower()
        url_key = _safe_str(item.get("url")).lower()
        key = (title_key, url_key)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _rank(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def _score(item: dict[str, Any]) -> tuple[float, int]:
        freshness = float(item.get("freshnessScore", 0) or 0)
        importance = float(item.get("importance", 0) or 0)
        ts = int(item.get("time") or 0)
        return (importance * 1.8 + freshness * 0.35, ts)

    return sorted(items, key=_score, reverse=True)


def _df_to_items(df: pd.DataFrame, *, source: str, title_col: str, summary_col: str, time_col: str, url_col: str | None = None, limit: int = 100, category: str | None = None) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    items: list[dict[str, Any]] = []
    for _, row in df.head(limit).iterrows():
        title = _safe_str(row.get(title_col))
        if not title:
            continue
        summary = _safe_str(row.get(summary_col, "")) or title
        published = row.get(time_col, "")
        url = _safe_str(row.get(url_col, "")) if url_col else ""
        items.append(
            _normalize_item(
                title=title,
                summary=summary,
                url=url,
                source=source,
                published_at=published,
                raw=row.to_dict(),
                source_category=category,
            )
        )
    return items


class NewsDataSource:
    """统一新闻聚合器。"""

    def sina_news(self, limit: int = 40) -> dict[str, Any]:
        lids = [
            (2510, "财经"),
            (2513, "证券"),
            (2515, "股票"),
            (2518, "滚动"),
            (2511, "国际"),
            (2514, "全球"),
            (2509, "国内"),
            (2516, "行业"),
        ]
        items: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for lid, _name in lids:
            try:
                url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid={lid}&k=&num={min(limit, 20)}&page=1"
                data = _fetch_json(url, headers=SINA_HEADERS, timeout=15)
                rows = (((data or {}).get("result") or {}).get("data") or [])
                for row in rows:
                    title = _safe_str(row.get("title"))
                    if not title:
                        continue
                    summary = _safe_str(row.get("intro") or row.get("summary") or row.get("wapsummary") or title)
                    items.append(
                        _normalize_item(
                            title=title,
                            summary=summary,
                            url=_safe_str(row.get("url")),
                            source="新浪财经",
                            published_at=row.get("ctime"),
                            raw=row,
                        )
                    )
            except Exception as e:
                errors.append({"source": f"新浪财经(lid={lid})", "message": str(e)})
        items = _rank(_dedup(items))[:limit]
        return self._pack("新浪财经", items, errors)

    def eastmoney_stock_news(self, symbol: str, page: int = 1, pagesize: int = 20) -> dict[str, Any]:
        sym = code6(symbol)
        try:
            import akshare as ak

            df = ak.stock_news_em(symbol=sym)
            items = _df_to_items(
                df,
                source="东方财富",
                title_col="新闻标题",
                summary_col="新闻内容",
                time_col="发布时间",
                url_col="新闻链接",
                limit=pagesize,
            )
            items = _rank(_dedup(items))[:pagesize]
            return self._pack("东方财富个股新闻", items, [])
        except Exception as e:
            return self._pack("东方财富个股新闻", [], [{"source": "东方财富个股新闻", "message": str(e)}], unavailable=True)

    def eastmoney_global_news(self, page: int = 1, pagesize: int = 30) -> dict[str, Any]:
        try:
            import akshare as ak

            df = ak.stock_info_global_em()
            items = _df_to_items(
                df,
                source="东方财富",
                title_col="标题",
                summary_col="摘要",
                time_col="发布时间",
                url_col="链接",
                limit=pagesize,
                category="global",
            )
            if not items:
                df2 = ak.stock_info_global_cls("全部")
                items = _df_to_items(
                    df2,
                    source="财联社",
                    title_col="标题",
                    summary_col="内容",
                    time_col="发布时间",
                    url_col=None,
                    limit=pagesize,
                    category="global",
                )
            items = _rank(_dedup(items))[:pagesize]
            return self._pack("东方财富全球快讯", items, [])
        except Exception as e:
            return self._pack("东方财富全球快讯", [], [{"source": "东方财富全球快讯", "message": str(e)}], unavailable=True)

    def cailianshe_news(self, limit: int = 30) -> dict[str, Any]:
        try:
            import akshare as ak

            df = ak.stock_info_global_cls("全部")
            items = _df_to_items(
                df,
                source="财联社",
                title_col="标题",
                summary_col="内容",
                time_col="发布时间",
                url_col=None,
                limit=limit,
                category="important",
            )
            if not items:
                items = self._cailian_from_local_cache(limit)
            items = _rank(_dedup(items))[:limit]
            return self._pack("财联社", items, [])
        except Exception as e:
            cached = self._cailian_from_local_cache(limit)
            if cached:
                return self._pack("财联社", cached, [{"source": "财联社", "message": str(e)}], stale=True)
            return self._pack("财联社", [], [{"source": "财联社", "message": str(e)}], unavailable=True)

    def caixin_news(self, limit: int = 30) -> dict[str, Any]:
        try:
            import akshare as ak

            df = ak.stock_news_main_cx()
            if df is None or df.empty:
                return self._pack("财新", [], [])
            items: list[dict[str, Any]] = []
            for _, row in df.head(limit).iterrows():
                title = _safe_str(row.get("summary") or row.get("title") or row.get("tag"))
                if not title:
                    continue
                items.append(
                    _normalize_item(
                        title=title,
                        summary=_safe_str(row.get("summary") or title),
                        url=_safe_str(row.get("url")),
                        source="财新",
                        published_at=row.get("time") or row.get("发布时间") or now_text(),
                        raw=row.to_dict(),
                        source_category="global",
                    )
                )
            items = _rank(_dedup(items))[:limit]
            return self._pack("财新", items, [])
        except Exception as e:
            return self._pack("财新", [], [{"source": "财新", "message": str(e)}], unavailable=True)

    def baidu_macro_news(self, limit: int = 30) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        try:
            import akshare as ak

            today = datetime.now().strftime("%Y%m%d")
            for fetcher, label, kwargs in [
                (ak.news_economic_baidu, "宏观日历", {"date": today}),
                (ak.news_report_time_baidu, "财报日历", {"date": today}),
                (ak.news_trade_notify_dividend_baidu, "分红送转", {"date": today}),
                (ak.news_trade_notify_suspend_baidu, "停复牌", {"date": today}),
            ]:
                try:
                    df = fetcher(**kwargs)
                    if df is None or df.empty:
                        continue
                    if "事件" in df.columns:
                        for _, row in df.head(limit).iterrows():
                            title = _safe_str(row.get("事件"))
                            if not title:
                                continue
                            summary = " | ".join(
                                _safe_str(x)
                                for x in [row.get("地区"), row.get("公布"), row.get("预期"), row.get("前值")]
                                if _safe_str(x)
                            )
                            items.append(
                                _normalize_item(
                                    title=title,
                                    summary=summary or title,
                                    url="https://www.jin10.com/",
                                    source="百度宏观",
                                    published_at=f"{row.get('日期', '')} {row.get('时间', '')}",
                                    raw=row.to_dict(),
                                    source_category="macro",
                                )
                            )
                    else:
                        for _, row in df.head(limit).iterrows():
                            title = _safe_str(row.get("股票简称") or row.get("股票代码") or row.get("标题") or row.get("名称"))
                            if not title:
                                continue
                            summary = " | ".join(
                                _safe_str(x)
                                for x in [row.get("财报类型"), row.get("发布时间"), row.get("发布日期"), row.get("市值")]
                                if _safe_str(x)
                            )
                            items.append(
                                _normalize_item(
                                    title=title,
                                    summary=summary or title,
                                    url="https://www.jin10.com/",
                                    source=f"百度{label}",
                                    published_at=row.get("发布日期") or row.get("发布时间") or now_text(),
                                    raw=row.to_dict(),
                                    source_category="finance",
                                )
                            )
                except Exception as inner:
                    errors.append({"source": f"百度{label}", "message": str(inner)})
        except Exception as e:
            errors.append({"source": "百度新闻", "message": str(e)})
        items = _rank(_dedup(items))[:limit]
        return self._pack("百度新闻", items, errors)

    def jin10_news(self, limit: int = 30) -> dict[str, Any]:
        cache_key = "jin10"
        if cache_key in _cache and (datetime.now().timestamp() - _cache[cache_key]["ts"] < 120):
            return _cache[cache_key]["payload"]
        try:
            html = _fetch_text("https://www.jin10.com/", headers=JIN10_HEADERS, timeout=20)
            items = self._parse_jin10(html, limit)
            payload = self._pack("金十数据", items, [])
            _cache[cache_key] = {"ts": datetime.now().timestamp(), "payload": payload}
            return payload
        except Exception as e:
            cached = _cache.get(cache_key, {}).get("payload")
            if cached:
                cached = dict(cached)
                cached["freshness"] = "stale-cache"
                cached["stale"] = True
                cached["errors"] = cached.get("errors", []) + [{"source": "金十数据", "message": str(e)}]
                return cached
            return self._pack("金十数据", [], [{"source": "金十数据", "message": str(e)}], unavailable=True)

    def tonghuashun_news(self, limit: int = 30) -> dict[str, Any]:
        try:
            url = "https://news.10jqka.com.cn/tapp/news/push/stock/"
            data = _fetch_json(url, headers={**HEADERS, "Referer": "https://www.10jqka.com.cn/"}, params={"page": 1, "tag": "", "track": "website"}, timeout=15)
            rows = ((data.get("data") or {}).get("list") or data.get("list") or [])
            items = []
            for row in rows[:limit]:
                title = _safe_str(row.get("title"))
                if not title:
                    continue
                summary = _safe_str(row.get("digest") or row.get("summary") or title)
                items.append(
                    _normalize_item(
                        title=title,
                        summary=summary,
                        url=_safe_str(row.get("url") or row.get("shareUrl")),
                        source="同花顺",
                        published_at=row.get("ctime") or row.get("rtime") or row.get("time"),
                        raw=row,
                    )
                )
            items = _rank(_dedup(items))[:limit]
            return self._pack("同花顺", items, [])
        except Exception as e:
            return self._pack("同花顺", [], [{"source": "同花顺", "message": str(e)}], unavailable=True)

    def get_news(self, symbol: str = "", limit: int = 40) -> dict[str, Any]:
        cache_key = f"{symbol or 'ALL'}:{limit}"
        cached = _news_cache.get(cache_key)
        if cached and (datetime.now().timestamp() - cached.get("ts", 0) < 90):
            return cached["payload"]

        items: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        sources: list[str] = []

        tasks: list[tuple[str, Any, tuple, dict[str, Any]]] = []
        if symbol:
            tasks.append(("stock", self.eastmoney_stock_news, (symbol,), {"page": 1, "pagesize": max(limit, 20)}))
        tasks.extend([
            ("global", self.eastmoney_global_news, tuple(), {"page": 1, "pagesize": max(limit, 20)}),
            ("sina", self.sina_news, tuple(), {"limit": max(limit, 20)}),
            ("cls", self.cailianshe_news, tuple(), {"limit": max(limit, 20)}),
            ("caixin", self.caixin_news, tuple(), {"limit": max(limit, 20)}),
            ("macro", self.baidu_macro_news, tuple(), {"limit": max(limit, 20)}),
            ("jin10", self.jin10_news, tuple(), {"limit": max(limit, 20)}),
            ("ths", self.tonghuashun_news, tuple(), {"limit": max(limit, 20)}),
        ])

        timeout_seconds = 10 if not symbol else 8
        result_queue: queue.Queue[tuple[str, dict[str, Any] | None, str | None]] = queue.Queue()

        def _worker(label: str, fn, args, kwargs):
            try:
                result_queue.put((label, fn(*args, **kwargs), None))
            except Exception as e:
                result_queue.put((label, None, str(e)))

        for label, fn, args, kwargs in tasks:
            threading.Thread(
                target=_worker,
                args=(label, fn, args, kwargs),
                daemon=True,
            ).start()

        deadline = datetime.now().timestamp() + timeout_seconds
        completed = 0
        while completed < len(tasks):
            remaining = deadline - datetime.now().timestamp()
            if remaining <= 0:
                break
            try:
                label, result, err = result_queue.get(timeout=remaining)
            except queue.Empty:
                break
            completed += 1
            if err:
                errors.append({"source": label, "message": err})
                continue
            if not result:
                continue
            items.extend(result.get("items", []))
            errors.extend(result.get("errors", []))
            sources.extend(result.get("sources", []))
            items = _rank(_dedup(items))[:limit]

        items = _rank(_dedup(items))[:limit]
        payload = self._pack(
            "新闻聚合",
            items,
            errors,
            sources=sources,
            extra={
                "symbol": symbol,
                "limit": limit,
                "important": [item for item in items if float(item.get("importance", 0) or 0) >= 25][:10],
                "categories": self._category_summary(items),
            },
            stale=not bool(items),
            unavailable=not bool(items),
        )
        _news_cache[cache_key] = {"ts": datetime.now().timestamp(), "payload": payload}
        return payload

    def get_stock_news(self, symbol: str, limit: int = 30) -> dict[str, Any]:
        return self.eastmoney_stock_news(symbol, pagesize=limit)

    def get_global_news(self, limit: int = 30) -> dict[str, Any]:
        return self.eastmoney_global_news(page=1, pagesize=limit)

    def _pack(
        self,
        source: str,
        items: list[dict[str, Any]],
        errors: list[dict[str, Any]],
        *,
        sources: list[str] | None = None,
        extra: dict[str, Any] | None = None,
        stale: bool | None = None,
        unavailable: bool | None = None,
    ) -> dict[str, Any]:
        items = _rank(_dedup(items))
        timestamps = [int(item.get("time") or 0) for item in items if item.get("time")]
        updated_at = now_text()
        if timestamps:
            try:
                updated_at = datetime.fromtimestamp(max(timestamps)).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        payload = {
            "source": source if not sources else " + ".join(dict.fromkeys(sources)) if sources else source,
            "updatedAt": updated_at,
            "asOf": now_text(),
            "freshness": "realtime" if items else "unavailable",
            "stale": bool(stale if stale is not None else not items),
            "unavailable": bool(unavailable if unavailable is not None else not items),
            "errors": errors,
            "data": {
                "items": items,
                "important": [item for item in items if float(item.get("importance", 0) or 0) >= 25][:10],
                "categories": self._category_summary(items),
            },
            "items": items,
            "sources": list(dict.fromkeys([source] + (sources or []))),
        }
        if extra:
            payload["data"].update(extra)
        payload["items"] = payload["data"]["items"]
        payload["news"] = payload["items"]
        payload["count"] = len(payload["items"])
        payload["total"] = len(payload["items"])
        payload["data"]["news"] = payload["items"]
        payload["data"]["count"] = payload["count"]
        return payload

    def _category_summary(self, items: list[dict[str, Any]]) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for item in items:
            counter[str(item.get("category") or "important")] += 1
        return dict(counter)

    def _parse_jin10(self, html: str, limit: int) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        patterns = [
            r'window\.__NUXT__\s*=\s*(\{.*?\})\s*;</script>',
            r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;</script>',
        ]
        for pat in patterns:
            m = re.search(pat, html, re.S)
            if not m:
                continue
            blob = m.group(1)
            try:
                data = json.loads(blob)
            except Exception:
                continue
            items.extend(self._extract_jin10_from_obj(data))
            if items:
                break
        if not items:
            # 兜底：从脚本或页面文本提取带时间的快讯片段
            for title, summary, ts in self._extract_jin10_from_html(html):
                items.append(
                    _normalize_item(
                        title=title,
                        summary=summary,
                        url="https://www.jin10.com/",
                        source="金十数据",
                        published_at=ts,
                        raw={"title": title, "summary": summary, "ts": ts},
                        source_category="macro",
                    )
                )
        return _rank(_dedup(items))[:limit]

    def _extract_jin10_from_obj(self, obj: Any) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        stack = [obj]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                if any(k in cur for k in ("title", "content", "summary", "time")):
                    title = _safe_str(cur.get("title") or cur.get("name"))
                    summary = _safe_str(cur.get("content") or cur.get("summary") or cur.get("desc") or title)
                    if title:
                        out.append(
                            _normalize_item(
                                title=title,
                                summary=summary,
                                url=_safe_str(cur.get("url") or cur.get("link") or "https://www.jin10.com/"),
                                source="金十数据",
                                published_at=cur.get("time") or cur.get("ts") or cur.get("created_at") or cur.get("createdAt"),
                                raw=cur,
                                source_category="macro",
                            )
                        )
                stack.extend(cur.values())
            elif isinstance(cur, list):
                stack.extend(cur)
        return out

    def _extract_jin10_from_html(self, html: str) -> list[tuple[str, str, Any]]:
        out: list[tuple[str, str, Any]] = []
        text = re.sub(r"<script.*?>.*?</script>", " ", html, flags=re.S)
        text = re.sub(r"<style.*?>.*?</style>", " ", text, flags=re.S)
        text = re.sub(r"\s+", " ", text)
        for match in re.finditer(r"(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<title>[^。！？]{6,120}?)(?:。|！|？)", text):
            title = match.group("title").strip()
            if "金十" in title or len(title) < 6:
                continue
            out.append((title, title, match.group("time")))
            if len(out) >= 30:
                break
        return out

    def _cailian_from_local_cache(self, limit: int) -> list[dict[str, Any]]:
        cache_path = Path(__file__).resolve().parents[2] / "news_cache.json"
        if not cache_path.exists():
            return []
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            items = (((data.get("payload") or {}).get("items")) or [])
            out: list[dict[str, Any]] = []
            for row in items[:limit]:
                title = _safe_str(row.get("title"))
                if not title:
                    continue
                out.append(
                    _normalize_item(
                        title=title,
                        summary=_safe_str(row.get("summary") or row.get("intro") or title),
                        url=_safe_str(row.get("url")),
                        source="财联社",
                        published_at=row.get("time") or row.get("timeStr") or row.get("ctime"),
                        raw=row,
                    )
                )
            return out
        except Exception:
            return []


news_source = NewsDataSource()
