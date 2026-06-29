# -*- coding: utf-8 -*-
import urllib.request, json, ssl, urllib.parse

ssl_ctx = ssl.create_default_context()
h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": "https://data.eastmoney.com/"}

# Test datacenter APIs
tests = [
    ("RPT_DMSK_HOLDER_NUM", "END_DATE,HOLDER_NUM,HOLDER_NUM_RATIO,TOTAL_SHARES,AVG_HOLD_NUM", "股东户数"),
    ("RPT_FN_DIVIDEND", "NOTICE_DATE,EX_DIVIDEND_DATE,PLAN_EXPLAIN,BONUS_IT_RATIO,TRANSFER_IT_RATIO,SECURITY_NAME_ABBR", "分红送转"),
    ("RPTA_WEB_MARGIN_TRADING", "TRADE_DATE,RZYE,RZYL,RQYE,RQYL,RZRQYE", "融资融券"),
    ("RPTA_WEB_DZJY_DAILY", "TRADE_DATE,SECURITY_NAME,PRICE,PRICE_CHANGE_RATIO,TRADE_VOLUME,TRADE_AMOUNT,BUYER_NAME,SELLER_NAME", "大宗交易"),
]

code = "600487"
for report, columns, label in tests:
    filter_val = '(SECURITY_CODE="' + code + '")'
    url = ("https://datacenter.eastmoney.com/securities/api/data/v1/get?"
           "reportName=" + report + "&columns=" + columns +
           "&filter=" + urllib.parse.quote(filter_val) +
           "&pageNumber=1&pageSize=5&sortTypes=-1&sortColumns=TRADE_DATE")
    try:
        req = urllib.request.Request(url, headers=h)
        r = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
        raw = json.loads(r.read().decode("utf-8"))
        success = raw.get("success", False)
        code_val = raw.get("code", -1)
        msg = raw.get("message", "")
        if raw.get("result") and raw["result"].get("data"):
            data = raw["result"]["data"]
            print(label + ": OK", len(data), "items")
            if data:
                print(" ", json.dumps(data[0], ensure_ascii=False)[:200])
        else:
            print(label + ": FAIL - success=" + str(success) + " code=" + str(code_val) + " msg=" + str(msg)[:100])
    except Exception as e:
        print(label + ": FAIL -", str(e)[:100])
    print()

# Also test push2 fund flow
print("=== 资金流 push2his ===")
try:
    url = ("https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?"
           "secid=1.600487&fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
           "&klt=101&lmt=5")
    req = urllib.request.Request(url, headers=h)
    r = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
    raw = json.loads(r.read().decode("utf-8"))
    klines = raw.get("data", {}).get("klines", []) or []
    print("资金流(日线): OK", len(klines), "items")
    if klines:
        print(" ", klines[0])
except Exception as e:
    print("资金流(日线): FAIL -", str(e)[:100])