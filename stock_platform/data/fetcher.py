# -*- coding: utf-8 -*-
"""
数据抓取模块 —— 封装 AKShare 全部数据接口
"""

import os
import time
from datetime import datetime, timedelta

# 禁用系统代理，避免代理连接失败
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

# 强制 requests 不信任系统代理，并设置默认请求头
import requests
_original_session_init = requests.Session.__init__
def _patched_session_init(self, *args, **kwargs):
    _original_session_init(self, *args, **kwargs)
    self.trust_env = False
    self.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
requests.Session.__init__ = _patched_session_init

import akshare as ak
import pandas as pd

from .database import (
    get_latest_date, insert_stock_daily, insert_index_daily,
    insert_sector_flow, insert_news, get_stock_daily,
)
from ..config import (
    PORTFOLIO, INDEX_CODES, US_INDEX_CODES, KOSPI_CODE, START_DATE,
)

# ============================================================
#  重试工具
# ============================================================

def _retry_fetch(func, max_retries: int = 3, base_delay: float = 2.0):
    """带指数退避的重试包装器"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                wait = base_delay * (2 ** attempt)
                print(f"  [Retry] 第{attempt+1}次失败: {e}, {wait:.0f}秒后重试...")
                time.sleep(wait)
            else:
                raise e

# ============================================================
#  A 股个股日线
# ============================================================

def _to_tx_symbol(symbol: str) -> str:
    """将 AKShare symbol 转为腾讯格式: 600487 -> sh600487, 002475 -> sz002475"""
    if symbol.startswith("sh") or symbol.startswith("sz"):
        return symbol
    if symbol.startswith(("6", "9")):
        return f"sh{symbol}"
    return f"sz{symbol}"


def fetch_stock_daily(symbol: str, start_date: str = START_DATE, end_date: str = None) -> pd.DataFrame | None:
    """
    获取单只A股日K线（前复权）
    优先使用腾讯数据源（更稳定），东方财富为备选
    返回统一列名 DataFrame
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    df = None

    # Try Tencent API first (more network-friendly)
    tx_symbol = _to_tx_symbol(symbol)
    try:
        df = _retry_fetch(
            lambda: ak.stock_zh_a_hist_tx(
                symbol=tx_symbol,
                start_date=start_date,
                end_date=end_date,
            )
        )
    except Exception as e:
        print(f"[Fetcher] 腾讯源获取 {symbol} 失败: {e}")

    # Fallback: EastMoney API
    if df is None or df.empty:
        try:
            df = _retry_fetch(
                lambda: ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq",
                )
            )
        except Exception as e:
            print(f"[Fetcher] 东方财富源获取 {symbol} 失败: {e}")

    if df is None or df.empty:
        print(f"[Fetcher] {symbol} 所有数据源均无数据返回")
        return None

    # 统一列名
    col_map = {
        "日期": "date", "开盘": "open", "最高": "high",
        "最低": "low", "收盘": "close", "成交量": "volume", "成交额": "amount",
    }
    df.rename(columns=col_map, inplace=True)

    keep_cols = ["date", "open", "high", "low", "close", "volume", "amount"]
    df = df[[c for c in keep_cols if c in df.columns]]

    # 腾讯源没有 volume 列，用 amount/(high+low)/2 估算
    if "volume" not in df.columns and "amount" in df.columns:
        avg_price = (df["high"] + df["low"]) / 2
        df["volume"] = (df["amount"] / avg_price.replace(0, 1)).round(0)

    df["symbol"] = symbol
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df.drop_duplicates(subset=["date"], inplace=True)
    return df


def update_all_stock_daily():
    """更新所有持仓股历史日线（增量）"""
    for name, symbol in PORTFOLIO.items():
        latest = get_latest_date(symbol)
        if latest:
            latest_date = datetime.strptime(latest, "%Y-%m-%d")
            # 从上次日期后一天开始
            start = (latest_date + timedelta(days=1)).strftime("%Y%m%d")
            today = datetime.now().strftime("%Y%m%d")
            if start >= today:
                print(f"[Fetcher] {name}({symbol}) 已是最新，跳过")
                continue
        else:
            start = START_DATE

        print(f"[Fetcher] 更新 {name}({symbol}) 从 {start} ...")
        df = fetch_stock_daily(symbol, start_date=start)
        if df is not None and not df.empty:
            insert_stock_daily(df)
            print(f"[Fetcher] {name}({symbol}) 插入 {len(df)} 条")
        time.sleep(0.5)  # 请求间隔


def fetch_single_stock_daily(symbol: str, start_date: str = START_DATE) -> pd.DataFrame | None:
    """获取单只股票日线（返回DataFrame给其他模块使用）"""
    df = fetch_stock_daily(symbol, start_date=start_date)
    if df is not None:
        return df
    # 尝试从数据库读取
    return get_stock_daily(symbol, start=start_date)


# ============================================================
#  A 股大盘指数
# ============================================================

def fetch_index_daily(code: str, name: str = "") -> pd.DataFrame | None:
    """
    获取A股大盘指数日线
    code 示例: sh000001, sz399001, sz399006
    """
    try:
        df = ak.stock_zh_index_daily(symbol=code)
    except Exception as e:
        print(f"[Fetcher] 获取指数 {code} 失败: {e}")
        return None

    if df is None or df.empty:
        return None

    col_map = {
        "date": "date", "open": "open", "high": "high",
        "low": "low", "close": "close", "volume": "volume",
    }
    df.rename(columns=col_map, inplace=True)
    keep_cols = ["date", "open", "high", "low", "close", "volume"]
    df = df[[c for c in keep_cols if c in df.columns]]

    df["code"] = code
    df["name"] = name
    if "amount" not in df.columns:
        df["amount"] = 0
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df


def update_indices():
    """更新所有A股大盘指数"""
    for code, name in INDEX_CODES.items():
        print(f"[Fetcher] 更新指数 {name}({code}) ...")
        df = fetch_index_daily(code, name)
        if df is not None and not df.empty:
            # 移除旧数据再插入（简单处理）
            insert_index_daily(df)
            print(f"[Fetcher] {name} 插入 {len(df)} 条")
        time.sleep(0.5)

    print(f"[Fetcher] 更新指数 韩国KOSPI({KOSPI_CODE}) ...")
    df_kospi = fetch_kospi_daily()
    if df_kospi is not None and not df_kospi.empty:
        insert_index_daily(df_kospi)
        print(f"[Fetcher] 韩国KOSPI 插入 {len(df_kospi)} 条")


# ============================================================
#  美股三大指数
# ============================================================

def fetch_us_index_daily() -> dict[str, pd.DataFrame]:
    """获取美股三大指数"""
    results = {}
    for code, name in US_INDEX_CODES.items():
        try:
            df = ak.index_us_stock_sina(symbol=code)
            if df is not None and not df.empty:
                col_map = {
                    "date": "date", "open": "open", "high": "high",
                    "low": "low", "close": "close", "volume": "volume",
                }
                df.rename(columns=col_map, inplace=True)
                df["code"] = code
                df["name"] = name
                if "amount" not in df.columns:
                    df["amount"] = 0
                results[code] = df
            time.sleep(0.5)
        except Exception as e:
            print(f"[Fetcher] 获取美股指数 {code} 失败: {e}")
    return results


# ============================================================
#  韩国 KOSPI
# ============================================================

def fetch_kospi_daily() -> pd.DataFrame | None:
    """获取韩国 KOSPI 指数"""
    try:
        df = ak.index_global_hist_sina(symbol=KOSPI_CODE)
        if df is not None and not df.empty:
            col_map = {
                "date": "date", "open": "open", "high": "high",
                "low": "low", "close": "close", "volume": "volume",
            }
            df.rename(columns=col_map, inplace=True)
            df["code"] = KOSPI_CODE
            df["name"] = "韩国KOSPI"
            if "amount" not in df.columns:
                df["amount"] = 0
            return df
    except Exception as e:
        print(f"[Fetcher] 新浪全球指数获取KOSPI失败: {e}")

    try:
        spot = ak.index_global_spot_em()
        if spot is None or spot.empty:
            return None
        text_df = spot.astype(str)
        mask = text_df.apply(lambda s: s.str.contains("KS11|KOSPI|韩国", case=False, na=False)).any(axis=1)
        if not mask.any():
            return None
        row = spot.loc[mask].iloc[0]
        close = float(row.get("最新价", row.get("最新", row.get("今收", 0))) or 0)
        open_price = float(row.get("今开", close) or close)
        high = float(row.get("最高", close) or close)
        low = float(row.get("最低", close) or close)
        return pd.DataFrame([{
            "date": datetime.now().strftime("%Y-%m-%d"),
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": 0,
            "amount": 0,
            "code": KOSPI_CODE,
            "name": "韩国KOSPI",
        }])
    except Exception as e:
        print(f"[Fetcher] 东方财富全球指数获取KOSPI失败: {e}")
    return None


# ============================================================
#  行业板块资金流向
# ============================================================

def fetch_sector_flow() -> pd.DataFrame | None:
    """获取行业板块资金流向（东方财富）"""
    try:
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
    except Exception as e:
        print(f"[Fetcher] 获取板块资金流失败: {e}")
        return None

    if df is None or df.empty:
        return None

    # 统一列名
    rename_map = {
        "名称": "sector_name",
        "今日主力净流入-净额": "main_net_inflow",
        "今日超大单净流入-净额": "super_large_net",
        "今日大单净流入-净额": "large_net",
        "今日中单净流入-净额": "mid_net",
        "今日小单净流入-净额": "small_net",
        "今日涨跌幅": "change_pct",
    }
    df.rename(columns=rename_map, inplace=True)
    keep_cols = ["sector_name", "main_net_inflow", "super_large_net",
                  "large_net", "mid_net", "small_net", "change_pct"]
    df = df[[c for c in keep_cols if c in df.columns]]
    df["date"] = datetime.now().strftime("%Y-%m-%d")

    # 数值列转换
    for c in ["main_net_inflow", "super_large_net", "large_net", "mid_net", "small_net", "change_pct"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df.dropna(subset=["sector_name"], inplace=True)
    return df


def update_sector_flow():
    """获取并入库板块资金流向"""
    df = fetch_sector_flow()
    if df is not None and not df.empty:
        insert_sector_flow(df)
        print(f"[Fetcher] 板块资金流插入 {len(df)} 条")
    else:
        print("[Fetcher] 板块资金流无数据")


# ============================================================
#  财联社实时电报
# ============================================================

def fetch_cls_news() -> list[dict] | None:
    """获取财联社电报"""
    try:
        if hasattr(ak, "stock_info_global_cls"):
            df = ak.stock_info_global_cls(symbol="全部")
        else:
            df = ak.stock_telegraph_cls()
    except Exception as e:
        print(f"[Fetcher] 获取财联社电报失败: {e}")
        return None

    if df is None or df.empty:
        return None

    records = []
    fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for _, row in df.iterrows():
        title = str(row.get("标题", row.get("title", "")))
        content = str(row.get("内容", row.get("content", title)))
        ctime = str(row.get("发布时间", row.get("ctime", row.get("时间", ""))))
        records.append({
            "fetch_time": fetch_time,
            "content": content or title,
            "ctime": ctime,
        })
    return records


def update_cls_news():
    """获取并入库财联社电报"""
    records = fetch_cls_news()
    if records:
        insert_news(records)
        print(f"[Fetcher] 财联社电报插入 {len(records)} 条")
    else:
        print("[Fetcher] 财联社电报无数据")


# ============================================================
#  运行入口
# ============================================================

def run_daily_update():
    """每日收盘后全量更新"""
    print(f"\n{'='*50}")
    print(f"[Fetcher] 开始每日数据更新 {datetime.now()}")
    print(f"{'='*50}")
    update_all_stock_daily()
    update_indices()
    update_sector_flow()
    update_cls_news()
    print(f"[Fetcher] 每日数据更新完成\n")


def run_morning_snapshot():
    """早间快照（板块资金+新闻）"""
    print(f"[Fetcher] 早间快照 {datetime.now()}")
    update_sector_flow()
    update_cls_news()


def run_intraday():
    """盘中更新（新闻+短线行情）"""
    print(f"[Fetcher] 盘中更新 {datetime.now()}")
    update_cls_news()


if __name__ == "__main__":
    run_daily_update()
