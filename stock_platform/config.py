# -*- coding: utf-8 -*-
"""
全局配置文件
"""

# ============ 持仓标的 ============
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

# ============ 大盘指数代码 ============
INDEX_CODES = {
    "sh000001": "上证指数",
    "sz399001": "深证成指",
    "sz399006": "创业板指",
}

# ============ 美股三大指数 (AKShare sina 接口) ============
US_INDEX_CODES = {
    ".DJI": "道琼斯工业",
    ".IXIC": "纳斯达克",
    ".INX":  "标普500",
}

# ============ 韩国KOSPI ============
KOSPI_CODE = "KS11"

# ============ 数据库路径 ============
DB_PATH = "sqlite:///stock_platform.db"

# ============ 数据起始日期 ============
START_DATE = "20200101"

# ============ 信号检测参数 ============
SIGNAL_CONFIG = {
    "volume_breakout_multiplier": 1.5,      # 放量突破：成交量 > 均量 × 倍数
    "volume_shrink_multiplier": 0.5,        # 缩量回调：成交量 < 均量 × 倍数
    "new_high_days": 60,                     # 新高：收盘价创N日新高
    "ma_cross_pairs": [                      # MA金叉/死叉检测对
        ("ma5", "ma20"),
        ("ma10", "ma20"),
        ("ma5", "ma60"),
    ],
    "divergence_lookback": 60,               # 背离检测回顾窗口
}

# ============ 预测Agent参数 ============
PREDICTION_CONFIG = {
    "similar_samples": 30,                   # 相似样本数
    "feature_window": 20,                    # 特征窗口（最近N天）
    "history_window": 60,                    # 历史回溯窗口
    "horizons": [5, 10, 20],                 # 预测周期
    "min_history_days": 120,                 # 最少需要的历史数据天数
}

# ============ 调度时间 ============
SCHEDULE_CONFIG = {
    "morning_snapshot": "09:00",            # 早间板块资金快照
    "intraday_start": "09:30",              # 盘中抓取启动
    "after_close": "15:30",                 # 收盘后执行
}

# ============ 数据文件缓存路径 ============
CACHE_DIR = "./cache"
