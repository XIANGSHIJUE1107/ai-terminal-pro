# -*- coding: utf-8 -*-
"""
技术指标计算模块
MA, MACD, KDJ, RSI, BOLL 计算并写入数据库
"""

import numpy as np
import pandas as pd

from ..data.database import get_stock_daily, insert_tech_indicator, get_tech_indicator
from ..config import PORTFOLIO


def compute_ma(series: pd.Series, periods: list[int]) -> pd.DataFrame:
    """计算多周期简单移动平均"""
    result = pd.DataFrame(index=series.index)
    for p in periods:
        result[f"ma{p}"] = series.rolling(window=p, min_periods=p).mean()
    return result


def compute_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """计算 MACD"""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd = 2 * (dif - dea)
    return pd.DataFrame({"dif": dif, "dea": dea, "macd": macd}, index=close.index)


def compute_kdj(df: pd.DataFrame, n: int = 9) -> pd.DataFrame:
    """计算 KDJ 指标"""
    low_min = df["low"].rolling(window=n, min_periods=n).min()
    high_max = df["high"].rolling(window=n, min_periods=n).max()

    rsv = ((df["close"] - low_min) / (high_max - low_min + 1e-10)) * 100

    k = rsv.ewm(com=2, adjust=False, min_periods=n).mean()
    d = k.ewm(com=2, adjust=False, min_periods=n).mean()
    j = 3 * k - 2 * d

    return pd.DataFrame({"k": k, "d": d, "j": j}, index=df.index)


def compute_rsi(close: pd.Series, periods: list[int] = [6, 12, 24]) -> pd.DataFrame:
    """计算多个周期的 RSI"""
    result = pd.DataFrame(index=close.index)
    for p in periods:
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.ewm(span=p, adjust=False, min_periods=p).mean()
        avg_loss = loss.ewm(span=p, adjust=False, min_periods=p).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        result[f"rsi{p}"] = 100 - 100 / (1 + rs)
    return result


def compute_boll(close: pd.Series, period: int = 20, std_mult: float = 2.0) -> pd.DataFrame:
    """计算布林带"""
    mid = close.rolling(window=period, min_periods=period).mean()
    std = close.rolling(window=period, min_periods=period).std()
    upper = mid + std_mult * std
    lower = mid - std_mult * std
    return pd.DataFrame({"boll_upper": upper, "boll_mid": mid, "boll_lower": lower}, index=close.index)


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    输入一只股票的标准日线 DataFrame（含 date, open, high, low, close, volume, symbol）
    返回包含所有技术指标列的 DataFrame
    """
    df = df.sort_values("date").reset_index(drop=True).copy()
    close = df["close"]

    # MA
    ma_df = compute_ma(close, [5, 10, 20, 60, 120])

    # MACD
    macd_df = compute_macd(close)

    # KDJ
    kdj_df = compute_kdj(df)

    # RSI
    rsi_df = compute_rsi(close)

    # BOLL
    boll_df = compute_boll(close)

    # 合并
    result = df[["date", "symbol"]].copy()
    result = pd.concat([result, ma_df, macd_df, kdj_df, rsi_df, boll_df], axis=1)

    return result


def batch_update():
    """遍历持仓，计算最新日指标并写入数据库"""
    print(f"[Indicator] 开始批量计算技术指标...")
    for name, symbol in PORTFOLIO.items():
        try:
            # 获取已有指标的最新日期
            existing = get_tech_indicator(symbol)
            if not existing.empty:
                existing["date"] = pd.to_datetime(existing["date"])
                latest_indicator_date = existing["date"].max()
            else:
                latest_indicator_date = None

            # 获取全量日线
            daily_df = get_stock_daily(symbol)
            if daily_df.empty:
                print(f"[Indicator] {name}({symbol}) 无日线数据，跳过")
                continue

            daily_df["date"] = pd.to_datetime(daily_df["date"])

            # 计算全量指标
            full_indicators = compute_indicators(daily_df)
            full_indicators["date"] = pd.to_datetime(full_indicators["date"])

            # 只插入新增的行
            if latest_indicator_date is not None:
                new_rows = full_indicators[full_indicators["date"] > latest_indicator_date]
            else:
                new_rows = full_indicators

            if not new_rows.empty:
                new_rows["date"] = new_rows["date"].dt.strftime("%Y-%m-%d")
                # 只保留需要的列
                cols = ["date", "symbol", "ma5", "ma10", "ma20", "ma60", "ma120",
                        "dif", "dea", "macd", "k", "d", "j",
                        "rsi6", "rsi12", "rsi24",
                        "boll_upper", "boll_mid", "boll_lower"]
                new_rows = new_rows[[c for c in cols if c in new_rows.columns]]
                insert_tech_indicator(new_rows)
                print(f"[Indicator] {name}({symbol}) 新增 {len(new_rows)} 条指标")
            else:
                print(f"[Indicator] {name}({symbol}) 指标已是最新")

        except Exception as e:
            print(f"[Indicator] {name}({symbol}) 计算失败: {e}")


if __name__ == "__main__":
    batch_update()