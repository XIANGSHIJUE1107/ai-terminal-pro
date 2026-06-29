# -*- coding: utf-8 -*-
"""
资金流向可视化模块（Plotly）
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..data.database import get_sector_flow


def plot_sector_flow_bar(top_n: int = 15) -> go.Figure:
    """
    行业板块资金流向柱状图（最新日）
    """
    df = get_sector_flow()
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="无板块资金流数据", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False)
        return fig

    # 取最新日期
    latest_date = df["date"].max()
    latest_df = df[df["date"] == latest_date].head(top_n)

    # 正负颜色
    colors = ["#ef5350" if v >= 0 else "#26a69a" for v in latest_df["main_net_inflow"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=latest_df["main_net_inflow"].values,
        y=latest_df["sector_name"].values,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.2f}亿" if abs(v) < 100 else f"{v/1e8:.2f}亿" for v in latest_df["main_net_inflow"]],
        textposition="outside",
        name="主力净流入",
    ))

    fig.update_layout(
        title=f"行业板块资金流向 ({latest_date})",
        xaxis_title="主力净流入 (亿元)",
        yaxis=dict(autorange="reversed"),
        height=500,
        template="plotly_white",
        margin=dict(l=10, r=10, t=50, b=10),
    )

    return fig


def plot_sector_flow_timeline(sector_names: list[str], days: int = 20) -> go.Figure:
    """
    特定行业板块资金流向时序图
    """
    df = get_sector_flow()
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="无数据", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False)
        return fig

    # 筛选板块并排序
    df = df[df["sector_name"].isin(sector_names)]
    df = df.sort_values("date").groupby("sector_name").tail(days)

    fig = go.Figure()
    for name in sector_names:
        sector_df = df[df["sector_name"] == name]
        if not sector_df.empty:
            fig.add_trace(go.Scatter(
                x=sector_df["date"], y=sector_df["main_net_inflow"],
                mode="lines+markers", name=name,
            ))

    fig.update_layout(
        title="板块资金流向趋势",
        xaxis_title="日期",
        yaxis_title="主力净流入 (亿元)",
        hovermode="x unified",
        template="plotly_white",
        height=400,
    )

    return fig


def plot_sector_change_pct(top_n: int = 15) -> go.Figure:
    """行业板块涨跌幅柱状图"""
    df = get_sector_flow()
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="无数据", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False)
        return fig

    latest_date = df["date"].max()
    latest_df = df[df["date"] == latest_date].sort_values("change_pct", ascending=True).tail(top_n)

    colors = ["#ef5350" if v >= 0 else "#26a69a" for v in latest_df["change_pct"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=latest_df["change_pct"].values,
        y=latest_df["sector_name"].values,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.2f}%" for v in latest_df["change_pct"]],
        textposition="outside",
        name="涨跌幅",
    ))

    fig.update_layout(
        title=f"行业板块涨跌幅 ({latest_date})",
        xaxis_title="涨跌幅 (%)",
        yaxis=dict(autorange="reversed"),
        height=500,
        template="plotly_white",
    )

    return fig