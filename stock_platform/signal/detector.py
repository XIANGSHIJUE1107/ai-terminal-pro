# -*- coding: utf-8 -*-
"""
信号识别系统
MACD金叉/死叉、MA金叉/死叉、顶底背离、放量突破、缩量回调、新高突破、跌破支撑
"""

from datetime import datetime

import numpy as np
import pandas as pd

from ..config import PORTFOLIO, SIGNAL_CONFIG
from ..data.database import (
    get_stock_daily, get_tech_indicator, insert_signals, get_latest_date,
)


def detect_golden_cross(series_a: pd.Series, series_b: pd.Series, dates: pd.Series) -> list[dict]:
    """
    检测金叉：series_a 上穿 series_b
    返回: [{"date":..., "detail":...}, ...]
    """
    results = []
    for i in range(1, len(series_a)):
        if (series_a.iloc[i - 1] <= series_b.iloc[i - 1] and
                series_a.iloc[i] > series_b.iloc[i]):
            results.append({
                "date": str(dates.iloc[i]),
                "detail": f"上穿值: {series_a.iloc[i]:.2f} vs {series_b.iloc[i]:.2f}"
            })
    return results


def detect_death_cross(series_a: pd.Series, series_b: pd.Series, dates: pd.Series) -> list[dict]:
    """检测死叉：series_a 下穿 series_b"""
    results = []
    for i in range(1, len(series_a)):
        if (series_a.iloc[i - 1] >= series_b.iloc[i - 1] and
                series_a.iloc[i] < series_b.iloc[i]):
            results.append({
                "date": str(dates.iloc[i]),
                "detail": f"下穿值: {series_a.iloc[i]:.2f} vs {series_b.iloc[i]:.2f}"
            })
    return results


def detect_divergence(df: pd.DataFrame, price_col: str, indicator_col: str,
                      lookback: int, is_bottom: bool = False) -> list[dict]:
    """
    检测顶背离 / 底背离
    - 顶背离: 价格创新高，但指标峰值下降
    - 底背离: 价格创新低，但指标底部抬升
    """
    results = []
    if len(df) < lookback:
        return results

    dates = df["date"]
    prices = df[price_col].values
    indicators = df[indicator_col].values

    for i in range(lookback, len(prices)):
        window_prices = prices[i - lookback:i + 1]
        window_indicators = indicators[i - lookback:i + 1]

        if is_bottom:
            # 底背离: 价格新低，指标底抬升
            price_min_idx = np.argmin(window_prices)
            ind_min_idx = np.argmin(window_indicators)

            # 当前价格接近窗口低点，且价格创新低但指标未创新低
            current_p = prices[i]
            current_ind = indicators[i]
            prev_min_p = np.min(window_prices[:-1])
            prev_min_ind = np.min(window_indicators[:-1])

            if current_p <= prev_min_p and current_ind > prev_min_ind:
                results.append({
                    "date": str(dates.iloc[i]),
                    "detail": f"股价新低{current_p:.2f}, 指标{indicator_col}={current_ind:.2f}, 背离抬升"
                })
        else:
            # 顶背离: 价格新高，指标峰下降
            price_max_idx = np.argmax(window_prices)
            ind_max_idx = np.argmax(window_indicators)

            current_p = prices[i]
            current_ind = indicators[i]
            prev_max_p = np.max(window_prices[:-1])
            prev_max_ind = np.max(window_indicators[:-1])

            if current_p >= prev_max_p and current_ind < prev_max_ind:
                results.append({
                    "date": str(dates.iloc[i]),
                    "detail": f"股价新高{current_p:.2f}, 指标{indicator_col}={current_ind:.2f}, 背离下降"
                })

    return results


def detect_volume_breakout(df: pd.DataFrame, volume_col: str = "volume",
                           price_col: str = "close", n_days: int = 20,
                           vol_mult: float = None) -> list[dict]:
    """
    放量突破：价格向上突破前N日高点，且成交量大于均量×倍数
    """
    if vol_mult is None:
        vol_mult = SIGNAL_CONFIG["volume_breakout_multiplier"]

    results = []
    if len(df) < n_days:
        return results

    volume = df[volume_col].values
    close = df[price_col].values
    dates = df["date"].values

    for i in range(n_days, len(close)):
        prev_high = np.max(close[i - n_days:i])
        avg_vol = np.mean(volume[i - n_days:i])
        if close[i] > prev_high and volume[i] > avg_vol * vol_mult:
            vol_ratio = volume[i] / avg_vol if avg_vol > 0 else 0
            results.append({
                "date": str(dates[i]),
                "detail": f"突破前{n_days}日高点{prev_high:.2f}, 量能倍数: {vol_ratio:.1f}x"
            })
    return results


def detect_volume_shrink(df: pd.DataFrame, volume_col: str = "volume",
                         price_col: str = "close", ma_col: str = "ma20",
                         n_days: int = 20, vol_mult: float = None) -> list[dict]:
    """
    缩量回调：价格回踩MA，且成交量低于均量×倍数
    """
    if vol_mult is None:
        vol_mult = SIGNAL_CONFIG["volume_shrink_multiplier"]

    results = []
    if len(df) < n_days or ma_col not in df.columns:
        return results

    volume = df[volume_col].values
    close = df[price_col].values
    ma = df[ma_col].values
    dates = df["date"].values

    for i in range(n_days, len(close)):
        if pd.isna(ma[i]):
            continue
        avg_vol = np.mean(volume[i - n_days:i])
        # 价格接近MA（偏差在2%以内）
        near_ma = abs(close[i] - ma[i]) / ma[i] < 0.02
        if near_ma and volume[i] < avg_vol * vol_mult:
            vol_ratio = volume[i] / avg_vol if avg_vol > 0 else 0
            results.append({
                "date": str(dates[i]),
                "detail": f"回踩MA, 量能缩小至均量的{vol_ratio:.1%}"
            })
    return results


def detect_new_high(df: pd.DataFrame, price_col: str = "close",
                    n_days: int = None) -> list[dict]:
    """新高突破：收盘价创N日新高"""
    if n_days is None:
        n_days = SIGNAL_CONFIG["new_high_days"]

    results = []
    if len(df) < n_days:
        return results

    close = df[price_col].values
    dates = df["date"].values

    for i in range(n_days, len(close)):
        if close[i] >= np.max(close[i - n_days:i]):
            results.append({
                "date": str(dates[i]),
                "detail": f"创{n_days}日新高, 收盘价: {close[i]:.2f}"
            })
    return results


def detect_break_support(df: pd.DataFrame, price_col: str = "close",
                         ma60_col: str = "ma60") -> list[dict]:
    """跌破支撑：收盘价跌破MA60"""
    results = []
    if ma60_col not in df.columns:
        return results

    close = df[price_col].values
    ma60 = df[ma60_col].values
    dates = df["date"].values

    for i in range(1, len(close)):
        if pd.isna(ma60[i - 1]) or pd.isna(ma60[i]):
            continue
        # 前一日未跌破，今日跌破
        if close[i - 1] >= ma60[i - 1] and close[i] < ma60[i]:
            results.append({
                "date": str(dates[i]),
                "detail": f"跌破MA60, 收盘价: {close[i]:.2f}, MA60: {ma60[i]:.2f}"
            })
    return results


def scan_all():
    """
    扫描全部持仓，将信号写入数据库
    每次运行前清空旧信号（当天重新生成）
    """
    today = datetime.now().strftime("%Y-%m-%d")
    all_signals = []

    for name, symbol in PORTFOLIO.items():
        print(f"[Signal] 扫描 {name}({symbol})...")
        try:
            daily_df = get_stock_daily(symbol)
            tech_df = get_tech_indicator(symbol)
            if daily_df.empty or tech_df.empty:
                print(f"[Signal] {name}({symbol}) 数据不足，跳过")
                continue

            # 合并日线与技术指标
            df = pd.merge(daily_df, tech_df, on=["date", "symbol"], how="inner")
            df = df.sort_values("date").reset_index(drop=True)

            # --- MACD 金叉/死叉 ---
            macd_signals = []
            macd_signals += [
                {"symbol": symbol, "signal_type": "golden_cross_macd", **s}
                for s in detect_golden_cross(df["dif"], df["dea"], df["date"])
            ]
            macd_signals += [
                {"symbol": symbol, "signal_type": "death_cross_macd", **s}
                for s in detect_death_cross(df["dif"], df["dea"], df["date"])
            ]
            all_signals += macd_signals

            # --- MA 金叉/死叉 ---
            for ma_short, ma_long in SIGNAL_CONFIG["ma_cross_pairs"]:
                if ma_short in df.columns and ma_long in df.columns:
                    all_signals += [
                        {"symbol": symbol, "signal_type": f"golden_cross_{ma_short}_{ma_long}", **s}
                        for s in detect_golden_cross(df[ma_short], df[ma_long], df["date"])
                    ]
                    all_signals += [
                        {"symbol": symbol, "signal_type": f"death_cross_{ma_short}_{ma_long}", **s}
                        for s in detect_death_cross(df[ma_short], df[ma_long], df["date"])
                    ]

            # --- 顶背离/底背离 (MACD DIF) ---
            lookback = SIGNAL_CONFIG["divergence_lookback"]
            all_signals += [
                {"symbol": symbol, "signal_type": "top_divergence", **s}
                for s in detect_divergence(df, "close", "dif", lookback, is_bottom=False)
            ]
            all_signals += [
                {"symbol": symbol, "signal_type": "bottom_divergence", **s}
                for s in detect_divergence(df, "close", "dif", lookback, is_bottom=True)
            ]

            # --- 放量突破 ---
            all_signals += [
                {"symbol": symbol, "signal_type": "volume_breakout", **s}
                for s in detect_volume_breakout(df)
            ]

            # --- 缩量回调 ---
            all_signals += [
                {"symbol": symbol, "signal_type": "volume_shrink", **s}
                for s in detect_volume_shrink(df)
            ]

            # --- 新高突破 ---
            all_signals += [
                {"symbol": symbol, "signal_type": "new_high", **s}
                for s in detect_new_high(df)
            ]

            # --- 跌破支撑 ---
            all_signals += [
                {"symbol": symbol, "signal_type": "break_support", **s}
                for s in detect_break_support(df)
            ]

            print(f"[Signal] {name}({symbol}) 共检测到 {len(all_signals)} 个信号（累计）")

        except Exception as e:
            print(f"[Signal] {name}({symbol}) 扫描失败: {e}")
            import traceback
            traceback.print_exc()

    # 只保留当天的信号写入数据库
    today_signals = [s for s in all_signals if s["date"] == today]
    if today_signals:
        insert_signals(today_signals)
        print(f"[Signal] 写入 {len(today_signals)} 条当天信号")
    else:
        print(f"[Signal] 当天无新信号")

    return all_signals


if __name__ == "__main__":
    scan_all()