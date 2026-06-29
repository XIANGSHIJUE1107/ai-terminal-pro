# -*- coding: utf-8 -*-
"""Test Eastmoney datacenter API with different report names"""
import urllib.request, json, ssl, urllib.parse

ssl_ctx = ssl.create_default_context()
h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": "https://data.eastmoney.com/"}

# Try different report name patterns for margin trading
code = "600487"
report_tests = [
    # 融资融券 variants
    ("RPTA_WEB_MARGIN_TRADING", "TRADE_DATE,RZYE,RZYL,RQYE,RQYL,RZRQYE", "margin1"),
    ("RPT_MARGIN_TRADING", "TRADE_DATE,RZYE,RZYL,RQYE,RQYL,RZRQYE", "margin2"),
    ("RPTA_MARGIN_TRADING", "TRADE_DATE,RZYE,RZYL,RQYE,RQYL,RZRQYE", "margin3"),
    ("RPT_DAILY_MARGIN", "TRADE_DATE,RZYE,RZYL,RQYE,RQYL,RZRQYE", "margin4"),
    # 大宗交易 variants
    ("RPTA_WEB_DZJY_DAILY", "TRADE_DATE,SECURITY_NAME,PRICE,PRICE_CHANGE_RATIO,TRADE_VOLUME,TRADE_AMOUNT", "block1"),
    ("RPT_BLOCK_TRADE", "TRADE_DATE,SECURITY_NAME,PRICE,PRICE_CHANGE_RATIO,TRADE_VOLUME,TRADE_AMOUNT", "block2"),
    # 股东户数 variants
    ("RPT_DMSK_HOLDER_NUM", "END_DATE,HOLDER_NUM,HOLDER_NUM_RATIO", "holder1"),
    ("RPT_HOLDER_NUM", "END_DATE,HOLDER_NUM,HOLDER_NUM_RATIO", "holder2"),
    ("RPTA_HOLDER_NUM", "END_DATE,HOLDER_NUM,HOLDER_NUM_RATIO", "holder3"),
    # 分红送转 variants
    ("RPT_FN_DIVIDEND", "NOTICE_DATE,EX_DIVIDEND_DATE,PLAN_EXPLAIN,BONUS_IT_RATIO", "div1"),
    ("RPT_DIVIDEND", "NOTICE_DATE,EX_DIVIDEND_DATE,PLAN_EXPLAIN,BONUS_IT_RATIO", "div2"),
    ("RPTA_DIVIDEND", "NOTICE_DATE,EX_DIVIDEND_DATE,PLAN_EXPLAIN,BONUS_IT_RATIO", "div3"),
]

for report, columns, label in report_tests:
    filter_val = '(SECURITY_CODE="' + code + '")'
    url = ("https://datacenter.eastmoney.com/securities/api/data/v1/get?"
           "reportName=" + report + "&columns=" + columns +
           "&filter=" + urllib.parse.quote(filter_val) +
           "&pageNumber=1&pageSize=3&sortTypes=-1&sortColumns=TRADE_DATE")
    try:
        req = urllib.request.Request(url, headers=h)
        r = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
        raw = json.loads(r.read().decode("utf-8"))
        success = raw.get("success", False)
        msg = raw.get("message", "")
        data = (raw.get("result") or {}).get("data") or []
        if success and data:
            print(label + ": OK " + str(len(data)) + " items")
            print("  " + json.dumps(data[0], ensure_ascii=False)[:200])
        else:
            print(label + ": " + str(msg)[:80])
    except Exception as e:
        print(label + ": " + str(e)[:100])

# Also try the push2 API with different URL
print("\n=== push2 测试 ===")
for url in [
    "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=3&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t2&fields=f12,f14,f2,f3,f62",
    "https://push2.eastmoney.com/api/qt/stock/get?secid=1.600487&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f161,f162,f163,f164,f165,f166,f167,f168,f169,f170,f171",
]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": h["User-Agent"], "Referer": "https://quote.eastmoney.com/"})
        r = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
        raw = json.loads(r.read().decode("utf-8"))
        print("push2:", url[:80], "->", json.dumps(raw, ensure_ascii=False)[:200])
    except Exception as e:
        print("push2:", url[:80], "FAIL:", str(e)[:80])