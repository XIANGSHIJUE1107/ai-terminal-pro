# -*- coding: utf-8 -*-
"""自选股管理 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from backend.models.database import get_session, Watchlist

router = APIRouter()


class WatchlistCreate(BaseModel):
    symbol: str
    name: str
    market: str = "A"
    tags: str = "[]"
    notes: str = ""
    position: Optional[float] = None
    cost: Optional[float] = None


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    market: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None
    position: Optional[float] = None
    cost: Optional[float] = None


@router.get("/list")
async def get_watchlist(market: Optional[str] = None, tag: Optional[str] = None):
    """获取自选股列表"""
    session = get_session()
    q = session.query(Watchlist)
    if market:
        q = q.filter(Watchlist.market == market)
    items = q.all()

    result = []
    for w in items:
        result.append({
            "id": w.id, "symbol": w.symbol, "name": w.name,
            "market": w.market, "tags": w.tags, "notes": w.notes,
            "position": w.position, "cost": w.cost,
            "created_at": w.created_at,
        })
    session.close()
    return {"watchlist": result, "total": len(result)}


@router.post("/add")
async def add_watchlist(item: WatchlistCreate):
    """添加自选股"""
    session = get_session()
    existing = session.query(Watchlist).filter_by(symbol=item.symbol).first()
    if existing:
        session.close()
        raise HTTPException(400, f"股票 {item.symbol} 已存在")

    w = Watchlist(
        symbol=item.symbol, name=item.name, market=item.market,
        tags=item.tags, notes=item.notes,
        position=item.position, cost=item.cost,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    session.add(w)
    session.commit()
    session.close()
    return {"ok": True, "id": w.id}


@router.put("/{item_id}")
async def update_watchlist(item_id: int, data: WatchlistUpdate):
    """更新自选股"""
    session = get_session()
    w = session.query(Watchlist).filter_by(id=item_id).first()
    if not w:
        session.close()
        raise HTTPException(404, "自选股不存在")

    for k, v in data.dict(exclude_none=True).items():
        setattr(w, k, v)
    w.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.commit()
    session.close()
    return {"ok": True}


@router.delete("/{item_id}")
async def delete_watchlist(item_id: int):
    """删除自选股"""
    session = get_session()
    w = session.query(Watchlist).filter_by(id=item_id).first()
    if not w:
        session.close()
        raise HTTPException(404, "自选股不存在")
    session.delete(w)
    session.commit()
    session.close()
    return {"ok": True}


@router.get("/markets")
async def get_markets():
    """获取支持的市场列表"""
    return {
        "markets": [
            {"code": "A", "name": "A股"},
            {"code": "HK", "name": "港股"},
            {"code": "US", "name": "美股"},
            {"code": "ETF", "name": "ETF"},
            {"code": "INDEX", "name": "指数"},
            {"code": "SECTOR", "name": "行业板块"},
            {"code": "FUTURE", "name": "期货"},
            {"code": "GOLD", "name": "黄金"},
            {"code": "FX", "name": "外汇"},
            {"code": "CRYPTO", "name": "加密货币"},
        ]
    }