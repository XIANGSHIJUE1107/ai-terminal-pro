# -*- coding: utf-8 -*-
"""Extract local Excel snapshots into normalized JSON files.

The workbook layout is transposed: the first column stores field names and each
following column stores one stock or sector.  This script intentionally resolves
all files relative to the project directory so the project can be moved without
breaking the data refresh path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
STOCK_XLSX = BASE_DIR / "持仓股.xlsx"
SECTOR_XLSX = BASE_DIR / "行业资金量.xlsx"
STOCK_JSON = BASE_DIR / "stock_data.json"
SECTOR_JSON = BASE_DIR / "sector_data.json"

JINTUO_CODE = "603211.SH"
JINTUO_BASELINE = {
    "简称": "晋拓股份",
    "日期": 20260618,
    "时间": "11:53:35",
    "前收": 33.13,
    "今开": 33.79,
    "最高": 36.44,
    "最低": 33.01,
    "现价": 36.44,
    "成交量": 8769700,
    "成交额": 310570002,
    "涨跌": 3.31,
    "涨跌幅": 9.99,
    "振幅": 10.36,
    "5日涨跌幅": 0,
    "当日净流入率": 0,
    "5日净流入率": 0,
    "10日净流入率": 0,
    "当日净流入额": 0,
    "机构资金净流入": 0,
    "大户资金净流入": 0,
    "中户资金净流入": 0,
    "散户资金净流入": 0,
    "数据状态": "已加入持仓，等待下一次行情刷新",
}


def _clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass
    return value


def read_transposed_excel(path: Path) -> dict[str, dict]:
    df = pd.read_excel(path, sheet_name=0)
    if df.empty:
        return {}
    first_col = df.columns[0]
    result: dict[str, dict] = {}
    for col in df.columns[1:]:
        code = str(col).strip()
        if not code or code.lower().startswith("unnamed"):
            continue
        item = {}
        for _, row in df.iterrows():
            field = str(row[first_col]).strip()
            if not field or field.lower() == "nan":
                continue
            value = _clean_value(row[col])
            if value is not None:
                item[field] = value
        if item:
            result[code] = item
    return result


def ensure_jintuo(stocks: dict[str, dict]) -> None:
    if JINTUO_CODE not in stocks:
        stocks[JINTUO_CODE] = dict(JINTUO_BASELINE)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    if not STOCK_XLSX.exists():
        raise FileNotFoundError(f"Missing holdings workbook: {STOCK_XLSX}")
    if not SECTOR_XLSX.exists():
        raise FileNotFoundError(f"Missing sector workbook: {SECTOR_XLSX}")

    stocks = read_transposed_excel(STOCK_XLSX)
    ensure_jintuo(stocks)
    write_json(STOCK_JSON, stocks)

    sectors = read_transposed_excel(SECTOR_XLSX)
    write_json(SECTOR_JSON, sectors)

    print(f"Saved {STOCK_JSON.name}: {len(stocks)} stocks")
    print(f"Saved {SECTOR_JSON.name}: {len(sectors)} sectors")
    print(f"Jintuo present: {JINTUO_CODE in stocks}")


if __name__ == "__main__":
    main()
