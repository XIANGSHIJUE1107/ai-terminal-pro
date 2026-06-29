# -*- coding: utf-8 -*-
"""首页 Dashboard API"""
from fastapi import APIRouter, Query
from backend.services.market_service import market_service

router = APIRouter()


@router.get("/overview")
async def dashboard_overview():
    """首页市场概览"""
    return {
        "indices": market_service.get_index_overview(),
        "portfolio": market_service.get_portfolio_summary(),
        "breadth": market_service.get_market_breadth(),
    }


@router.get("/portfolio")
async def portfolio_summary():
    """持仓概览"""
    return {"stocks": market_service.get_portfolio_summary()}


@router.get("/indices")
async def market_indices():
    """全球市场指数"""
    return market_service.get_index_overview()


@router.get("/sentiment")
async def market_sentiment():
    """AI市场温度计数据"""
    from backend.ai.service import ai_service
    breadth = market_service.get_market_breadth()
    sector_data = market_service.get_sector_flow_data()

    # 计算情绪分数
    up_ratio = breadth["up_sectors"] / max(breadth["total"], 1) * 100
    sentiment_map = {
        (80, 101): ("极度乐观", 85),
        (60, 80): ("乐观", 70),
        (40, 60): ("中性", 50),
        (20, 40): ("谨慎", 30),
        (0, 20): ("恐慌", 15),
    }
    sentiment = "中性"
    score = 50
    for (lo, hi), (s, sc) in sentiment_map.items():
        if lo <= up_ratio < hi:
            sentiment, score = s, sc
            break

    return {
        "sentiment": sentiment,
        "score": score,
        "up_ratio": round(up_ratio, 1),
        "up_sectors": breadth["up_sectors"],
        "down_sectors": breadth["down_sectors"],
        "top_inflows": sector_data[:5] if sector_data else [],
    }