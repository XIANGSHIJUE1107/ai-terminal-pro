# -*- coding: utf-8 -*-
"""
A 股全栈数据 · 七层架构 · V3.2.4
优先级：mootdx/腾讯 不封IP 优先用；东财仅用于独有数据，已内置限流防封
"""
from backend.data_sources.base import (
    to_float, with_prefix, code6, now_text, now_dt, safe_json,
    TDX_SERVERS, probe_tdx,
)
from backend.data_sources.rate_limiter import rate_limiter

# 延迟导入避免循环依赖
def _get_market_source():
    from backend.data_sources.market import market_source as ms
    return ms

def _get_research_source():
    from backend.data_sources.research import research_source as rs
    return rs

def _get_signal_source():
    from backend.data_sources.signal import signal_source as ss
    return ss

def _get_fundflow_source():
    from backend.data_sources.fundflow import fundflow_source as fs
    return fs

def _get_news_source():
    from backend.data_sources.news import news_source as ns
    return ns

def _get_fundamental_source():
    from backend.data_sources.fundamental import fundamental_source as fs
    return fs

def _get_announcement_source():
    from backend.data_sources.announcement import announcement_source as as_
    return as_


# 直接导出类（兼容旧代码）
from backend.data_sources.market import MarketDataSource
from backend.data_sources.research import ResearchDataSource
from backend.data_sources.signal import SignalDataSource
from backend.data_sources.fundflow import FundFlowDataSource
from backend.data_sources.news import NewsDataSource
from backend.data_sources.fundamental import FundamentalDataSource
from backend.data_sources.announcement import AnnouncementDataSource