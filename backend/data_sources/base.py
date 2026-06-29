# -*- coding: utf-8 -*-
"""数据源基础工具"""

from __future__ import annotations

import json
import socket
from datetime import datetime
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ========== TDX 服务器池 ==========
TDX_SERVERS = [
    ("119.97.185.59", 7709),
    ("124.70.133.119", 7709),
    ("116.205.183.150", 7709),
    ("112.74.214.194", 7709),
    ("120.55.193.148", 7709),
    ("47.92.127.106", 7709),
]

# ========== 通用 HTTP Session ==========
_session: requests.Session | None = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.trust_env = False
        retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        _session.mount("https://", adapter)
        _session.mount("http://", adapter)
        _session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
    return _session


# ========== 工具函数 ==========
def now_dt() -> datetime:
    return datetime.now()


def now_text() -> str:
    return now_dt().strftime("%Y-%m-%d %H:%M:%S")


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            text = value.replace(",", "").strip()
            if text.endswith("%"):
                text = text[:-1]
            if text in {"--", "-", "None", "nan", "null", "NULL"}:
                return default
            if text.endswith("亿"):
                return float(text[:-1]) * 1e8
            if text.endswith("万"):
                return float(text[:-1]) * 1e4
            return float(text)
        return float(value)
    except Exception:
        return default


def with_prefix(symbol: str) -> str:
    symbol = str(symbol).strip()
    if symbol.startswith(("sh", "sz", "bj")):
        return symbol
    if symbol.endswith(".SH"):
        return "sh" + symbol[:6]
    if symbol.endswith(".SZ"):
        return "sz" + symbol[:6]
    if symbol.endswith(".BJ"):
        return "bj" + symbol[:6]
    if symbol.startswith(("5", "6", "9")):
        return "sh" + symbol[:6]
    if symbol.startswith(("0", "2", "3")):
        return "sz" + symbol[:6]
    if symbol.startswith(("8", "4")):
        return "bj" + symbol[:6]
    return "sz" + symbol[:6]


def code6(symbol: str) -> str:
    symbol = str(symbol).strip()
    if symbol.startswith(("sh", "sz", "bj")):
        return symbol[2:]
    if symbol.endswith((".SH", ".SZ", ".BJ")):
        return symbol[:6]
    return symbol[:6]


def market_code(symbol: str) -> int:
    """0=深圳, 1=上海, 2=北交所"""
    c = code6(symbol)
    if c.startswith(("5", "6", "9")):
        return 1
    if c.startswith(("8", "4")):
        return 2
    return 0


def safe_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def probe_tdx(ip: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False