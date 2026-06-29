# -*- coding: utf-8 -*-
"""大盘复盘系统 API"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from backend.services.market_service import market_service
from backend.ai.service import ai_service

router = APIRouter()


@router.get("/daily")
async def daily_review(date: str = None):
    """获取每日复盘数据"""
    indices = market_service.get_index_overview()
    sectors = market_service.get_sector_flow_data()
    breadth = market_service.get_market_breadth()

    return {
        "date": date or breadth.get("date", ""),
        "indices": indices,
        "sectors": sectors[:10],
        "breadth": breadth,
    }


@router.get("/generate")
async def generate_daily_review(date: str = None):
    """AI生成每日复盘"""
    indices = market_service.get_index_overview()
    sectors = market_service.get_sector_flow_data()
    breadth = market_service.get_market_breadth()

    index_text = "\n".join([
        f"{i['name']}: {i['close']} ({i['change_pct']:+.2f}%)"
        for i in indices.get("a_shares", [])
    ])

    sector_text = "\n".join([
        f"{s['sector_name']}: 净流入{s.get('main_net_inflow', 0):.0f}万"
        for s in sectors[:8]
    ])

    messages = [
        {"role": "system", "content": ai_service.DAILY_REVIEW_PROMPT},
        {"role": "user", "content": ai_service.DAILY_REVIEW_PROMPT.format(
            index_data=index_text,
            sector_data=sector_text,
            fund_data=f"上涨板块{breadth['up_sectors']}个, 下跌板块{breadth['down_sectors']}个",
        )},
    ]

    try:
        review = await ai_service.chat(messages)
        return {"date": breadth.get("date", ""), "review": review}
    except Exception as e:
        return {"error": str(e), "review": "AI复盘生成失败，请稍后重试"}


@router.get("/generate/stream")
async def generate_daily_review_stream():
    """AI生成每日复盘（流式）"""
    indices = market_service.get_index_overview()
    sectors = market_service.get_sector_flow_data()
    breadth = market_service.get_market_breadth()

    index_text = "\n".join([
        f"{i['name']}: {i['close']} ({i['change_pct']:+.2f}%)"
        for i in indices.get("a_shares", [])
    ])

    messages = [
        {"role": "user", "content": ai_service.DAILY_REVIEW_PROMPT.format(
            index_data=index_text,
            sector_data=str(sectors[:5]),
            fund_data=f"上涨{breadth['up_sectors']}个, 下跌{breadth['down_sectors']}个",
        )},
    ]

    async def generate():
        try:
            async for chunk in ai_service.stream_chat(messages):
                yield chunk
        except Exception as e:
            yield f"\n[生成失败: {e}]"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.get("/etf")
async def etf_analysis():
    """ETF分析"""
    from backend.config import ETF_LIST
    return {"etfs": [{"name": n, "code": c} for n, c in ETF_LIST.items()]}
