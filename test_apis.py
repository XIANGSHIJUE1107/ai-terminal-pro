# -*- coding: utf-8 -*-
"""测试各个API端点"""
import urllib.request, json, ssl, gzip

HEADERS_SINA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": "https://finance.sina.com.cn/"}
HEADERS_EM = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36", "Referer": "https://data.eastmoney.com/", "Accept": "*/*"}

def fetch(url, headers, timeout=10):
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        body = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        return body.decode("utf-8", errors="ignore")

# Test 1: 新浪行情 (known working)
print("=== 1. 新浪行情 ===")
try:
    text = fetch("https://hq.sinajs.cn/list=sh600487", HEADERS_SINA, 10)
    print("OK:", text[:200])
except Exception as e:
    print("FAIL:", e)

# Test 2: 东财datacenter 融资融券
print("\n=== 2. 东财datacenter 融资融券 ===")
try:
    url = "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPTA_WEB_MARGIN_TRADING&columns=TRADE_DATE,RZYE,RZYL,RQYE,RQYL,RZRQYE&filter=(SECURITY_CODE=%22600487%22)&pageNumber=1&pageSize=5&sortTypes=-1&sortColumns=TRADE_DATE"
    text = fetch(url, HEADERS_EM, 15)
    raw = json.loads(text)
    print("success:", raw.get("success"))
    data = raw.get("result", {}).get("data", []) if raw.get("result") else []
    print("items:", len(data))
    if data:
        print("first:", json.dumps(data[0], ensure_ascii=False))
except Exception as e:
    print("FAIL:", e)

# Test 3: 东财datacenter 大宗交易
print("\n=== 3. 东财datacenter 大宗交易 ===")
try:
    url = "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPTA_WEB_DZJY_DAILY&columns=TRADE_DATE,SECURITY_CODE,SECURITY_NAME,PRICE,PRICE_CHANGE_RATIO,TRADE_VOLUME,TRADE_AMOUNT,BUYER_NAME,SELLER_NAME&filter=(SECURITY_CODE=%22600487%22)&pageNumber=1&pageSize=5&sortTypes=-1&sortColumns=TRADE_DATE"
    text = fetch(url, HEADERS_EM, 15)
    raw = json.loads(text)
    print("success:", raw.get("success"))
    data = raw.get("result", {}).get("data", []) if raw.get("result") else []
    print("items:", len(data))
    if data:
        print("first:", json.dumps(data[0], ensure_ascii=False))
except Exception as e:
    print("FAIL:", e)

# Test 4: 东财datacenter 股东户数
print("\n=== 4. 东财datacenter 股东户数 ===")
try:
    url = "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_DMSK_HOLDER_NUM&columns=END_DATE,HOLDER_NUM,HOLDER_NUM_RATIO,TOTAL_SHARES,AVG_HOLD_NUM&filter=(SECURITY_CODE=%22600487%22)&pageNumber=1&pageSize=5&sortTypes=-1&sortColumns=END_DATE"
    text = fetch(url, HEADERS_EM, 15)
    raw = json.loads(text)
    print("success:", raw.get("success"))
    data = raw.get("result", {}).get("data", []) if raw.get("result") else []
    print("items:", len(data))
    if data:
        print("first:", json.dumps(data[0], ensure_ascii=False))
except Exception as e:
    print("FAIL:", e)

# Test 5: 东财datacenter 分红送转
print("\n=== 5. 东财datacenter 分红送转 ===")
try:
    url = "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_FN_DIVIDEND&columns=NOTICE_DATE,EX_DIVIDEND_DATE,PLAN_EXPLAIN,BONUS_IT_RATIO,TRANSFER_IT_RATIO,ADD_ALLOTMENT_RATIO,SECURITY_NAME_ABBR,DIVIDEND_PLAN_DATE&filter=(SECURITY_CODE=%22600487%22)&pageNumber=1&pageSize=5&sortTypes=-1&sortColumns=NOTICE_DATE"
    text = fetch(url, HEADERS_EM, 15)
    raw = json.loads(text)
    print("success:", raw.get("success"))
    data = raw.get("result", {}).get("data", []) if raw.get("result") else []
    print("items:", len(data))
    if data:
        print("first:", json.dumps(data[0], ensure_ascii=False))
except Exception as e:
    print("FAIL:", e)

# Test 6: 东财push2 板块资金流 (different approach)
print("\n=== 6. 东财push2 板块资金流 ===")
try:
    url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f62&fs=m:90+t2&fields=f12,f14,f2,f3,f62,f184"
    text = fetch(url, HEADERS_EM, 15)
    raw = json.loads(text)
    print("success:", "data" in raw)
    data = raw.get("data", {}).get("diff", []) if raw.get("data") else []
    print("items:", len(data))
except Exception as e:
    print("FAIL:", e)

# Test 7: 同花顺 板块资金流
print("\n=== 7. 同花顺 板块资金流 ===")
try:
    url = "https://q.10jqka.com.cn/gn/detail/field/199112/order/desc/page/1/ajax/1/code/"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://q.10jqka.com.cn/"}
    text = fetch(url, headers, 10)
    print("OK:", text[:500])
except Exception as e:
    print("FAIL:", e)

# Test 8: 新浪个股资金流
print("\n=== 8. 新浪个股资金流 ===")
try:
    url = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600487&scale=240&datalen=5"
    text = fetch(url, HEADERS_SINA, 10)
    print("OK:", text[:500])
except Exception as e:
    print("FAIL:", e)

# Test 9: 东财datacenter alternative format
print("\n=== 9. 东财datacenter alt format ===")
try:
    url = "https://datacenter.eastmoney.com/securities/api/data/get?type=RPTA_WEB_MARGIN_TRADING&sty=TRADE_DATE,RZYE&filter=(SECURITY_CODE=%22600487%22)&p=1&ps=5&sr=-1&st=TRADE_DATE"
    text = fetch(url, HEADERS_EM, 15)
    raw = json.loads(text)
    print("success:", raw.get("success"))
except Exception as e:
    print("FAIL:", e)

# Test 10: 东财web stock data
print("\n=== 10. 东财web stock data ===")
try:
    url = "https://quote.eastmoney.com/concept/sh600487.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    text = fetch(url, headers, 10)
    print("OK, len:", len(text))
except Exception as e:
    print("FAIL:", e)

# Test 11: 东财web API for sector
print("\n=== 11. 东财web API sector ===")
try:
    url = "https://data.eastmoney.com/bkzj/hy.html"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    text = fetch(url, headers, 10)
    print("OK, len:", len(text))
except Exception as e:
    print("FAIL:", e)

# Test 12: 新浪资金流 API
print("\n=== 12. 新浪资金流 API ===")
try:
    url = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600487&scale=5&datalen=10"
    text = fetch(url, HEADERS_SINA, 10)
    print("OK:", text[:300])
except Exception as e:
    print("FAIL:", e)

# Test 13: 新浪板块行情
print("\n=== 13. 新浪板块行情 ===")
try:
    url = "https://vip.stock.finance.sina.com.cn/q/go.php/vIndustryRank/kind/sshy/num/10/asc/0/field/avgprice"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
    text = fetch(url, headers, 10)
    print("OK:", text[:500])
except Exception as e:
    print("FAIL:", e)

print("\n=== DONE ===")