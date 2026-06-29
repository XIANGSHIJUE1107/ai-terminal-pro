# -*- coding: utf-8 -*-
"""预警系统 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from backend.models.database import get_session, AlertRule

router = APIRouter()


class AlertCreate(BaseModel):
    symbol: str
    name: str
    alert_type: str  # price/volume/ma/news
    condition: str   # JSON 条件
    channels: str = "web"
    enabled: bool = True


class AlertUpdate(BaseModel):
    name: Optional[str] = None
    condition: Optional[str] = None
    channels: Optional[str] = None
    enabled: Optional[bool] = None


@router.get("/list")
async def get_alerts(symbol: Optional[str] = None):
    """获取预警列表"""
    session = get_session()
    q = session.query(AlertRule)
    if symbol:
        q = q.filter(AlertRule.symbol == symbol)
    items = q.all()
    result = []
    for a in items:
        result.append({
            "id": a.id, "symbol": a.symbol, "name": a.name,
            "alert_type": a.alert_type, "condition": a.condition,
            "channels": a.channels, "enabled": bool(a.enabled),
            "created_at": a.created_at,
        })
    session.close()
    return {"alerts": result}


@router.post("/add")
async def add_alert(data: AlertCreate):
    """添加预警"""
    session = get_session()
    a = AlertRule(
        symbol=data.symbol, name=data.name,
        alert_type=data.alert_type, condition=data.condition,
        channels=data.channels, enabled=int(data.enabled),
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    session.add(a)
    session.commit()
    session.close()
    return {"ok": True, "id": a.id}


@router.put("/{alert_id}")
async def update_alert(alert_id: int, data: AlertUpdate):
    """更新预警"""
    session = get_session()
    a = session.query(AlertRule).filter_by(id=alert_id).first()
    if not a:
        session.close()
        raise HTTPException(404, "预警不存在")
    for k, v in data.dict(exclude_none=True).items():
        if k == "enabled":
            v = int(v)
        setattr(a, k, v)
    session.commit()
    session.close()
    return {"ok": True}


@router.put("/{alert_id}/toggle")
async def toggle_alert(alert_id: int):
    """切换预警开关"""
    session = get_session()
    a = session.query(AlertRule).filter_by(id=alert_id).first()
    if not a:
        session.close()
        raise HTTPException(404, "预警不存在")
    a.enabled = 1 if a.enabled == 0 else 0
    session.commit()
    session.close()
    return {"ok": True, "enabled": bool(a.enabled)}


@router.delete("/{alert_id}")
async def delete_alert(alert_id: int):
    """删除预警"""
    session = get_session()
    a = session.query(AlertRule).filter_by(id=alert_id).first()
    if not a:
        session.close()
        raise HTTPException(404, "预警不存在")
    session.delete(a)
    session.commit()
    session.close()
    return {"ok": True}


@router.get("/channels")
async def get_channels():
    """获取支持的通知渠道"""
    return {
        "channels": [
            {"code": "web", "name": "网页通知"},
            {"code": "wecom", "name": "企业微信"},
            {"code": "wechat", "name": "微信"},
            {"code": "email", "name": "邮件"},
            {"code": "telegram", "name": "Telegram"},
            {"code": "dingtalk", "name": "钉钉"},
        ]
    }