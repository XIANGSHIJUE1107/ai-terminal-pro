# -*- coding: utf-8 -*-
"""测试从东财网页抓取板块资金流数据"""
import urllib.request, json, ssl, gzip, re

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}

def fetch(url, headers=None, timeout=10):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        body = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        return body.decode("utf-8", errors="ignore")

# Test: 东财行业资金流页面 - 找嵌入的JSON数据
print("=== 东财行业资金流页面 ===")
try:
    html = fetch("https://data.eastmoney.com/bkzj/hy.html")
    print(f"HTML length: {len(html)}")
    
    # Look for JSON data patterns
    # Common patterns: window.__DATA__ = {...}, var data = [...], etc.
    patterns = [
        r'var\s+rankData\s*=\s*(\[.*?\]);',
        r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
        r'\"data\":\s*(\[.*?\])',
        r'var\s+dataList\s*=\s*(\[.*?\]);',
        r'var\s+list\s*=\s*(\[.*?\]);',
    ]
    for pat in patterns:
        matches = re.findall(pat, html, re.DOTALL)
        if matches:
            print(f"Found pattern '{pat[:50]}...': {len(matches)} matches")
            print(f"  First match (truncated): {matches[0][:500]}")
    
    # Search for specific data patterns
    if 'mainNetInflow' in html or 'f62' in html:
        print("Found capital flow data patterns!")
    
    # Search for sector names
    if '通信设备' in html:
        print("Found sector names in HTML!")
    
except Exception as e:
    print("FAIL:", e)

# Test: 东财行业资金流JSON API
print("\n=== 东财行业资金流JSON API ===")
try:
    # Try the API used by the web page
    url = "https://data.eastmoney.com/bkzj/hy.html"
    # The page might load data via a separate API
    # Let's try common API patterns
    api_urls = [
        "https://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz=20&po=1&np=1&fltt=2&invt=2&fid=f62&fs=m:90+t2&fields=f2,f3,f4,f12,f14,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87",
        "https://data.eastmoney.com/dataapi/xuangu/industry",
    ]
    for url in api_urls:
        try:
            text = fetch(url, timeout=10)
            print(f"OK [{url[:80]}]:", text[:300])
        except Exception as e:
            print(f"FAIL [{url[:60]}]:", e)
except Exception as e:
    print("FAIL:", e)

print("\n=== DONE ===")