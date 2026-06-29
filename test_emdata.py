# -*- coding: utf-8 -*-
"""测试东财emdatah5 API"""
import urllib.request, json, ssl, gzip

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36", "Referer": "https://data.eastmoney.com/", "Accept": "*/*"}

def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers=HEADERS)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        body = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        return body.decode("utf-8", errors="ignore")

# Test emdatah5 API
urls = [
    "https://emdatah5.eastmoney.com/dc/zjlx/block",
    "https://emdatah5.eastmoney.com/dc/zjlx/block?type=hy",
    "https://emdatah5.eastmoney.com/dc/zjlx/block?type=hy&page=1&size=10",
    "https://emdatah5.eastmoney.com/dc/zjlx/block/hy",
]
for url in urls:
    try:
        text = fetch(url, 15)
        print(f"[{url[:80]}] len={len(text)}")
        print(f"  {text[:500]}")
        print()
    except Exception as e:
        print(f"[{url[:60]}] FAIL: {e}")
        print()

# Try the datacenter API with different report names
print("=== datacenter report names ===")
report_urls = [
    "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPTA_WEB_MARGIN_TRADING&columns=ALL&filter=&pageNumber=1&pageSize=3&sortTypes=-1&sortColumns=TRADE_DATE",
    "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_DMSK_HOLDER_NUM&columns=ALL&filter=&pageNumber=1&pageSize=3&sortTypes=-1&sortColumns=END_DATE",
    "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_FN_DIVIDEND&columns=ALL&filter=&pageNumber=1&pageSize=3&sortTypes=-1&sortColumns=NOTICE_DATE",
]
for url in report_urls:
    try:
        text = fetch(url, 15)
        data = json.loads(text)
        print(f"  success={data.get('success')}, message={data.get('message', '')[:80]}")
        if data.get('result') and data['result'].get('data'):
            print(f"    items: {len(data['result']['data'])}")
            print(f"    first: {json.dumps(data['result']['data'][0], ensure_ascii=False)[:200]}")
    except Exception as e:
        print(f"  FAIL: {e}")

print("\n=== DONE ===")