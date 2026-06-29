# -*- coding: utf-8 -*-
"""
预测 Agent
基于历史相似形态匹配的统计预测
"""

from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from ..config import PORTFOLIO, PREDICTION_CONFIG
from ..data.database import (
    get_stock_daily, get_tech_indicator, insert_predictions,
)


def build_feature_vector(df: pd.DataFrame, idx: int) -> np.ndarray | None:
    """
    构建某日的特征向量
    特征：最近20天的涨跌幅、MA排列状态、MACD位置、RSI超买超卖、量能变化
    """
    window = PREDICTION_CONFIG["feature_window"]
    if idx < window:
        return None

    features = []

    # 数据切片
    slice_df = df.iloc[idx - window + 1:idx + 1]

    # 1. 最近20天每日涨跌幅
    for i in range(window):
        if i >= len(slice_df):
            break
        ret = 0
        if "close" in slice_df.columns and i > 0:
            prev_close = slice_df["close"].iloc[i - 1] if pd.notna(slice_df["close"].iloc[i - 1]) else slice_df["close"].iloc[i]
            ret = (slice_df["close"].iloc[i] - prev_close) / prev_close if prev_close != 0 else 0
        features.append(ret)

    # 2. MA排列状态：MA5/MA10/MA20/MA60 的相对位置
    for ma in ["ma5", "ma10", "ma20", "ma60"]:
        if ma in df.columns:
            ma_val = df.iloc[idx][ma]
            close_val = df.iloc[idx]["close"]
            if pd.notna(ma_val) and pd.notna(close_val):
                features.append((close_val - ma_val) / ma_val)
            else:
                features.append(0)
        else:
            features.append(0)

    # 3. MACD DIF值及方向
    if "dif" in df.columns and "dea" in df.columns:
        dif_val = df.iloc[idx]["dif"]
        dea_val = df.iloc[idx]["dea"]
        macd_val = df.iloc[idx].get("macd", 0)
        features.append(dif_val if pd.notna(dif_val) else 0)
        features.append(dea_val if pd.notna(dea_val) else 0)
        features.append(macd_val if pd.notna(macd_val) else 0)
        features.append(
            ((dif_val - dea_val) / (abs(dea_val) + 1e-10)) if pd.notna(dif_val) and pd.notna(dea_val) else 0
        )
    else:
        features.extend([0, 0, 0, 0])

    # 4. RSI 超买超卖
    for rsi in ["rsi6", "rsi12", "rsi24"]:
        if rsi in df.columns:
            val = df.iloc[idx][rsi]
            features.append(val if pd.notna(val) else 50)
        else:
            features.append(50)

    # 5. 量能变化：近5日均量 vs 近20日均量
    if "volume" in df.columns:
        vol_5 = df["volume"].iloc[max(0, idx - 4):idx + 1].mean()
        vol_20 = df["volume"].iloc[max(0, idx - 19):idx + 1].mean()
        features.append(vol_5 / vol_20 if vol_20 > 0 else 1.0)
    else:
        features.append(1.0)

    # 6. 近5日和近20日累计涨跌幅
    if "close" in df.columns:
        for lookback in [5, 10, 20]:
            if idx >= lookback:
                ret = (df["close"].iloc[idx] - df["close"].iloc[idx - lookback]) / df["close"].iloc[idx - lookback]
            else:
                ret = 0
            features.append(ret if pd.notna(ret) else 0)
    else:
        features.extend([0, 0, 0])

    return np.array(features, dtype=float)


def find_similar_dates(df: pd.DataFrame, current_idx: int, top_n: int = 30) -> list:
    """
    寻找与当前形态最相似的历史日期
    返回: [(idx, distance), ...]
    """
    current_vec = build_feature_vector(df, current_idx)
    if current_vec is None:
        return []

    window = PREDICTION_CONFIG["feature_window"]
    min_history = PREDICTION_CONFIG["min_history_days"]

    distances = []
    for i in range(window + min_history, current_idx):
        hist_vec = build_feature_vector(df, i)
        if hist_vec is not None:
            # 归一化欧氏距离
            combined = np.vstack([current_vec, hist_vec])
            scaler = StandardScaler()
            combined_scaled = scaler.fit_transform(combined)
            dist = np.linalg.norm(combined_scaled[0] - combined_scaled[1])
            distances.append((i, dist))

    distances.sort(key=lambda x: x[1])
    return distances[:top_n]


def make_predictions(symbol: str) -> list[dict]:
    """
    为单只股票生成未来5/10/20日预测
    """
    daily_df = get_stock_daily(symbol)
    tech_df = get_tech_indicator(symbol)

    if daily_df.empty:
        print(f"[Predict] {symbol} 无日线数据")
        return []

    df = pd.merge(daily_df, tech_df, on=["date", "symbol"], how="left")
    df = df.sort_values("date").reset_index(drop=True)

    min_required = PREDICTION_CONFIG["min_history_days"]
    if len(df) < min_required:
        print(f"[Predict] {symbol} 数据不足({len(df)}天 < {min_required}天)")
        return []

    current_idx = len(df) - 1
    current_close = df.iloc[current_idx]["close"]
    current_date = df.iloc[current_idx]["date"]
    today = datetime.now().strftime("%Y-%m-%d")

    # 找相似历史样本
    similar = find_similar_dates(df, current_idx, top_n=PREDICTION_CONFIG["similar_samples"])
    if not similar:
        print(f"[Predict] {symbol} 无相似样本")
        return []

    # MA60支撑位
    ma60 = df.iloc[current_idx].get("ma60", current_close * 0.9)
    if pd.isna(ma60):
        ma60 = current_close * 0.9

    records = []
    horizons = PREDICTION_CONFIG["horizons"]

    for horizon in horizons:
        returns = []
        for hist_idx, _ in similar:
            future_idx = hist_idx + horizon
            if future_idx < len(df):
                future_close = df.iloc[future_idx]["close"]
                ret = (future_close - df.iloc[hist_idx]["close"]) / df.iloc[hist_idx]["close"]
                returns.append(ret)

        if not returns:
            continue

        returns = np.array(returns)
        up_count = np.sum(returns > 0)
        prob = up_count / len(returns)
        avg_return = np.mean(returns)
        target_price = current_close * (1 + avg_return)
        direction = "up" if prob >= 0.5 else "down"

        records.append({
            "pred_date": today,
            "symbol": symbol,
            "horizon": horizon,
            "direction": direction,
            "probability": round(float(prob), 4),
            "target_price": round(float(target_price), 2),
            "invalid_condition": f"跌破MA60({ma60:.2f})",
        })

        print(f"[Predict] {symbol} {horizon}日: 方向={direction}, 概率={prob:.2%}, 目标价={target_price:.2f}")

    return records


def run_predictions():
    """为所有持仓股生成预测"""
    print(f"\n[Predict] 开始生成预测 {datetime.now()}")
    for name, symbol in PORTFOLIO.items():
        try:
            records = make_predictions(symbol)
            if records:
                insert_predictions(records)
                print(f"[Predict] {name}({symbol}) 生成 {len(records)} 条预测")
        except Exception as e:
            print(f"[Predict] {name}({symbol}) 预测失败: {e}")
            import traceback
            traceback.print_exc()
    print(f"[Predict] 预测生成完成\n")


if __name__ == "__main__":
    run_predictions()