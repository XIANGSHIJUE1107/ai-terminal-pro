# -*- coding: utf-8 -*-
"""
A 股全栈数据 · 七层架构 · V3.2.4
DataHub API 路由
"""

from fastapi import APIRouter, Query

from backend.datahub import datahub_service

router = APIRouter()

# ==================== 核心接口 ====================

@router.get("/latest")
async def latest():
    """最新全量快照"""
    return datahub_service.latest()


@router.post("/refresh")
async def refresh(force: bool = False):
    """强制刷新"""
    return datahub_service.refresh(force=force)


@router.get("/snapshots")
async def snapshots(kind: str | None = None):
    """快照历史"""
    items = datahub_service.snapshot_list(kind)
    return {
        "source": "datahub_snapshots",
        "updatedAt": datahub_service.state().get("last_update_time"),
        "freshness": "local-cache",
        "stale": False,
        "unavailable": False,
        "errors": [],
        "data": {"items": items},
        "items": items,
    }


@router.get("/portfolio")
async def portfolio():
    """持仓行情"""
    return datahub_service.portfolio()


@router.get("/quotes")
async def quotes(symbols: str = Query(..., description="Comma separated symbols")):
    """实时行情（含五档盘口+PE/PB/市值）"""
    symbol_list = [item.strip() for item in symbols.split(",") if item.strip()]
    return datahub_service.quotes(symbol_list)


@router.get("/sectors")
async def sectors(refresh: bool = False):
    """行业板块资金流"""
    return datahub_service.sectors(refresh=refresh)


@router.get("/kline")
async def kline(symbol: str, scale: int = 240, length: int = 120):
    """K线数据（含MA5/10/20/60 + MACD/RSI/BOLL）"""
    return datahub_service.kline(symbol, scale, length)


@router.get("/sector-history")
async def sector_history(name: str, days: int = 30):
    """板块历史资金流"""
    return datahub_service.sector_history(name, days)


# ==================== 行情层（market） ====================

@router.get("/market/quote")
async def market_quote(symbol: str):
    """个股行情（mootdx五档盘口 > 腾讯PE/PB/市值）"""
    from backend.data_sources.market import market_source
    return market_source.get_quote(symbol)


@router.get("/market/level2")
async def market_level2(symbol: str):
    """五档盘口（mootdx）"""
    from backend.data_sources.market import market_source
    return market_source.mootdx_level2(symbol)


@router.get("/market/index")
async def market_index(code: str):
    """指数行情"""
    from backend.data_sources.market import market_source
    return market_source.get_index_quote(code)


@router.get("/market/etf")
async def market_etf(symbol: str):
    """ETF行情"""
    from backend.data_sources.market import market_source
    return market_source.get_etf_quote(symbol)


# ==================== 研报层（research） ====================

@router.get("/research/reports")
async def research_reports(symbol: str, page: int = 1):
    """个股研报（东财 > 同花顺）"""
    return datahub_service.research_reports(symbol, page)


@router.get("/research/industry")
async def research_industry(industry: str = "", page: int = 1):
    """行业研报"""
    return datahub_service.research_industry_reports(industry, page)


@router.get("/research/consensus")
async def research_consensus(symbol: str):
    """一致预期"""
    return datahub_service.research_consensus(symbol)


@router.get("/research/iwencai")
async def research_iwencai(query: str):
    """iWenCai自然语言搜索"""
    return datahub_service.research_iwencai(query)


# ==================== 信号层（signal） ====================

@router.get("/signal/strong")
async def signal_strong(sort: str = "change_pct", limit: int = 50):
    """强势股排行"""
    return datahub_service.signal_strong_stocks(sort, limit)


@router.get("/signal/attribution")
async def signal_attribution(symbol: str):
    """题材归因 + 板块归属"""
    return datahub_service.signal_stock_attribution(symbol)


@router.get("/signal/northbound")
async def signal_northbound(days: int = 20):
    """北向资金"""
    return datahub_service.signal_north_bound(days)


@router.get("/signal/dragontiger")
async def signal_dragontiger(date: str = "", top: int = 50):
    """龙虎榜"""
    return datahub_service.signal_dragon_tiger(date, top)


@router.get("/signal/lockup")
async def signal_lockup(days: int = 30):
    """限售解禁"""
    return datahub_service.signal_lockup_expiry(days)


@router.get("/signal/sector-compare")
async def signal_sector_compare(sector_name: str, top: int = 20):
    """行业板块内个股对比"""
    return datahub_service.signal_sector_compare(sector_name, top)


@router.get("/signal/stock/{symbol}")
async def signal_stock(symbol: str):
    """个股综合信号"""
    return datahub_service.signal_stock_full(symbol)


# ==================== 资金面（fundflow） ====================

@router.get("/fundflow/margin")
async def fundflow_margin(symbol: str, days: int = 60):
    """融资融券"""
    return datahub_service.fundflow_margin(symbol, days)


@router.get("/fundflow/blocktrade")
async def fundflow_blocktrade(symbol: str = "", days: int = 30):
    """大宗交易"""
    return datahub_service.fundflow_block_trade(symbol, days)


@router.get("/fundflow/shareholder")
async def fundflow_shareholder(symbol: str):
    """股东户数"""
    return datahub_service.fundflow_shareholder(symbol)


@router.get("/fundflow/dividend")
async def fundflow_dividend(symbol: str):
    """分红送转"""
    return datahub_service.fundflow_dividend(symbol)


@router.get("/fundflow/stock")
async def fundflow_stock(symbol: str, days: int = 120):
    """个股资金流（120日）"""
    return datahub_service.fundflow_stock_fundflow(symbol, days)


@router.get("/fundflow/stock/minute")
async def fundflow_stock_minute(symbol: str):
    """个股资金流（分钟级）"""
    return datahub_service.fundflow_stock_minute(symbol)


@router.get("/fundflow/stock/{symbol}")
async def fundflow_stock_full(symbol: str):
    """个股资金面全量数据"""
    return datahub_service.fundflow_stock_full(symbol)


# ==================== 新闻层（news） ====================

@router.get("/news")
async def news():
    """综合新闻（东财直连HTTP）"""
    return datahub_service.news()


@router.get("/news/stock")
async def news_stock(symbol: str, limit: int = 30):
    """个股新闻"""
    return datahub_service.news_stock(symbol, limit)


@router.get("/news/global")
async def news_global(limit: int = 30):
    """全球资讯"""
    return datahub_service.news_global(limit)


# ==================== 基础数据层（fundamental） ====================

@router.get("/fundamental/f10")
async def fundamental_f10(symbol: str, category: str = "cwzy"):
    """F10数据（九大类: cwzy/gshg/gdbd/zygc/jbxx/sdlt/sdlc/gqjg/ygbb）"""
    return datahub_service.fundamental_f10(symbol, category)


@router.get("/fundamental/f10-all")
async def fundamental_f10_all(symbol: str):
    """F10全部九大类"""
    return datahub_service.fundamental_f10_all(symbol)


@router.get("/fundamental/quarterly")
async def fundamental_quarterly(symbol: str):
    """季报37字段"""
    return datahub_service.fundamental_quarterly(symbol)


@router.get("/fundamental/balance")
async def fundamental_balance(symbol: str):
    """资产负债表"""
    return datahub_service.fundamental_balance_sheet(symbol)


@router.get("/fundamental/cashflow")
async def fundamental_cashflow(symbol: str):
    """现金流量表"""
    return datahub_service.fundamental_cashflow(symbol)


@router.get("/fundamental/stock/{symbol}")
async def fundamental_stock(symbol: str):
    """个股基础数据全量"""
    return datahub_service.fundamental_stock_full(symbol)


# ==================== 公告层（announcement） ====================

@router.get("/announcements")
async def announcements(
    symbol: str = "",
    page: int = 1,
    pagesize: int = 30,
    days: int = 7,
):
    """公告查询（巨潮cninfo 沪深北全量）"""
    return datahub_service.announcements(symbol, page, pagesize, days)


@router.get("/announcements/stock/{symbol}")
async def announcements_stock(symbol: str, page: int = 1, pagesize: int = 30):
    """个股公告"""
    return datahub_service.announcements_stock(symbol, page, pagesize)


@router.get("/announcements/latest")
async def announcements_latest(days: int = 3, pagesize: int = 50):
    """最新全市场公告"""
    return datahub_service.announcements_latest(days, pagesize)