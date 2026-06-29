# -*- coding: utf-8 -*-
"""新闻中心 API"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from backend.data_sources.news import news_source
from backend.datahub import datahub_service
from backend.ai.service import ai_service
from backend.models.database import get_session, News

router = APIRouter()


@router.get("/list")
async def get_news_list(
    limit: int = Query(50, ge=1, le=200),
    source: Optional[str] = None,
    sentiment: Optional[str] = None,
):
    """获取新闻列表"""
    result = news_source.get_news(limit=limit)
    items = result.get("items", [])
    if source:
        items = [i for i in items if i.get("source") == source]
    if sentiment:
        items = [i for i in items if i.get("sentiment") == sentiment]
    return {"news": items[:limit], "total": len(items), "source": result.get("source", "新闻聚合")}

    # Fallback: 本地数据库
    session = get_session()
    q = session.query(News)
    if source:
        q = q.filter(News.source == source)
    if sentiment:
        q = q.filter(News.sentiment == sentiment)
    items = q.order_by(News.ctime.desc()).limit(limit).all()

    result_list = []
    for n in items:
        result_list.append({
            "id": n.id, "fetch_time": n.fetch_time, "content": n.content,
            "ctime": n.ctime, "source": n.source or "cls",
            "sentiment": n.sentiment, "ai_summary": n.ai_summary,
            "related_stocks": n.related_stocks,
        })
    session.close()
    return {"news": result_list, "total": len(result_list), "source": "本地数据库"}


@router.get("/stock/{symbol}")
async def get_stock_news(symbol: str, limit: int = 30):
    """个股新闻（东财直连）"""
    return news_source.get_stock_news(symbol, limit)


@router.get("/global")
async def get_global_news(limit: int = 30):
    """全球资讯（东财直连）"""
    return news_source.get_global_news(limit)


@router.get("/sources")
async def get_news_sources():
    """新闻源状态"""
    return {
        "sources": {
            "东财直连HTTP": {"status": "active", "priority": 1, "features": ["个股新闻", "全球资讯"]},
            "同花顺": {"status": "active", "priority": 2, "features": ["个股新闻", "行业资讯"]},
            "新浪财经": {"status": "active", "priority": 3, "features": ["综合资讯"]},
            "财联社": {"status": "deprecated", "priority": 4, "note": "快讯已下线，仅保留本地库兜底"},
        },
        "rate_limiter": datahub_service.health().get("rate_limiter", {}),
    }


@router.post("/analyze/{news_id}")
async def analyze_news(news_id: int):
    """AI分析单条新闻"""
    session = get_session()
    news = session.query(News).filter_by(id=news_id).first()
    if not news:
        session.close()
        raise HTTPException(404, "新闻不存在")

    messages = [
        {"role": "system", "content": "你是一位资深财经分析师"},
        {"role": "user", "content": ai_service.NEWS_ANALYSIS_PROMPT.format(
            content=news.content, source=news.source or "财联社"
        )},
    ]

    try:
        import json
        result = await ai_service.chat(messages)
        try:
            analysis = json.loads(result)
        except json.JSONDecodeError:
            analysis = {"summary": result[:50], "sentiment": "neutral", "analysis": result}

        news.sentiment = analysis.get("sentiment", "neutral")
        news.ai_summary = analysis.get("summary", "")
        news.related_stocks = json.dumps(analysis.get("affected_stocks", []), ensure_ascii=False)
        session.commit()
        session.close()

        return {"ok": True, "analysis": analysis}
    except Exception as e:
        session.close()
        raise HTTPException(500, f"AI分析失败: {e}")


@router.post("/analyze/batch")
async def analyze_news_batch(limit: int = 20):
    """批量AI分析新闻"""
    session = get_session()
    items = session.query(News).filter(
        News.sentiment == None
    ).limit(limit).all()

    analyzed = 0
    for news in items:
        try:
            import json
            messages = [
                {"role": "user", "content": ai_service.NEWS_ANALYSIS_PROMPT.format(
                    content=news.content[:500], source=news.source or "财联社"
                )},
            ]
            result = await ai_service.chat(messages)
            analysis = json.loads(result) if result.startswith("{") else {"sentiment": "neutral", "summary": result[:50]}
            news.sentiment = analysis.get("sentiment", "neutral")
            news.ai_summary = analysis.get("summary", "")
            news.related_stocks = json.dumps(analysis.get("affected_stocks", []), ensure_ascii=False)
            analyzed += 1
        except Exception:
            continue

    session.commit()
    session.close()
    return {"ok": True, "analyzed": analyzed, "total": len(items)}


@router.get("/sentiment_stats")
async def news_sentiment_stats():
    """新闻情绪统计"""
    session = get_session()
    from sqlalchemy import func
    stats = session.query(
        News.sentiment, func.count(News.id)
    ).filter(
        News.sentiment != None
    ).group_by(News.sentiment).all()
    session.close()

    return {
        "stats": [{"sentiment": s, "count": c} for s, c in stats],
    }
