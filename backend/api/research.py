# -*- coding: utf-8 -*-
"""AI研究报告中心 API - 集成七层架构研报层"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

from backend.ai.service import ai_service
from backend.datahub import datahub_service
from backend.models.database import get_session, ResearchReport
from backend.config import PORTFOLIO
from datetime import datetime

router = APIRouter()


@router.get("/reports")
async def get_research_reports(
    symbol: str = Query(""),
    page: int = Query(1, ge=1),
    type: str = Query("stock", description="stock / industry"),
):
    """获取研报列表（东财reportapi > 同花顺）"""
    if type == "industry":
        return datahub_service.research_industry_reports("", page)
    if symbol:
        return datahub_service.research_reports(symbol, page)
    return {"items": [], "total": 0, "message": "请指定 stock symbol 或使用 type=industry"}


@router.get("/reports/stock/{symbol}")
async def get_stock_reports(symbol: str, page: int = 1):
    """个股研报"""
    return datahub_service.research_reports(symbol, page)


@router.get("/reports/industry")
async def get_industry_reports(industry: str = "", page: int = 1):
    """行业研报"""
    return datahub_service.research_industry_reports(industry, page)


@router.get("/consensus/{symbol}")
async def get_consensus(symbol: str):
    """一致预期（分析师预测）"""
    return datahub_service.research_consensus(symbol)


@router.get("/iwencai")
async def iwencai_search(query: str):
    """iWenCai 自然语言搜索"""
    return datahub_service.research_iwencai(query)


@router.post("/generate")
async def generate_report(
    target_code: str = Query(...),
    target_name: str = Query(""),
    report_type: str = Query("stock", regex="^(stock|industry|theme)$"),
):
    """生成AI研究报告"""
    if not target_name:
        for n, c in PORTFOLIO.items():
            if c == target_code:
                target_name = n
                break

    messages = [
        {"role": "user", "content": ai_service.RESEARCH_PROMPT.format(
            name=target_name, symbol=target_code, report_type=report_type,
        )},
    ]

    try:
        content = await ai_service.chat(messages, max_tokens=4096)

        session = get_session()
        report = ResearchReport(
            report_type=report_type,
            target_code=target_code,
            target_name=target_name,
            title=f"{target_name}研究报告",
            content=content,
            ai_model="deepseek",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        session.add(report)
        session.commit()
        report_id = report.id
        session.close()

        return {
            "ok": True,
            "id": report_id,
            "title": f"{target_name}研究报告",
            "content": content,
        }
    except Exception as e:
        raise HTTPException(500, f"报告生成失败: {e}")


@router.get("/generate/stream")
async def generate_report_stream(
    target_code: str = Query(...),
    target_name: str = Query(""),
):
    """流式生成研究报告"""
    if not target_name:
        for n, c in PORTFOLIO.items():
            if c == target_code:
                target_name = n
                break

    messages = [
        {"role": "user", "content": ai_service.RESEARCH_PROMPT.format(
            name=target_name, symbol=target_code, report_type="stock",
        )},
    ]

    async def generate():
        try:
            async for chunk in ai_service.stream_chat(messages):
                yield chunk
        except Exception as e:
            yield f"\n[生成失败: {e}]"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.get("/list")
async def list_reports(report_type: str = None):
    """获取研究报告列表"""
    session = get_session()
    q = session.query(ResearchReport)
    if report_type:
        q = q.filter(ResearchReport.report_type == report_type)
    items = q.order_by(ResearchReport.created_at.desc()).limit(50).all()

    result = []
    for r in items:
        result.append({
            "id": r.id, "report_type": r.report_type,
            "target_code": r.target_code, "target_name": r.target_name,
            "title": r.title, "ai_model": r.ai_model,
            "created_at": r.created_at,
            "content_preview": (r.content or "")[:200],
        })
    session.close()
    return {"reports": result}


@router.get("/{report_id}")
async def get_report(report_id: int):
    """获取单篇报告"""
    session = get_session()
    r = session.query(ResearchReport).filter_by(id=report_id).first()
    if not r:
        session.close()
        raise HTTPException(404, "报告不存在")

    result = {
        "id": r.id, "report_type": r.report_type,
        "target_code": r.target_code, "target_name": r.target_name,
        "title": r.title, "content": r.content,
        "ai_model": r.ai_model, "created_at": r.created_at,
    }
    session.close()
    return result


@router.delete("/{report_id}")
async def delete_report(report_id: int):
    """删除报告"""
    session = get_session()
    r = session.query(ResearchReport).filter_by(id=report_id).first()
    if not r:
        session.close()
        raise HTTPException(404, "报告不存在")
    session.delete(r)
    session.commit()
    session.close()
    return {"ok": True}