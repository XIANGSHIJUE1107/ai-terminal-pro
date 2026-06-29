# -*- coding: utf-8 -*-
"""行业板块分析 API"""
from fastapi import APIRouter, Query
from typing import Optional

from backend.services.market_service import market_service
from backend.models.database import get_session, SectorFundFlow

router = APIRouter()


@router.get("/list")
async def get_sectors(date: Optional[str] = None):
    """获取板块列表（含资金流向）"""
    data = market_service.get_sector_flow_data(date)
    return {"sectors": data}


@router.get("/hot")
async def get_hot_sectors():
    """获取热门板块"""
    from backend.config import HOT_SECTORS
    data = market_service.get_sector_flow_data()
    hot = [s for s in data if any(h in s.get("sector_name", "") for h in HOT_SECTORS)]
    return {"hot_sectors": hot}


@router.get("/{sector_name}/history")
async def get_sector_history(sector_name: str, days: int = 30):
    """获取板块历史数据"""
    session = get_session()
    from datetime import datetime, timedelta
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = session.query(SectorFundFlow).filter(
        SectorFundFlow.sector_name == sector_name,
        SectorFundFlow.date >= start,
    ).order_by(SectorFundFlow.date.asc()).all()

    result = []
    for r in rows:
        result.append({
            "date": r.date,
            "sector_name": r.sector_name,
            "main_net_inflow": r.main_net_inflow,
            "super_large_net": r.super_large_net,
            "large_net": r.large_net,
            "mid_net": r.mid_net,
            "small_net": r.small_net,
            "change_pct": r.change_pct,
        })
    session.close()
    return {"history": result}


@router.get("/rankings")
async def get_sector_rankings(
    sort_by: str = Query("main_net_inflow", regex="^(main_net_inflow|change_pct)$"),
    top_n: int = 20,
):
    """板块排行"""
    data = market_service.get_sector_flow_data()
    sorted_data = sorted(data, key=lambda x: x.get(sort_by, 0) or 0, reverse=True)
    return {"rankings": sorted_data[:top_n], "sort_by": sort_by}