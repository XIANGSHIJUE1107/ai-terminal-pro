# -*- coding: utf-8 -*-
"""Generate browser-readable data snapshots from normalized JSON files."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
STOCK_JSON = BASE_DIR / "stock_data.json"
SECTOR_JSON = BASE_DIR / "sector_data.json"
STOCK_JS = BASE_DIR / "stock_data.js"
SECTOR_JS = BASE_DIR / "sector_data.js"

STOCK_FIELDS = [
    "简称",
    "日期",
    "时间",
    "前收",
    "今开",
    "最高",
    "最低",
    "现价",
    "成交量",
    "成交额",
    "涨跌",
    "涨跌幅",
    "振幅",
    "5日涨跌幅",
    "当日净流入率",
    "5日净流入率",
    "10日净流入率",
    "当日净流入额",
    "机构资金净流入",
    "大户资金净流入",
    "中户资金净流入",
    "散户资金净流入",
    "数据状态",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def js_const(name: str, value) -> str:
    return f"const {name}={json.dumps(value, ensure_ascii=False, separators=(',', ':'))};\n"


def normalize_stocks(stocks: dict) -> dict:
    out = {}
    text_fields = {"简称", "日期", "时间", "数据状态"}
    for code, data in stocks.items():
        out[code] = {
            field: data.get(field, "" if field in text_fields else 0)
            for field in STOCK_FIELDS
        }
    return out


def normalize_sectors(sectors: dict) -> dict:
    out = {}
    for code, data in sectors.items():
        out[code] = {
            "n": data.get("简称", ""),
            "p": data.get("现价", 0),
            "c": data.get("涨跌幅", 0),
            "a": data.get("成交额", 0),
            "ni": data.get("当日净流入额", 0),
            "nr": data.get("当日净流入率", 0),
            "ii": data.get("机构资金净流入", 0),
            "date": data.get("日期", ""),
            "time": data.get("时间", ""),
            "src": "行业资金量.xlsx",
        }
    return out


def build_meta(stocks: dict, sectors: dict) -> dict:
    stock_dates = sorted({str(v.get("日期", "")) for v in stocks.values() if v.get("日期")})
    sector_dates = sorted({str(v.get("日期", "")) for v in sectors.values() if v.get("日期")})
    return {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sources": ["持仓股.xlsx", "行业资金量.xlsx"],
        "stockCount": len(stocks),
        "sectorCount": len(sectors),
        "stockDates": stock_dates,
        "sectorDates": sector_dates,
        "quality": {
            "jintuoIncluded": "603211.SH" in stocks,
            "sectorFields": ["简称", "现价", "涨跌幅", "成交额", "当日净流入额", "当日净流入率", "机构资金净流入"],
        },
    }


def main() -> None:
    stocks_raw = load_json(STOCK_JSON)
    sectors_raw = load_json(SECTOR_JSON)
    stocks = normalize_stocks(stocks_raw)
    sectors = normalize_sectors(sectors_raw)
    meta = build_meta(stocks_raw, sectors_raw)

    STOCK_JS.write_text(
        js_const("STOCK_DATA", stocks) + js_const("DATA_META", meta),
        encoding="utf-8",
    )
    SECTOR_JS.write_text(
        js_const("SECTOR_DATA", sectors) + js_const("DATA_META", meta),
        encoding="utf-8",
    )
    print(f"Generated {STOCK_JS.name} with {len(stocks)} stocks")
    print(f"Generated {SECTOR_JS.name} with {len(sectors)} sectors")


if __name__ == "__main__":
    main()
