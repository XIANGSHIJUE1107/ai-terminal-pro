# -*- coding: utf-8 -*-
"""从东财网页提取板块资金流数据"""
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

html = fetch("https://data.eastmoney.com/bkzj/hy.html")

# Search for all script/data patterns
# Find all script tags
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print(f"Found {len(scripts)} script tags")

# find data patterns
for i, s in enumerate(scripts):
    if 'bkzj' in s.lower() or 'sector' in s.lower() or '板块' in s or 'f62' in s or 'f12' in s:
        print(f"\nScript {i} (len={len(s)}):")
        print(s[:1000])

# Also search for JSON-like data
print("\n\n=== Searching for JSON data ===")
# Look for patterns like: var xxx = [...]
data_vars = re.findall(r'var\s+(\w+)\s*=\s*(\[[^\]]*\])', html)
for name, val in data_vars[:10]:
    print(f"var {name} = {val[:200]}")

# Look for large arrays
arrays = re.findall(r'\[{.*?}\]', html)
for arr in arrays:
    if len(arr) > 200:
        print(f"\nLarge array (len={len(arr)}):")
        print(arr[:500])
        break

# Look for function calls with data
func_calls = re.findall(r'(\w+)\((\[.*?\])\)', html, re.DOTALL)
for name, args in func_calls:
    if len(args) > 200:
        print(f"\nFunction call {name} (len={len(args)}):")
        print(args[:500])
        break

print("\n=== DONE ===")