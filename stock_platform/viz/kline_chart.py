# -*- coding: utf-8 -*-
"""
K线图可视化模块（Plotly）
带信号标注、资金异动高亮、BOLL/MA/MACD/KDJ/RSI 副图
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..config import SIGNAL_CONFIG
from ..data.database import (
    get_stock_daily, get_tech_indicator, get_signals,
)


def plot_kline_with_signals(symbol: str, days: int = 120, show_indicators: list = None) -> go.Figure:
    """
    绘制带信号标注的交互式K线图
    Args:
        symbol: 股票代码
        days: 显示最近多少天
        show_indicators: 要显示的副图指标列表，可选 'volume', 'macd', 'kdj', 'rsi'
    """
    if show_indicators is None:
        show_indicators = ["volume", "macd"]

    # 获取数据
    daily_df = get_stock_daily(symbol)
    tech_df = get_tech_indicator(symbol)
    signals_df = get_signals(symbol=symbol)

    if daily_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="无数据", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

    # 合并数据
    df = pd.merge(daily_df, tech_df, on=["date", "symbol"], how="left")
    df = df.sort_values("date").reset_index(drop=True)

    # 截取最近 days 天
    df = df.tail(days).reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])

    # 子图布局
    main_rows = 1
    subplot_rows = len(show_indicators)
    total_rows = main_rows + subplot_rows

    row_heights = [0.5] + [0.5 / max(subplot_rows, 1)] * subplot_rows
    specs = [[{"type": "candlestick"}]] * main_rows
    for ind in show_indicators:
        if ind == "volume":
            specs.append([{"secondary_y": True}])
        else:
            specs.append([{"type": "scatter"}])

    fig = make_subplots(
        rows=total_rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        specs=specs,
    )

    # ========== 主图：K线 + MA + BOLL ==========
    # K线
    fig.add_trace(
        go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"],
            low=df["low"], close=df["close"],
            name="K线",
            increasing_line_color="#ef5350",
            decreasing_line_color="#26a69a",
        ),
        row=1, col=1
    )

    # MA 线
    ma_colors = {"ma5": "#FF6B6B", "ma10": "#FFA726", "ma20": "#AB47BC", "ma60": "#42A5F5", "ma120": "#78909C"}
    for ma_name, color in ma_colors.items():
        if ma_name in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["date"], y=df[ma_name],
                    mode="lines", name=ma_name.upper(),
                    line=dict(color=color, width=1.2),
                ),
                row=1, col=1
            )

    # BOLL 带
    if "boll_upper" in df.columns and "boll_lower" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"], y=df["boll_upper"],
                mode="lines", name="BOLL上轨",
                line=dict(color="rgba(173,216,230,0.6)", width=0.8),
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df["date"], y=df["boll_lower"],
                mode="lines", name="BOLL下轨",
                line=dict(color="rgba(173,216,230,0.6)", width=0.8),
                fill="tonexty", fillcolor="rgba(173,216,230,0.1)",
            ),
            row=1, col=1
        )

    # ========== 信号标注 ==========
    if not signals_df.empty:
        signals_df["date"] = pd.to_datetime(signals_df["date"])
        # 筛选最近 days 天的信号
        min_date = df["date"].min()
        recent_signals = signals_df[signals_df["date"] >= min_date]

        signal_markers = {
            "golden_cross_macd": ("金叉", "triangle-up", "green", 1.03),
            "death_cross_macd": ("死叉", "triangle-down", "red", 0.97),
            "volume_breakout": ("放量突破", "star", "orange", 1.05),
            "new_high": ("新高", "diamond", "gold", 1.04),
            "break_support": ("破支撑", "x", "red", 0.96),
            "top_divergence": ("顶背离", "triangle-down", "darkred", 1.04),
            "bottom_divergence": ("底背离", "triangle-up", "darkgreen", 0.96),
        }

        for _, sig in recent_signals.iterrows():
            sig_date = sig["date"]
            sig_type = sig["signal_type"]

            # 匹配信号标记
            marker_info = None
            for keyword, info in signal_markers.items():
                if keyword in sig_type:
                    marker_info = info
                    break

            if marker_info:
                label, symbol_marker, color, y_factor = marker_info
                # 找到对应日期的价格
                row_data = df[df["date"] == sig_date]
                if not row_data.empty:
                    y_val = row_data["high"].values[0] * y_factor if y_factor > 1 else row_data["low"].values[0] * y_factor
                    fig.add_trace(
                        go.Scatter(
                            x=[sig_date], y=[y_val],
                            mode="markers+text",
                            marker=dict(symbol=symbol_marker, size=14, color=color),
                            text=[label],
                            textposition="top center" if y_factor > 1 else "bottom center",
                            name=label,
                            showlegend=False,
                        ),
                        row=1, col=1
                    )

    # ========== 副图 ==========
    current_row = 2
    for indicator in show_indicators:
        if indicator == "volume":
            # 成交量柱，高亮异常量
            colors = []
            if "volume" in df.columns:
                avg_vol = df["volume"].tail(20).mean()
                for vol in df["volume"]:
                    if vol > avg_vol * SIGNAL_CONFIG["volume_breakout_multiplier"]:
                        colors.append("rgba(239,83,80,0.8)")  # 红 = 放量
                    elif vol < avg_vol * SIGNAL_CONFIG["volume_shrink_multiplier"]:
                        colors.append("rgba(38,166,154,0.6)")  # 绿 = 缩量
                    else:
                        colors.append("rgba(100,100,100,0.4)")
            else:
                colors = "rgba(100,100,100,0.4)"

            fig.add_trace(
                go.Bar(
                    x=df["date"], y=df.get("volume", [0]),
                    name="成交量", marker_color=colors,
                    showlegend=False,
                ),
                row=current_row, col=1
            )

        elif indicator == "macd":
            # MACD 柱 + DIF/DEA 线
            if "dif" in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df["date"], y=df["dif"],
                        mode="lines", name="DIF",
                        line=dict(color="#FF6B6B", width=1),
                    ),
                    row=current_row, col=1
                )
            if "dea" in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df["date"], y=df["dea"],
                        mode="lines", name="DEA",
                        line=dict(color="#42A5F5", width=1),
                    ),
                    row=current_row, col=1
                )
            if "macd" in df.columns:
                macd_colors = ["#ef5350" if v >= 0 else "#26a69a" for v in df["macd"].fillna(0)]
                fig.add_trace(
                    go.Bar(
                        x=df["date"], y=df["macd"],
                        name="MACD柱", marker_color=macd_colors,
                        showlegend=False,
                    ),
                    row=current_row, col=1
                )

        elif indicator == "kdj":
            if "k" in df.columns:
                fig.add_trace(
                    go.Scatter(x=df["date"], y=df["k"], mode="lines", name="K",
                               line=dict(color="#FF6B6B", width=1)),
                    row=current_row, col=1
                )
            if "d" in df.columns:
                fig.add_trace(
                    go.Scatter(x=df["date"], y=df["d"], mode="lines", name="D",
                               line=dict(color="#42A5F5", width=1)),
                    row=current_row, col=1
                )
            if "j" in df.columns:
                fig.add_trace(
                    go.Scatter(x=df["date"], y=df["j"], mode="lines", name="J",
                               line=dict(color="#FFA726", width=1)),
                    row=current_row, col=1
                )

        elif indicator == "rsi":
            for rsi_name, color in [("rsi6", "#FF6B6B"), ("rsi12", "#42A5F5"), ("rsi24", "#FFA726")]:
                if rsi_name in df.columns:
                    fig.add_trace(
                        go.Scatter(x=df["date"], y=df[rsi_name], mode="lines",
                                   name=rsi_name.upper(),
                                   line=dict(color=color, width=1)),
                        row=current_row, col=1
                    )
            # 超买超卖线
            fig.add_hline(y=70, line_dash="dash", line_color="gray", row=current_row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="gray", row=current_row, col=1)

        current_row += 1

    # ========== 布局 ==========
    fig.update_layout(
        title=f"股票 {symbol} K线图",
        xaxis_rangeslider_visible=False,
        height=400 + 200 * total_rows,
        hovermode="x unified",
        template="plotly_white",
        margin=dict(l=10, r=10, t=50, b=10),
    )

    # 隐藏X轴标题
    for i in range(1, total_rows + 1):
        fig.update_xaxes(title_text="", row=i, col=1)

    fig.update_yaxes(title_text="价格", row=1, col=1)

    return fig


def plot_multi_stock_overlay(symbols: list[str], days: int = 60, normalize: bool = True) -> go.Figure:
    """
    多只股票收盘价叠加对比图
    """
    fig = go.Figure()

    for symbol in symbols:
        df = get_stock_daily(symbol)
        if df.empty:
            continue
        df = df.sort_values("date").tail(days).reset_index(drop=True)
        df["date"] = pd.to_datetime(df["date"])

        if normalize:
            y = df["close"] / df["close"].iloc[0] * 100
            y_label = "归一化价格 (基点100)"
        else:
            y = df["close"]
            y_label = "收盘价"

        fig.add_trace(go.Scatter(
            x=df["date"], y=y, mode="lines",
            name=f"{symbol}",
        ))

    fig.update_layout(
        title="持仓股票走势对比",
        xaxis_title="日期",
        yaxis_title=y_label,
        hovermode="x unified",
        template="plotly_white",
        height=500,
    )

    return fig