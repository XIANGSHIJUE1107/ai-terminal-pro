# -*- coding: utf-8 -*-
"""深度检查各API返回的实际数据内容"""
import json
import ssl
import urllib.request
import gzip

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.sina.com.cn/",
}

EM_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": "https://data.eastmoney.com/",
    "Accept": "*/*",
}

def fetch_raw(url, headers, timeout=15):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        body = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        text = body.decode("utf-8", errors="ignore")
        return text

print("=" * 70)
print("[A] 新浪行业资金流 - 完整返回")
print("=" * 70)
try:
    url = "https://money.finance.sina.com.cn/q/api/openapi.php/StockRankService.getIndustryCapitalFlowInRank?page=1&num=5&sort=net_inflow&asc=0"
    text = fetch_raw(url, HEADERS)
    print(f"Raw({len(text)}): {text[:800]}")
    j = json.loads(text)
    print(f"\nParsed: {json.dumps(j, ensure_ascii=False, indent=2)[:1000]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("[B] 东财push2 板块资金流 - 完整返回")
print("=" * 70)
try:
    url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f62&fs=m:90+t2&fields=f12,f14,f2,f3,f62,f184"
    text = fetch_raw(url, EM_HEADERS, timeout=15)
    print(f"Raw({len(text)}): {text[:1000]}")
    j = json.loads(text)
    print(f"\nParsed: {json.dumps(j, ensure_ascii=False, indent=2)[:1500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("[C] 东财push2his 个股K线 - 完整返回")
print("=" * 70)
try:
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.600487&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56&klt=101&fqt=1&end=20500101&lmt=3"
    text = fetch_raw(url, EM_HEADERS, timeout=15)
    print(f"Raw({len(text)}): {text[:1000]}")
    j = json.loads(text)
    print(f"\nParsed: {json.dumps(j, ensure_ascii=False, indent=2)[:1500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("[D] 东财push2his 资金流 - 完整返回")
print("=" * 70)
try:
    url = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?secid=1.600487&fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&lmt=3"
    text = fetch_raw(url, EM_HEADERS, timeout=15)
    print(f"Raw({len(text)}): {text[:1000]}")
    j = json.loads(text)
    print(f"\nParsed: {json.dumps(j, ensure_ascii=False, indent=2)[:1500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("[E] 东财datacenter - 尝试不同格式")
print("=" * 70)

# 测试不同的东财datacenter URL格式
test_urls = [
    ("标准GET", "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPTA_WEB_MARGIN_TRADING&columns=TRADE_DATE,RZYE&filter=(SECURITY_CODE=%22600487%22)&pageNumber=1&pageSize=3"),
    ("URL编码filter", "https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=TRADE_DATE&sortTypes=-1&pageNumber=1&pageSize=3&reportName=RPTA_WEB_MARGIN_TRADING&columns=ALL&filter=(SECURITY_CODE%3D%22600487%22)"),
]
for name, url in test_urls:
    try:
        text = fetch_raw(url, EM_HEADERS, timeout=15)
        j = json.loads(text)
        print(f"  [{name}] OK ({len(text)}bytes): keys={list(j.keys()) if isinstance(j,dict) else type(j)}")
        if isinstance(j, dict) and 'result' in j:
            r = j['result']
            print(f"    result keys: {list(r.keys()) if isinstance(r,dict) else type(r)}")
            if isinstance(r, dict) and 'data' in r:
                print(f"    data count: {len(r['data'])}")
                if r['data']:
                    print(f"    first item: {json.dumps(r['data'][0], ensure_ascii=False)[:200]}")
    except Exception as e:
        print(f"  [{name}] FAIL: {type(e).__name__}: {str(e)[:120]}")

print("\n" + "=" * 70)
print("[F] 新浪行情数据解析验证")
print("=" * 70)
try:
    url = "https://hq.sinajs.cn/list=sh600487,sz002475,sz000988"
    text = fetch_raw(url, HEADERS)
    for line in text.strip().split("\n"):
        if not line.strip(): continue
        m = line.split('="')
        if len(m) >= 2:
            sym = m[0].replace("var hq_str_", "")
            parts = m[1].rstrip('";\n').split(",")
            if len(parts) >= 10:
                print(f"  {sym}: 名称={parts[0]}, 现价={parts[3]}, 昨收={parts[2]}, 涨跌幅={((float(parts[3])-float(parts[2]))/float(parts[2])*100 if float(parts[2]) else 0):.2f}%, 成交额={parts[9]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("[G] 新闻Feed数据解析验证")
print("=" * 70)
try:
    url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2518&k=&num=3&page=1"
    text = fetch_raw(url, HEADERS)
    j = json.loads(text)
    result = j.get('result', {})
    data = result.get('data', [])
    print(f"  总条数: {len(data)}")
    for item in data[:3]:
        print(f"  - {item.get('title','')[:60]} | time={item.get('ctime','')}")
except Exception as e:
    print(f"Error: {e}")
