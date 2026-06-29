# -*- coding: utf-8 -*-
"""
Streamlit 可视化看板
多页面应用：持仓总览、指数对比、板块资金流向、新闻流、预测与验证、技术指标详情
"""

import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from stock_platform.config import PORTFOLIO, INDEX_CODES
from stock_platform.data.database import (
    init_db, get_stock_daily, get_index_daily,
    get_predictions, get_verify_stats, get_latest_news,
    get_tech_indicator,
)
from stock_platform.viz.kline_chart import plot_kline_with_signals, plot_multi_stock_overlay
from stock_platform.viz.flow_chart import (
    plot_sector_flow_bar, plot_sector_flow_timeline, plot_sector_change_pct,
)
from stock_platform.prediction.verify import compute_win_rate

# ============ 页面配置 ============
st.set_page_config(
    page_title="股票分析平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化数据库
init_db()

# ============ 侧边栏 ============
st.sidebar.title("📊 股票分析平台")
st.sidebar.markdown("---")

# 标的筛选
symbol_options = [f"{name}({code})" for name, code in PORTFOLIO.items()]
selected_stocks = st.sidebar.multiselect("选择持仓股票", symbol_options, default=symbol_options[:3])

# 日期范围
today = datetime.now()
date_range = st.sidebar.date_input(
    "选择日期范围",
    value=(today - timedelta(days=90), today),
)

# 页面选择
page = st.sidebar.radio(
    "导航",
    ["持仓总览", "指数对比", "板块资金流向", "新闻流", "预测与验证", "技术指标详情"],
)

# ============ 持仓总览 ============
if page == "持仓总览":
    st.title("持仓总览")

    tabs = st.tabs([s for s in selected_stocks] if selected_stocks else ["无数据"])

    for i, stock_label in enumerate(selected_stocks):
        with tabs[i]:
            code = stock_label.split("(")[-1].rstrip(")")

            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader(f"{stock_label} K线图")
                show_indicators = st.multiselect(
                    "副图指标", ["volume", "macd", "kdj", "rsi"],
                    default=["volume", "macd"], key=f"ind_{code}"
                )
                days = st.slider("显示天数", 30, 365, 120, key=f"days_{code}")

                try:
                    fig = plot_kline_with_signals(code, days=days, show_indicators=show_indicators)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"加载K线图失败: {e}")

            with col2:
                st.subheader("最新预测")
                preds = get_predictions(symbol=code, is_valid=1)
                if not preds.empty:
                    latest_preds = preds.head(3)
                    for _, pred in latest_preds.iterrows():
                        direction_icon = "🟢" if pred["direction"] == "up" else "🔴"
                        st.metric(
                            label=f"{pred['horizon']}日预测 ({pred['pred_date']})",
                            value=f"{direction_icon} {pred['direction']}",
                            delta=f"目标价: {pred['target_price']:.2f} | 概率: {pred['probability']:.1%}",
                        )
                else:
                    st.info("暂无预测数据")

                st.markdown("---")
                st.subheader("最近信号")
                from stock_platform.data.database import get_signals
                signals = get_signals(symbol=code, start=(today - timedelta(days=30)).strftime("%Y-%m-%d"))
                if not signals.empty:
                    for _, sig in signals.tail(10).iterrows():
                        st.caption(f"{sig['date']} | {sig['signal_type']}")
                        st.caption(f"  → {sig['detail']}")
                else:
                    st.info("最近30天无信号")

# ============ 指数对比 ============
elif page == "指数对比":
    st.title("指数对比")

    # 选择要对比的标的
    all_codes = list(PORTFOLIO.values())
    compare_symbols = st.multiselect(
        "选择对比标的",
        [f"{n}({c})" for n, c in PORTFOLIO.items()],
        default=[f"{n}({c})" for n, c in list(PORTFOLIO.items())[:3]],
    )
    compare_codes = [s.split("(")[-1].rstrip(")") for s in compare_symbols]

    normalize = st.checkbox("归一化显示 (基点100)", value=True)

    if compare_codes:
        try:
            fig = plot_multi_stock_overlay(compare_codes, days=120, normalize=normalize)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"加载对比图失败: {e}")

    st.markdown("---")
    st.subheader("大盘指数")
    index_options = st.multiselect(
        "选择大盘指数",
        [f"{n}({c})" for c, n in INDEX_CODES.items()],
        default=[f"{n}({c})" for c, n in INDEX_CODES.items()],
    )

    if index_options:
        try:
            import plotly.graph_objects as go
            fig = go.Figure()
            for idx_label in index_options:
                code = idx_label.split("(")[-1].rstrip(")")
                name = INDEX_CODES.get(code, code)
                idx_df = get_index_daily(code)
                if not idx_df.empty:
                    idx_df = idx_df.sort_values("date").tail(120)
                    idx_df["date"] = pd.to_datetime(idx_df["date"])
                    if normalize:
                        y = idx_df["close"] / idx_df["close"].iloc[0] * 100
                    else:
                        y = idx_df["close"]
                    fig.add_trace(go.Scatter(x=idx_df["date"], y=y, mode="lines", name=name))

            fig.update_layout(
                title="大盘指数走势" + (" (归一化)" if normalize else ""),
                hovermode="x unified",
                template="plotly_white",
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"加载指数失败: {e}")

# ============ 板块资金流向 ============
elif page == "板块资金流向":
    st.title("板块资金流向")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("主力净流入排名")
        try:
            fig = plot_sector_flow_bar(top_n=15)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"加载失败: {e}")

    with col2:
        st.subheader("板块涨跌幅排名")
        try:
            fig = plot_sector_change_pct(top_n=15)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"加载失败: {e}")

# ============ 新闻流 ============
elif page == "新闻流":
    st.title("财联社实时电报")

    news_df = get_latest_news(limit=50)
    if not news_df.empty:
        for _, news in news_df.iterrows():
            with st.expander(f"{news['ctime'][:19] if len(str(news['ctime'])) > 10 else news['ctime']}"):
                st.write(news["content"])
    else:
        st.info("暂无新闻数据，请先运行数据抓取")

# ============ 预测与验证 ============
elif page == "预测与验证":
    st.title("预测与验证")

    # 胜率统计
    st.subheader("胜率统计")
    try:
        stats = compute_win_rate()
        if not stats.empty:
            st.dataframe(
                stats[["symbol", "horizon", "total", "correct", "incorrect", "invalid", "win_rate"]],
                use_container_width=True,
                column_config={
                    "symbol": "标的",
                    "horizon": "预测周期(日)",
                    "total": "总预测数",
                    "correct": "正确",
                    "incorrect": "错误",
                    "invalid": "失效",
                    "win_rate": st.column_config.NumberColumn("胜率(%)", format="%.1f%%"),
                },
            )
        else:
            st.info("暂无验证统计数据")

        # 胜率图表
        if not stats.empty:
            import plotly.express as px
            fig_bar = px.bar(
                stats, x="symbol", y="win_rate", color="horizon",
                barmode="group", title="各标的各周期胜率",
                labels={"symbol": "标的", "win_rate": "胜率(%)", "horizon": "预测周期"},
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        st.error(f"加载胜率统计失败: {e}")

    # 预测历史
    st.markdown("---")
    st.subheader("预测历史")

    stock_for_pred = st.selectbox(
        "选择标的查看预测历史",
        [f"{n}({c})" for n, c in PORTFOLIO.items()],
    )
    if stock_for_pred:
        code = stock_for_pred.split("(")[-1].rstrip(")")
        preds = get_predictions(symbol=code)
        if not preds.empty:
            # 关联验证结果
            from stock_platform.data.database import get_connection
            conn = get_connection()
            result_df = pd.read_sql("""
                SELECT p.*, v.result as verify_result, v.profit_pct, v.verify_date
                FROM prediction p
                LEFT JOIN prediction_verify v ON p.id = v.pred_id
                WHERE p.symbol = ?
                ORDER BY p.pred_date DESC
            """, conn, params=(code,))
            conn.close()

            st.dataframe(
                result_df[["pred_date", "horizon", "direction", "probability",
                           "target_price", "verify_result", "profit_pct"]].head(50),
                use_container_width=True,
                column_config={
                    "pred_date": "预测日期",
                    "horizon": "周期",
                    "direction": "预测方向",
                    "probability": st.column_config.NumberColumn("概率", format="%.1f%%"),
                    "target_price": st.column_config.NumberColumn("目标价", format="%.2f"),
                    "verify_result": "验证结果",
                    "profit_pct": st.column_config.NumberColumn("实际收益", format="%.2f%%"),
                },
            )
        else:
            st.info("暂无预测记录")

# ============ 技术指标详情 ============
elif page == "技术指标详情":
    st.title("技术指标详情")

    stock_for_tech = st.selectbox(
        "选择标的",
        [f"{n}({c})" for n, c in PORTFOLIO.items()],
        key="tech_stock"
    )

    if stock_for_tech:
        code = stock_for_tech.split("(")[-1].rstrip(")")
        tech_df = get_tech_indicator(code)

        if not tech_df.empty:
            tech_df["date"] = pd.to_datetime(tech_df["date"])
            recent_tech = tech_df.tail(20)

            st.subheader("最近20日技术指标")

            # MA 数据
            st.markdown("**移动平均线 (MA)**")
            st.dataframe(
                recent_tech[["date", "ma5", "ma10", "ma20", "ma60", "ma120"]].tail(10),
                use_container_width=True,
                column_config={
                    "date": "日期",
                    "ma5": st.column_config.NumberColumn("MA5", format="%.2f"),
                    "ma10": st.column_config.NumberColumn("MA10", format="%.2f"),
                    "ma20": st.column_config.NumberColumn("MA20", format="%.2f"),
                    "ma60": st.column_config.NumberColumn("MA60", format="%.2f"),
                    "ma120": st.column_config.NumberColumn("MA120", format="%.2f"),
                },
            )

            # MACD 数据
            st.markdown("**MACD**")
            st.dataframe(
                recent_tech[["date", "dif", "dea", "macd"]].tail(10),
                use_container_width=True,
            )

            # KDJ 数据
            st.markdown("**KDJ**")
            st.dataframe(
                recent_tech[["date", "k", "d", "j"]].tail(10),
                use_container_width=True,
                column_config={
                    "k": st.column_config.NumberColumn("K", format="%.2f"),
                    "d": st.column_config.NumberColumn("D", format="%.2f"),
                    "j": st.column_config.NumberColumn("J", format="%.2f"),
                },
            )

            # RSI 数据
            st.markdown("**RSI**")
            st.dataframe(
                recent_tech[["date", "rsi6", "rsi12", "rsi24"]].tail(10),
                use_container_width=True,
                column_config={
                    "rsi6": st.column_config.NumberColumn("RSI6", format="%.2f"),
                    "rsi12": st.column_config.NumberColumn("RSI12", format="%.2f"),
                    "rsi24": st.column_config.NumberColumn("RSI24", format="%.2f"),
                },
            )

            # BOLL 数据
            st.markdown("**布林带 (BOLL)**")
            st.dataframe(
                recent_tech[["date", "boll_upper", "boll_mid", "boll_lower"]].tail(10),
                use_container_width=True,
                column_config={
                    "boll_upper": st.column_config.NumberColumn("上轨", format="%.2f"),
                    "boll_mid": st.column_config.NumberColumn("中轨", format="%.2f"),
                    "boll_lower": st.column_config.NumberColumn("下轨", format="%.2f"),
                },
            )
        else:
            st.info("暂无技术指标数据，请先运行指标计算")


# ============ 页脚 ============
st.sidebar.markdown("---")
st.sidebar.caption(f"数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")