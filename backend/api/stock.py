# -*- coding: utf-8 -*-
"""个股分析 API - K线数据 + AI技术分析"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

from backend.services.market_service import market_service
from backend.ai.service import ai_service, AIService

router = APIRouter()


@router.get("/{symbol}/kline")
async def get_stock_kline(
    symbol: str,
    days: int = Query(120, ge=1, le=1000),
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
):
    """获取个股K线数据"""
    data = market_service.get_stock_detail(symbol, days=days)
    if not data:
        raise HTTPException(404, f"未找到股票 {symbol} 的数据")
    return data


@router.get("/{symbol}/analysis")
async def get_stock_analysis(symbol: str):
    """AI 技术分析"""
    data = market_service.get_stock_detail(symbol, days=60)
    if not data:
        raise HTTPException(404, f"未找到股票 {symbol} 的数据")

    # 从 PORTFOLIO 获取股票名称
    from backend.config import PORTFOLIO
    name = ""
    for n, s in PORTFOLIO.items():
        if s == symbol:
            name = n
            break

    indicators = data.get("indicators", {})
    indicator_text = f"""
最新价: {data['latest_price']}
涨跌幅: {data['change_pct']}%
MA5: {indicators.get('ma5', 'N/A')}
MA10: {indicators.get('ma10', 'N/A')}
MA20: {indicators.get('ma20', 'N/A')}
MA60: {indicators.get('ma60', 'N/A')}
MACD: DIF={indicators.get('dif', 'N/A')} DEA={indicators.get('dea', 'N/A')} MACD柱={indicators.get('macd', 'N/A')}
KDJ: K={indicators.get('k', 'N/A')} D={indicators.get('d', 'N/A')} J={indicators.get('j', 'N/A')}
RSI6={indicators.get('rsi6', 'N/A')} RSI12={indicators.get('rsi12', 'N/A')} RSI24={indicators.get('rsi24', 'N/A')}
布林带: 上轨={indicators.get('boll_upper', 'N/A')} 中轨={indicators.get('boll_mid', 'N/A')} 下轨={indicators.get('boll_lower', 'N/A')}
"""

    messages = [
        {"role": "system", "content": ai_service.TECH_ANALYSIS_PROMPT},
        {"role": "user", "content": ai_service.TECH_ANALYSIS_PROMPT.format(
            name=name or symbol, symbol=symbol,
            price=data['latest_price'],
            indicators=indicator_text,
        )},
    ]

    try:
        analysis = await ai_service.chat(messages)
        return {"symbol": symbol, "name": name, "analysis": analysis, "indicators": indicators}
    except Exception as e:
        # AI 不可用时返回基础技术指标
        return {
            "symbol": symbol, "name": name,
            "analysis": "AI分析暂不可用，请查看技术指标数据",
            "indicators": indicators,
            "error": str(e),
        }


@router.get("/{symbol}/analysis/stream")
async def get_stock_analysis_stream(symbol: str):
    """AI 技术分析（流式输出）"""
    data = market_service.get_stock_detail(symbol, days=60)
    if not data:
        raise HTTPException(404, f"未找到股票 {symbol} 的数据")

    from backend.config import PORTFOLIO
    name = ""
    for n, s in PORTFOLIO.items():
        if s == symbol:
            name = n
            break

    indicators = data.get("indicators", {})
    indicator_text = f"最新价:{data['latest_price']}, 涨跌幅:{data['change_pct']}%, MA5:{indicators.get('ma5', 'N/A')}, MA20:{indicators.get('ma20', 'N/A')}, MACD:{indicators.get('macd', 'N/A')}"

    messages = [
        {"role": "system", "content": "你是一位资深量化分析师，请对股票进行技术分析"},
        {"role": "user", "content": f"分析 {name}({symbol}) 技术面: {indicator_text}"},
    ]

    async def generate():
        try:
            async for chunk in ai_service.stream_chat(messages):
                yield chunk
        except Exception as e:
            yield f"\n\n[AI分析出错: {e}]"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.get("/{symbol}/signals")
async def get_stock_signals(symbol: str, days: int = 60):
    """获取股票信号"""
    from stock_platform.data.database import get_signals
    from datetime import datetime, timedelta

    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    signals = get_signals(symbol=symbol, start=start)

    return {
        "symbol": symbol,
        "signals": [
            {"date": row["date"], "type": row["signal_type"], "detail": row["detail"]}
            for _, row in (signals.iterrows() if not signals.empty else [])
        ],
    }


@router.get("/search")
async def search_stock(q: str):
    """搜索股票"""
    from backend.config import PORTFOLIO
    results = []
    for name, symbol in PORTFOLIO.items():
        if q.upper() in symbol or q in name:
            results.append({"symbol": symbol, "name": name, "market": "A"})
    return {"results": results}