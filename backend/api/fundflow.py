# -*- coding: utf-8 -*-
"""资金流向中心 API - 集成七层架构资金面+信号层"""
from fastapi import APIRouter, Query

from backend.services.market_service import market_service
from backend.datahub import datahub_service
from backend.models.database import get_session, SectorFundFlow
from sqlalchemy import func

router = APIRouter()


@router.get("/overview")
async def fundflow_overview():
    """资金流向总览"""
    data = market_service.get_sector_flow_data()
    total_main = sum(s.get("main_net_inflow", 0) or 0 for s in data)
    total_super = sum(s.get("super_large_net", 0) or 0 for s in data)
    total_large = sum(s.get("large_net", 0) or 0 for s in data)

    return {
        "summary": {
            "total_main_net_inflow": round(total_main, 2),
            "total_super_large": round(total_super, 2),
            "total_large": round(total_large, 2),
        },
        "top_inflows": sorted(data, key=lambda x: x.get("main_net_inflow", 0) or 0, reverse=True)[:10],
        "top_outflows": sorted(data, key=lambda x: x.get("main_net_inflow", 0) or 0)[:10],
    }


@router.get("/trend")
async def fundflow_trend(days: int = 20):
    """资金流向趋势"""
    session = get_session()
    from datetime import datetime, timedelta
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    rows = session.query(
        SectorFundFlow.date,
        func.sum(SectorFundFlow.main_net_inflow).label("total_main"),
        func.sum(SectorFundFlow.super_large_net).label("total_super"),
        func.sum(SectorFundFlow.large_net).label("total_large"),
    ).filter(
        SectorFundFlow.date >= start
    ).group_by(SectorFundFlow.date).order_by(SectorFundFlow.date.asc()).all()

    result = []
    for r in rows:
        result.append({
            "date": r[0],
            "main_net_inflow": round(r[1], 2) if r[1] else 0,
            "super_large_net": round(r[2], 2) if r[2] else 0,
            "large_net": round(r[3], 2) if r[3] else 0,
        })
    session.close()
    return {"trend": result}


@router.get("/north")
async def north_bound():
    """北向资金数据（东财 push2）"""
    return datahub_service.signal_north_bound()


@router.get("/stock/{symbol}")
async def stock_fundflow(symbol: str, days: int = 120):
    """个股资金流（东财 push2）"""
    return datahub_service.fundflow_stock_fundflow(symbol, days)


@router.get("/stock/{symbol}/minute")
async def stock_fundflow_minute(symbol: str):
    """个股资金流（分钟级）"""
    return datahub_service.fundflow_stock_minute(symbol)


@router.get("/stock/{symbol}/margin")
async def stock_margin(symbol: str, days: int = 60):
    """融资融券"""
    return datahub_service.fundflow_margin(symbol, days)


@router.get("/stock/{symbol}/blocktrade")
async def stock_blocktrade(symbol: str, days: int = 30):
    """大宗交易"""
    return datahub_service.fundflow_block_trade(symbol, days)


@router.get("/stock/{symbol}/shareholder")
async def stock_shareholder(symbol: str):
    """股东户数"""
    return datahub_service.fundflow_shareholder(symbol)


@router.get("/stock/{symbol}/dividend")
async def stock_dividend(symbol: str):
    """分红送转"""
    return datahub_service.fundflow_dividend(symbol)


@router.get("/stock/{symbol}/full")
async def stock_fundflow_full(symbol: str):
    """个股资金面全量数据"""
    return datahub_service.fundflow_stock_full(symbol)


@router.get("/dragontiger")
async def dragontiger(date: str = "", top: int = 50):
    """龙虎榜"""
    return datahub_service.signal_dragon_tiger(date, top)


@router.get("/lockup")
async def lockup_expiry(days: int = 30):
    """限售解禁"""
    return datahub_service.signal_lockup_expiry(days)