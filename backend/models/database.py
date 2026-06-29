# -*- coding: utf-8 -*-
"""数据库模型与初始化 - SQLAlchemy + SQLite"""
import os
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, String, Float, Integer, Text, Date, DateTime,
    PrimaryKeyConstraint, ForeignKey, Index
)
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import DB_PATH

# 从 SQLAlchemy 格式提取文件路径
_db_file = DB_PATH.replace("sqlite:///", "")
_db_abs = os.path.join(os.path.dirname(os.path.dirname(__file__)), _db_file)

engine = create_engine(f"sqlite:///{_db_abs}", echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# ============ 股票日线 ============
class StockDaily(Base):
    __tablename__ = "stock_daily"
    date = Column(String(10), primary_key=True)
    symbol = Column(String(10), primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    __table_args__ = (PrimaryKeyConstraint("date", "symbol"),)


# ============ 指数日线 ============
class IndexDaily(Base):
    __tablename__ = "index_daily"
    date = Column(String(10), primary_key=True)
    code = Column(String(20), primary_key=True)
    name = Column(String(50))
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    __table_args__ = (PrimaryKeyConstraint("date", "code"),)


# ============ 板块资金流向 ============
class SectorFundFlow(Base):
    __tablename__ = "sector_fund_flow"
    date = Column(String(10), primary_key=True)
    sector_name = Column(String(50), primary_key=True)
    main_net_inflow = Column(Float)
    super_large_net = Column(Float)
    large_net = Column(Float)
    mid_net = Column(Float)
    small_net = Column(Float)
    change_pct = Column(Float)
    __table_args__ = (PrimaryKeyConstraint("date", "sector_name"),)


# ============ 技术指标 ============
class TechIndicator(Base):
    __tablename__ = "tech_indicator"
    date = Column(String(10), primary_key=True)
    symbol = Column(String(10), primary_key=True)
    ma5 = Column(Float)
    ma10 = Column(Float)
    ma20 = Column(Float)
    ma60 = Column(Float)
    ma120 = Column(Float)
    dif = Column(Float)
    dea = Column(Float)
    macd = Column(Float)
    k = Column(Float)
    d = Column(Float)
    j = Column(Float)
    rsi6 = Column(Float)
    rsi12 = Column(Float)
    rsi24 = Column(Float)
    boll_upper = Column(Float)
    boll_mid = Column(Float)
    boll_lower = Column(Float)
    __table_args__ = (PrimaryKeyConstraint("date", "symbol"),)


# ============ 信号事件 ============
class SignalEvent(Base):
    __tablename__ = "signal_event"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10))
    symbol = Column(String(10))
    signal_type = Column(String(50))
    detail = Column(Text)


# ============ 预测记录 ============
class Prediction(Base):
    __tablename__ = "prediction"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pred_date = Column(String(10))
    symbol = Column(String(10))
    horizon = Column(Integer)
    direction = Column(String(10))
    probability = Column(Float)
    target_price = Column(Float)
    invalid_condition = Column(Text)
    is_valid = Column(Integer, default=1)


# ============ 预测验证 ============
class PredictionVerify(Base):
    __tablename__ = "prediction_verify"
    pred_id = Column(Integer, ForeignKey("prediction.id"), primary_key=True)
    actual_close = Column(Float)
    result = Column(String(20))
    dev_reason = Column(Text)
    profit_pct = Column(Float)
    verify_date = Column(String(10))


# ============ 新闻 ============
class News(Base):
    __tablename__ = "cls_news"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fetch_time = Column(String(30))
    content = Column(Text)
    ctime = Column(String(30))
    source = Column(String(30), default="cls")
    sentiment = Column(String(10))      # positive/negative/neutral
    ai_summary = Column(Text)           # AI摘要
    related_stocks = Column(Text)       # 关联股票 JSON


# ============ 自选股 ============
class Watchlist(Base):
    __tablename__ = "watchlist"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20))
    name = Column(String(50))
    market = Column(String(10))          # A/HK/US/ETF/INDEX/FUTURE/GOLD/FX/CRYPTO
    tags = Column(String(200))           # 标签 JSON
    notes = Column(Text)                 # 备注
    position = Column(Float)             # 仓位
    cost = Column(Float)                 # 成本
    created_at = Column(String(20))
    updated_at = Column(String(20))


# ============ 预警规则 ============
class AlertRule(Base):
    __tablename__ = "alert_rule"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20))
    name = Column(String(50))
    alert_type = Column(String(30))      # price/volume/ma/news
    condition = Column(Text)             # 条件 JSON
    channels = Column(String(100))       # 通知渠道
    enabled = Column(Integer, default=1)
    created_at = Column(String(20))


# ============ AI 研究报告 ============
class ResearchReport(Base):
    __tablename__ = "research_report"
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_type = Column(String(20))     # stock/industry/theme
    target_code = Column(String(20))
    target_name = Column(String(100))
    title = Column(String(200))
    content = Column(Text)               # Markdown 内容
    ai_model = Column(String(30))
    created_at = Column(String(20))
    export_formats = Column(String(50))  # 导出格式


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
    print(f"[DB] 数据库初始化完成: {_db_abs}")
    _seed_watchlist()


def get_session():
    """获取数据库会话"""
    return SessionLocal()


def _seed_watchlist():
    """初始化默认自选股"""
    session = SessionLocal()
    try:
        from backend.config import PORTFOLIO
        for name, symbol in PORTFOLIO.items():
            existing = session.query(Watchlist).filter_by(symbol=symbol).first()
            if not existing:
                w = Watchlist(
                    symbol=symbol,
                    name=name,
                    market="A",
                    tags='["核心持仓"]',
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
                session.add(w)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[DB] 初始化自选股失败: {e}")
    finally:
        session.close()