# -*- coding: utf-8 -*-
"""测试东财网页API"""
import urllib.request, json, ssl, gzip, re

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36", "Referer": "https://data.eastmoney.com/", "Accept": "*/*"}

def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers=HEADERS)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        body = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        return body.decode("utf-8", errors="ignore")

# The Eastmoney sector flow page loads data via AJAX
# Let's try to find the actual API endpoint
html = fetch("https://data.eastmoney.com/bkzj/hy.html")
print(f"HTML length: {len(html)}")

# Search for API URLs in the page
api_urls = re.findall(r'(https?://[^"\']*(?:push2|api|data)[^"\']*)', html)
print(f"\nFound {len(api_urls)} API URLs in page:")
for u in api_urls[:20]:
    print(f"  {u[:120]}")

# Search for data patterns
import re
# Look for embedded JSON
json_patterns = re.findall(r'(?:var|let|const)\s+\w+\s*=\s*(\[[^\]]*\{[^}]*f62[^}]*\}[^\]]*\])', html, re.DOTALL)
print(f"\nFound {len(json_patterns)} patterns with f62:")
for p in json_patterns[:3]:
    print(f"  {p[:300]}")

# Try the datacenter API with a different filter format
print("\n=== datacenter API with code filter ===")
try:
    url = "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPTA_WEB_MARGIN_TRADING&columns=ALL&filter=(SECURITY_CODE=%22600487%22)&pageNumber=1&pageSize=3&sortTypes=-1&sortColumns=TRADE_DATE"
    text = fetch(url)
    data = json.loads(text)
    print(f"success: {data.get('success')}, message: {data.get('message', '')[:100]}")
    if data.get('result') and data['result'].get('data'):
        print(f"items: {len(data['result']['data'])}")
except Exception as e:
    print(f"FAIL: {e}")

print("\n=== DONE ===")