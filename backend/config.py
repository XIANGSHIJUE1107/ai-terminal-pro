# -*- coding: utf-8 -*-
"""
全局配置 - AI智能投研分析平台 Professional Edition
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ============ 服务器 ============
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# ============ 数据库 ============
DB_PATH = os.getenv("DB_PATH", "sqlite:///stock_platform.db")

# ============ Redis ============
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ============ AKShare 数据源 ============
AKSHARE_TIMEOUT = 30
AKSHARE_RETRY = 3

# ============ AI 模型配置 ============
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

# AI 默认模型
AI_DEFAULT_MODEL = os.getenv("AI_DEFAULT_MODEL", "deepseek")

# ============ 核心持仓 ============
PORTFOLIO = {
    "亨通光电": "600487",
    "立讯精密": "002475",
    "东山精密": "002384",
    "华工科技": "000988",
    "贵研铂业": "600459",
    "晋拓股份": "603211",
    "有研新材": "600206",
    "风华高科": "000636",
}

# ============ A股大盘指数 ============
A_INDEX_CODES = {
    "sh000001": "上证指数",
    "sz399001": "深证成指",
    "sz399006": "创业板指",
    "sh000300": "沪深300",
    "sh000852": "中证1000",
    "sh000688": "科创50",
}

# ============ 全球指数 ============
GLOBAL_INDEX_CODES = {
    # 港股
    "HSI": "恒生指数",
    "HSTECH": "恒生科技",
    # 美股
    ".DJI": "道琼斯工业",
    ".IXIC": "纳斯达克",
    ".INX": "标普500",
    ".RUT": "罗素2000",
    # 亚太
    "KS11": "韩国KOSPI",
    "N225": "日经225",
    # 欧洲
    "GDAXI": "德国DAX",
    # 恐慌指数
    "VIX": "VIX恐慌指数",
}

# ============ 数据起始日期 ============
START_DATE = "20200101"

# ============ ETF列表 ============
ETF_LIST = {
    "机器人ETF": "562500",
    "人工智能ETF": "159819",
    "芯片ETF": "159995",
    "算力ETF": "159665",
    "军工ETF": "512660",
    "黄金ETF": "159934",
}

# ============ 热门行业板块 ============
HOT_SECTORS = [
    "机器人", "AI", "算力", "半导体", "军工",
    "商业航天", "消费电子", "光模块", "新能源", "创新药",
]

# ============ 预警配置 ============
ALERT_CONFIG = {
    "price_breakout_pct": 5.0,
    "volume_breakout_multiplier": 2.0,
    "ma_cross_pairs": [("ma5", "ma20"), ("ma10", "ma20")],
}

# ============ 新闻源 ============
NEWS_SOURCES = [
    "eastmoney",  # 东方财富（直连HTTP，优先）
    "tonghuashun",  # 同花顺
    "sina",       # 新浪财经（备用）
    "cls",        # 财联社（本地库兜底）
]

# ============ 七层数据源配置 ============
DATA_SOURCE_CONFIG = {
    "行情层": {
        "priority": ["mootdx", "tencent", "baidu", "akshare"],
        "mootdx_enabled": True,
        "tencent_enabled": True,
        "baidu_enabled": True,
        "features": ["K线(MA5/10/20)", "五档盘口", "PE/PB/市值", "指数/ETF"],
    },
    "研报层": {
        "priority": ["eastmoney_reportapi", "tonghuashun", "iwencai"],
        "eastmoney_report_enabled": True,
        "tonghuashun_enabled": True,
        "iwencai_enabled": True,
        "features": ["个股研报", "行业研报", "PDF下载", "一致预期", "NL搜索"],
    },
    "信号层": {
        "priority": ["tonghuashun", "eastmoney"],
        "tonghuashun_enabled": True,
        "eastmoney_enabled": True,
        "features": ["强势股", "题材归因", "北向资金", "板块归属", "资金流向(push2)", "龙虎榜", "解禁", "行业对比"],
    },
    "资金面": {
        "priority": ["eastmoney_datacenter", "eastmoney_push2"],
        "eastmoney_enabled": True,
        "features": ["融资融券", "大宗交易", "股东户数", "分红送转", "资金流(分钟+120日)"],
    },
    "新闻层": {
        "priority": ["eastmoney_http", "tonghuashun", "sina"],
        "eastmoney_enabled": True,
        "tonghuashun_enabled": True,
        "sina_enabled": True,
        "features": ["个股新闻", "全球资讯"],
    },
    "基础数据": {
        "priority": ["mootdx", "eastmoney", "sina"],
        "mootdx_enabled": True,
        "eastmoney_enabled": True,
        "sina_enabled": True,
        "features": ["季报37字段", "F10九大类", "财报三表"],
    },
    "公告层": {
        "priority": ["cninfo", "mootdx", "eastmoney"],
        "cninfo_enabled": True,
        "mootdx_enabled": True,
        "eastmoney_enabled": True,
        "features": ["沪深北全量公告"],
    },
}

# ============ 东财限流配置 ============
EASTMONEY_RATE_LIMIT = {
    "push2.eastmoney.com": 0.35,
    "push2his.eastmoney.com": 0.35,
    "data.eastmoney.com": 0.5,
    "datacenter.eastmoney.com": 0.5,
    "reportapi.eastmoney.com": 0.6,
    "emweb.securities.eastmoney.com": 0.5,
    "searchadapter.eastmoney.com": 0.4,
    "quote.eastmoney.com": 0.35,
    "pdf.dfcfw.com": 0.6,
    "np-anotice-stock.eastmoney.com": 0.5,
    "circuit_breaker_threshold": 5,
    "circuit_breaker_cooldown": 60,
}

# ============ 定时任务 ============
SCHEDULE_CONFIG = {
    "market_open": "09:25",
    "morning_snapshot": "10:00",
    "afternoon_snapshot": "14:00",
    "after_close": "15:30",
    "news_interval": 60,  # 新闻抓取间隔（秒）
    "datahub_refresh_interval": 600,  # DataHub全量刷新间隔（秒）
}
