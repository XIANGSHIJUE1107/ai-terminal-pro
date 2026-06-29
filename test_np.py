# -*- coding: utf-8 -*-
"""测试东财API的不同格式"""
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

# Try np.mobile API (different Eastmoney domain)
urls = [
    "https://np.mobile.eastmoney.com/astock/api/stock/info?code=600487",
    "https://np.mobile.eastmoney.com/astock/api/stock/kline?code=600487&type=day&count=5",
    "https://np.mobile.eastmoney.com/astock/api/stock/capitalflow?code=600487",
]
for url in urls:
    try:
        text = fetch(url, 15)
        print(f"[{url[:80]}] OK, len={len(text)}")
        if text.startswith('{'):
            data = json.loads(text)
            print(f"  {json.dumps(data, ensure_ascii=False)[:300]}")
        else:
            print(f"  {text[:200]}")
        print()
    except Exception as e:
        print(f"[{url[:60]}] FAIL: {e}")
        print()

# Try the hq API (different domain)
urls2 = [
    "https://hqapi.eastmoney.com/api/stock/get?secid=1.600487&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60,f116,f117,f162,f167,f168,f169,f170,f171",
    "https://hqapi.eastmoney.com/api/stock/kline?secid=1.600487&klt=101&fqt=1&end=20500101&lmt=5",
]
for url in urls2:
    try:
        text = fetch(url, 15)
        print(f"[{url[:80]}] OK, len={len(text)}")
        if text.startswith('{'):
            data = json.loads(text)
            print(f"  {json.dumps(data, ensure_ascii=False)[:300]}")
        else:
            print(f"  {text[:200]}")
        print()
    except Exception as e:
        print(f"[{url[:60]}] FAIL: {e}")
        print()

# Try the web api
print("=== web API ===")
try:
    url = "https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery112305632960234350387_1750900000000&pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f62&fs=m:90+t2&fields=f12,f14,f2,f3,f62,f184&_=1750900000000"
    text = fetch(url, 15)
    print(f"OK, len={len(text)}")
    # Try to parse as JSONP
    import re
    m = re.match(r'jQuery\d+_\d+\((.*)\)', text, re.DOTALL)
    if m:
        data = json.loads(m.group(1))
        print(f"  {json.dumps(data, ensure_ascii=False)[:500]}")
    else:
        print(f"  {text[:500]}")
except Exception as e:
    print(f"FAIL: {e}")

print("\n=== DONE ===")