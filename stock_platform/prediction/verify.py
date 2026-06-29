# -*- coding: utf-8 -*-
"""
验证 Agent
检查到期预测并更新验证表，统计胜率
"""

from datetime import datetime

import pandas as pd

from ..data.database import (
    get_unverified_predictions, get_stock_daily,
    insert_verify_records, get_predictions, get_verify_stats,
)


def verify_expired_predictions():
    """
    检查所有到期预测，验证并更新验证表
    """
    print(f"\n[Verify] 开始验证过期预测 {datetime.now()}")

    predictions = get_unverified_predictions()
    if predictions.empty:
        print("[Verify] 无待验证预测")
        return

    verify_records = []
    for _, pred in predictions.iterrows():
        try:
            pred_id = pred["id"]
            symbol = pred["symbol"]
            pred_date = pred["pred_date"]
            horizon = pred["horizon"]
            direction = pred["direction"]
            invalid_condition = pred["invalid_condition"]

            # 获取预测日期之后的日线数据
            daily_df = get_stock_daily(symbol, start=pred_date)
            if daily_df.empty or len(daily_df) < horizon:
                continue

            # 取预测日期的索引
            daily_df = daily_df.sort_values("date").reset_index(drop=True)
            pred_idx = daily_df[daily_df["date"] == pred_date].index
            if len(pred_idx) == 0:
                continue
            pred_idx = pred_idx[0]

            # 需要 horizon 天后的数据
            target_idx = pred_idx + horizon
            if target_idx >= len(daily_df):
                continue

            # 检查失效条件：期间内是否跌破支撑
            is_invalid = False
            invalid_reason = ""
            for i in range(pred_idx + 1, target_idx + 1):
                if "close" in daily_df.columns and "ma60" in daily_df.columns:
                    close = daily_df.iloc[i]["close"]
                    # 从失效条件中提取支撑位
                    # invalid_condition 格式如 "跌破MA60(12.34)"
                    if "ma60" in daily_df.columns:
                        ma60 = daily_df.iloc[i].get("ma60")
                        if pd.notna(ma60) and close < ma60:
                            is_invalid = True
                            invalid_reason = f"第{i - pred_idx}天跌破MA60: {close:.2f} < {ma60:.2f}"
                            break

            if is_invalid:
                verify_records.append({
                    "pred_id": pred_id,
                    "actual_close": daily_df.iloc[target_idx]["close"],
                    "result": "invalid",
                    "dev_reason": invalid_reason,
                    "profit_pct": 0,
                    "verify_date": datetime.now().strftime("%Y-%m-%d"),
                })
                continue

            # 计算实际收益
            start_close = daily_df.iloc[pred_idx]["close"]
            actual_close = daily_df.iloc[target_idx]["close"]
            profit_pct = (actual_close - start_close) / start_close

            # 判断方向是否正确
            actual_direction = "up" if profit_pct > 0 else "down"
            result = "correct" if actual_direction == direction else "incorrect"

            dev_reason = ""
            if result == "incorrect":
                dev_reason = f"预测{direction}, 实际{actual_direction}, 涨跌幅{profit_pct:.2%}"

            verify_records.append({
                "pred_id": pred_id,
                "actual_close": actual_close,
                "result": result,
                "dev_reason": dev_reason,
                "profit_pct": round(float(profit_pct), 4),
                "verify_date": datetime.now().strftime("%Y-%m-%d"),
            })

        except Exception as e:
            print(f"[Verify] 验证 pred_id={pred['id']} 失败: {e}")

    if verify_records:
        insert_verify_records(verify_records)
        print(f"[Verify] 写入 {len(verify_records)} 条验证记录")
    else:
        print("[Verify] 无新验证记录")

    print(f"[Verify] 验证完成\n")


def compute_win_rate() -> pd.DataFrame:
    """计算胜率统计"""
    return get_verify_stats()


def print_win_rate():
    """打印胜率统计"""
    stats = compute_win_rate()
    if stats.empty:
        print("[Verify] 暂无验证统计数据")
        return

    print("\n" + "=" * 60)
    print("预测胜率统计")
    print("=" * 60)
    for _, row in stats.iterrows():
        print(f"{row['symbol']} | 周期{row['horizon']}日 | "
              f"胜率{row['win_rate']:.1f}% | "
              f"正确{int(row['correct'])}/总数{int(row['total'])}")
    print("=" * 60)


if __name__ == "__main__":
    verify_expired_predictions()
    print_win_rate()