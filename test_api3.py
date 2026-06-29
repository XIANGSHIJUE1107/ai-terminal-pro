# -*- coding: utf-8 -*-
"""Test push2 stock/get API for sectors and more"""
import urllib.request, json, ssl

ssl_ctx = ssl.create_default_context()
h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": "https://quote.eastmoney.com/"}

# Test push2 stock/get for sector boards
tests = [
    ("1.600487", "个股(亨通光电)"),
    ("0.002475", "个股(立讯精密)"),
    ("90.BK0477", "板块(通信设备)"),
    ("90.BK0729", "板块(消费电子)"),
    ("90.BK0473", "板块(激光设备)"),
    ("90.BK0480", "板块(贵金属)"),
    ("90.BK0481", "板块(汽车零部件)"),
]

for secid, label in tests:
    url = ("https://push2.eastmoney.com/api/qt/stock/get?"
           "secid=" + secid + "&fields=f43,f44,f45,f46,f47,f48,f49,f50,f57,f58,f59,f60,f161,f162,f163,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f174,f175,f176,f177")
    try:
        req = urllib.request.Request(url, headers=h)
        r = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
        raw = json.loads(r.read().decode("utf-8"))
        data = raw.get("data", {})
        if data:
            print(label + ": OK - price=" + str(data.get("f43")) + " code=" + str(data.get("f57")) + " name=" + str(data.get("f58")))
        else:
            print(label + ": NO DATA - rc=" + str(raw.get("rc")) + " rt=" + str(raw.get("rt")))
    except Exception as e:
        print(label + ": FAIL -", str(e)[:80])

# Also test push2his for historical data
print("\n=== push2his ===")
url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.600487&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=5"
try:
    req = urllib.request.Request(url, headers={"User-Agent": h["User-Agent"], "Referer": "https://quote.eastmoney.com/"})
    r = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
    raw = json.loads(r.read().decode("utf-8"))
    klines = raw.get("data", {}).get("klines", []) or []
    print("push2his kline: OK", len(klines), "items")
    if klines: print(" ", klines[0])
except Exception as e:
    print("push2his kline: FAIL -", str(e)[:80])

# Test push2his for sector board
url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.BK0477&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=5"
try:
    req = urllib.request.Request(url, headers={"User-Agent": h["User-Agent"], "Referer": "https://quote.eastmoney.com/"})
    r = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
    raw = json.loads(r.read().decode("utf-8"))
    klines = raw.get("data", {}).get("klines", []) or []
    print("push2his sector: OK", len(klines), "items")
    if klines: print(" ", klines[0])
except Exception as e:
    print("push2his sector: FAIL -", str(e)[:80])

# Test fund flow for sector
url = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?secid=90.BK0477&fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&lmt=5"
try:
    req = urllib.request.Request(url, headers={"User-Agent": h["User-Agent"], "Referer": "https://data.eastmoney.com/"})
    r = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
    raw = json.loads(r.read().decode("utf-8"))
    klines = raw.get("data", {}).get("klines", []) or []
    print("fundflow sector: OK", len(klines), "items")
    if klines: print(" ", klines[0])
except Exception as e:
    print("fundflow sector: FAIL -", str(e)[:80])