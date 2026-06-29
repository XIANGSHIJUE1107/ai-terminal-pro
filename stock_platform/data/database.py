# -*- coding: utf-8 -*-
"""
数据库连接、建表、CRUD 操作
"""

import os
import sqlite3
from datetime import datetime

import pandas as pd

from ..config import DB_PATH


def _db_path() -> str:
    """从 SQLAlchemy 格式的 DB_PATH 提取实际文件路径"""
    return DB_PATH.replace("sqlite:///", "")


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库，创建所有表"""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS stock_daily (
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            amount REAL,
            PRIMARY KEY (date, symbol)
        );

        CREATE TABLE IF NOT EXISTS index_daily (
            date TEXT NOT NULL,
            code TEXT NOT NULL,
            name TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            amount REAL,
            PRIMARY KEY (date, code)
        );

        CREATE TABLE IF NOT EXISTS sector_fund_flow (
            date TEXT NOT NULL,
            sector_name TEXT NOT NULL,
            main_net_inflow REAL,
            super_large_net REAL,
            large_net REAL,
            mid_net REAL,
            small_net REAL,
            change_pct REAL,
            PRIMARY KEY (date, sector_name)
        );

        CREATE TABLE IF NOT EXISTS tech_indicator (
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            ma5 REAL,
            ma10 REAL,
            ma20 REAL,
            ma60 REAL,
            ma120 REAL,
            dif REAL,
            dea REAL,
            macd REAL,
            k REAL,
            d REAL,
            j REAL,
            rsi6 REAL,
            rsi12 REAL,
            rsi24 REAL,
            boll_upper REAL,
            boll_mid REAL,
            boll_lower REAL,
            PRIMARY KEY (date, symbol)
        );

        CREATE TABLE IF NOT EXISTS signal_event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            detail TEXT
        );

        CREATE TABLE IF NOT EXISTS prediction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pred_date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            horizon INTEGER NOT NULL,
            direction TEXT,
            probability REAL,
            target_price REAL,
            invalid_condition TEXT,
            is_valid INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS prediction_verify (
            pred_id INTEGER NOT NULL,
            actual_close REAL,
            result TEXT,
            dev_reason TEXT,
            profit_pct REAL,
            verify_date TEXT,
            FOREIGN KEY (pred_id) REFERENCES prediction(id)
        );

        CREATE TABLE IF NOT EXISTS cls_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetch_time TEXT NOT NULL,
            content TEXT,
            ctime TEXT
        );
    """)

    conn.commit()
    conn.close()
    print(f"[DB] 数据库初始化完成: {os.path.abspath(_db_path())}")


# ============ stock_daily CRUD ============

def insert_stock_daily(df: pd.DataFrame):
    """插入或替换股票日线数据"""
    conn = get_connection()
    if "symbol" in df.columns and "date" in df.columns:
        symbols = df["symbol"].unique()
        for sym in symbols:
            dates = df[df["symbol"] == sym]["date"].tolist()
            if dates:
                conn.execute(
                    f"DELETE FROM stock_daily WHERE symbol = ? AND date IN ({','.join(['?']*len(dates))})",
                    [sym] + dates
                )
    df.to_sql("stock_daily", conn, if_exists="append", index=False,
              method="multi", chunksize=500)
    conn.commit()
    conn.close()


def get_stock_daily(symbol: str, start: str = None, end: str = None) -> pd.DataFrame:
    """查询单只股票日线数据"""
    conn = get_connection()
    sql = "SELECT * FROM stock_daily WHERE symbol = ?"
    params = [symbol]
    if start:
        sql += " AND date >= ?"
        params.append(start)
    if end:
        sql += " AND date <= ?"
        params.append(end)
    sql += " ORDER BY date ASC"
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


def get_latest_date(symbol: str) -> str | None:
    """获取某股票最新数据日期"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT MAX(date) FROM stock_daily WHERE symbol = ?", (symbol,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


# ============ index_daily CRUD ============

def insert_index_daily(df: pd.DataFrame):
    conn = get_connection()
    # 先删除已有数据避免主键冲突
    if "code" in df.columns and "date" in df.columns:
        codes = df["code"].unique()
        for code in codes:
            dates = df[df["code"] == code]["date"].tolist()
            if dates:
                conn.execute(
                    f"DELETE FROM index_daily WHERE code = ? AND date IN ({','.join(['?']*len(dates))})",
                    [code] + dates
                )
    df.to_sql("index_daily", conn, if_exists="append", index=False,
              method="multi", chunksize=500)
    conn.commit()
    conn.close()


def get_index_daily(code: str, start: str = None, end: str = None) -> pd.DataFrame:
    conn = get_connection()
    sql = "SELECT * FROM index_daily WHERE code = ?"
    params = [code]
    if start:
        sql += " AND date >= ?"
        params.append(start)
    if end:
        sql += " AND date <= ?"
        params.append(end)
    sql += " ORDER BY date ASC"
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


# ============ tech_indicator CRUD ============

def insert_tech_indicator(df: pd.DataFrame):
    conn = get_connection()
    if "symbol" in df.columns and "date" in df.columns:
        symbols = df["symbol"].unique()
        for sym in symbols:
            dates = df[df["symbol"] == sym]["date"].tolist()
            if dates:
                conn.execute(
                    f"DELETE FROM tech_indicator WHERE symbol = ? AND date IN ({','.join(['?']*len(dates))})",
                    [sym] + dates
                )
    df.to_sql("tech_indicator", conn, if_exists="append", index=False,
              method="multi", chunksize=500)
    conn.commit()
    conn.close()


def get_tech_indicator(symbol: str, start: str = None, end: str = None) -> pd.DataFrame:
    conn = get_connection()
    sql = "SELECT * FROM tech_indicator WHERE symbol = ?"
    params = [symbol]
    if start:
        sql += " AND date >= ?"
        params.append(start)
    if end:
        sql += " AND date <= ?"
        params.append(end)
    sql += " ORDER BY date ASC"
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


# ============ signal_event CRUD ============

def insert_signals(records: list[dict]):
    """批量插入信号"""
    if not records:
        return
    conn = get_connection()
    cur = conn.cursor()
    for r in records:
        cur.execute(
            "INSERT INTO signal_event (date, symbol, signal_type, detail) VALUES (?, ?, ?, ?)",
            (r["date"], r["symbol"], r["signal_type"], r["detail"])
        )
    conn.commit()
    conn.close()


def get_signals(symbol: str = None, start: str = None, end: str = None) -> pd.DataFrame:
    conn = get_connection()
    sql = "SELECT * FROM signal_event WHERE 1=1"
    params = []
    if symbol:
        sql += " AND symbol = ?"
        params.append(symbol)
    if start:
        sql += " AND date >= ?"
        params.append(start)
    if end:
        sql += " AND date <= ?"
        params.append(end)
    sql += " ORDER BY date ASC"
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


# ============ prediction CRUD ============

def insert_predictions(records: list[dict]):
    if not records:
        return
    conn = get_connection()
    cur = conn.cursor()
    for r in records:
        cur.execute(
            """INSERT INTO prediction (pred_date, symbol, horizon, direction, probability, target_price, invalid_condition, is_valid)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
            (r["pred_date"], r["symbol"], r["horizon"],
             r["direction"], r["probability"], r["target_price"],
             r["invalid_condition"])
        )
    conn.commit()
    conn.close()


def get_predictions(symbol: str = None, is_valid: int = None) -> pd.DataFrame:
    conn = get_connection()
    sql = "SELECT * FROM prediction WHERE 1=1"
    params = []
    if symbol:
        sql += " AND symbol = ?"
        params.append(symbol)
    if is_valid is not None:
        sql += " AND is_valid = ?"
        params.append(is_valid)
    sql += " ORDER BY pred_date DESC"
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


def get_unverified_predictions() -> pd.DataFrame:
    """获取未被验证的过期预测"""
    conn = get_connection()
    sql = """
        SELECT p.* FROM prediction p
        LEFT JOIN prediction_verify v ON p.id = v.pred_id
        WHERE v.pred_id IS NULL
          AND p.is_valid = 1
          AND DATE(p.pred_date, '+' || p.horizon || ' days') <= DATE('now')
    """
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


# ============ prediction_verify CRUD ============

def insert_verify_records(records: list[dict]):
    if not records:
        return
    conn = get_connection()
    cur = conn.cursor()
    for r in records:
        cur.execute(
            """INSERT INTO prediction_verify (pred_id, actual_close, result, dev_reason, profit_pct, verify_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (r["pred_id"], r["actual_close"], r["result"],
             r.get("dev_reason", ""), r["profit_pct"], r["verify_date"])
        )
    conn.commit()
    conn.close()


def get_verify_stats() -> pd.DataFrame:
    """获取验证统计"""
    conn = get_connection()
    sql = """
        SELECT p.symbol, p.horizon,
               COUNT(*) AS total,
               SUM(CASE WHEN v.result = 'correct' THEN 1 ELSE 0 END) AS correct,
               SUM(CASE WHEN v.result = 'incorrect' THEN 1 ELSE 0 END) AS incorrect,
               SUM(CASE WHEN v.result = 'invalid' THEN 1 ELSE 0 END) AS invalid,
               ROUND(
                   CAST(SUM(CASE WHEN v.result = 'correct' THEN 1 ELSE 0 END) AS FLOAT)
                   / NULLIF(SUM(CASE WHEN v.result IN ('correct','incorrect') THEN 1 ELSE 0 END), 0)
                   * 100, 2
               ) AS win_rate
        FROM prediction p
        JOIN prediction_verify v ON p.id = v.pred_id
        GROUP BY p.symbol, p.horizon
        ORDER BY p.symbol, p.horizon
    """
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


# ============ sector_fund_flow CRUD ============

def insert_sector_flow(df: pd.DataFrame):
    conn = get_connection()
    if "sector_name" in df.columns and "date" in df.columns:
        names = df["sector_name"].unique()
        for name in names:
            dates = df[df["sector_name"] == name]["date"].tolist()
            if dates:
                conn.execute(
                    f"DELETE FROM sector_fund_flow WHERE sector_name = ? AND date IN ({','.join(['?']*len(dates))})",
                    [name] + dates
                )
    df.to_sql("sector_fund_flow", conn, if_exists="append", index=False,
              method="multi", chunksize=500)
    conn.commit()
    conn.close()


def get_sector_flow(date: str = None) -> pd.DataFrame:
    conn = get_connection()
    if date:
        sql = "SELECT * FROM sector_fund_flow WHERE date = ? ORDER BY main_net_inflow DESC"
        df = pd.read_sql(sql, conn, params=(date,))
    else:
        sql = "SELECT * FROM sector_fund_flow ORDER BY date DESC, main_net_inflow DESC"
        df = pd.read_sql(sql, conn)
    conn.close()
    return df


# ============ cls_news CRUD ============

def insert_news(records: list[dict]):
    if not records:
        return
    conn = get_connection()
    cur = conn.cursor()
    for r in records:
        cur.execute(
            "INSERT OR IGNORE INTO cls_news (fetch_time, content, ctime) VALUES (?, ?, ?)",
            (r["fetch_time"], r["content"], r.get("ctime", ""))
        )
    conn.commit()
    conn.close()


def get_latest_news(limit: int = 100) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql(
        "SELECT * FROM cls_news ORDER BY ctime DESC LIMIT ?",
        conn, params=(limit,)
    )
    conn.close()
    return df