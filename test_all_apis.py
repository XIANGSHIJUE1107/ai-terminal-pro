# -*- coding: utf-8 -*-
"""全面测试所有数据API接口可用性"""
import json
import ssl
import urllib.request
import urllib.parse
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": "https://finance.sina.com.cn/",
}

EM_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": "https://data.eastmoney.com/",
    "Accept": "*/*",
}

def test_api(name, url, headers=None, timeout=12):
    """测试单个API，返回结果摘要"""
    h = headers or HEADERS
    t0 = time.time()
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                import gzip
                body = gzip.decompress(body)
            text = body.decode("utf-8", errors="ignore")
            elapsed = round((time.time() - t0) * 1000)
            # 尝试JSON解析
            try:
                j = json.loads(text)
                if isinstance(j, dict):
                    keys = list(j.keys())[:6]
                    return {"status": "OK", "ms": elapsed, "size": len(text), "keys": keys}
                elif isinstance(j, list):
                    return {"status": "OK", "ms": elapsed, "size": len(text), "count": len(j)}
            except:
                pass
            return {"status": "OK", "ms": elapsed, "size": len(text), "preview": text[:120]}
    except Exception as e:
        elapsed = round((time.time() - t0) * 1000)
        err_type = type(e).__name__
        err_msg = str(e)[:100]
        return {"status": "FAIL", "ms": elapsed, "error": f"{err_type}: {err_msg}"}


results = {}

print("=" * 70)
print("【1】新浪行情接口（核心数据源）")
print("=" * 70)

r = test_api("新浪行情-个股", "https://hq.sinajs.cn/list=sh600487,sz002475", HEADERS)
print(f"  新浪行情(个股): {r}")
results["sina_quote_stock"] = r

r = test_api("新浪行情-指数", "https://hq.sinajs.cn/list=sh000001,sz399001", HEADERS)
print(f"  新浪行情(指数): {r}")
results["sina_quote_index"] = r

print("\n" + "=" * 70)
print("【2】新浪K线接口")
print("=" * 70)

r = test_api("新浪K线-日线", 
    "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600487&scale=240&datalen=5",
    HEADERS)
print(f"  新浪K线(日线): {r}")
results["sina_kline"] = r

print("\n" + "=" * 70)
print("【3】新浪新闻接口")
print("=" * 70)

r = test_api("新浪新闻feed", 
    "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2518&k=&num=5&page=1",
    HEADERS)
print(f"  新闻Feed: {r}")
results["sina_news"] = r

print("\n" + "=" * 70)
print("【4】新浪板块资金流")
print("=" * 70)

r = test_api("新浪行业资金流", 
    "https://money.finance.sina.com.cn/q/api/openapi.php/StockRankService.getIndustryCapitalFlowInRank?page=1&num=10&sort=net_inflow&asc=0",
    HEADERS)
print(f"  行业资金流: {r}")
results["sina_sector_flow"] = r

print("\n" + "=" * 70)
print("【5】东方财富 push2 接口")
print("=" * 70)

r = test_api("东财push2-板块列表", 
    "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f62&fs=m:90+t2&fields=f12,f14,f2,f3,f62,f184",
    EM_HEADERS, timeout=15)
print(f"  板块资金流(push2): {r}")
results["em_push2_sector"] = r

r = test_api("东财push2-个股K线", 
    "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.600487&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56&klt=101&fqt=1&end=20500101&lmt=3",
    EM_HEADERS, timeout=15)
print(f"  个股K线(push2his): {r}")
results["em_push2his_kline"] = r

r = test_api("东财push2-资金流", 
    "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?secid=1.600487&fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&lmt=3",
    EM_HEADERS, timeout=15)
print(f"  个股资金流: {r}")
results["em_fund_flow"] = r

print("\n" + "=" * 70)
print("【6】东方财富 datacenter 接口")
print("=" * 70)

r = test_api("东财datacenter-融资融券", 
    "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPTA_WEB_MARGIN_TRADING&columns=TRADE_DATE,RZYE,RZYL,RQYE,RZRQYE&filter=(SECURITY_CODE=\"600487\")&pageNumber=1&pageSize=3&sortTypes=-1&sortColumns=TRADE_DATE",
    EM_HEADERS, timeout=15)
print(f"  融资融券: {r}")
results["em_margin"] = r

r = test_api("东财datacenter-大宗交易", 
    "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPTA_WEB_DZJY_DAILY&columns=TRADE_DATE,SECURITY_NAME,PRICE,PRICE_CHANGE_RATIO,TRADE_AMOUNT&filter=(SECURITY_CODE=\"600487\")&pageNumber=1&pageSize=3&sortTypes=-1&sortColumns=TRADE_DATE",
    EM_HEADERS, timeout=15)
print(f"  大宗交易: {r}")
results["em_blocktrade"] = r

r = test_api("东财datacenter-股东户数", 
    "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_DMSK_HOLDER_NUM&columns=END_DATE,HOLDER_NUM,TOTAL_SHARES,AVG_HOLD_NUM&filter=(SECURITY_CODE=\"600487\")&pageNumber=1&pageSize=3&sortTypes=-1&sortColumns=END_DATE",
    EM_HEADERS, timeout=15)
print(f"  股东户数: {r}")
results["em_holder"] = r

r = test_api("东财datacenter-分红送转", 
    "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_FN_DIVIDEND&columns=NOTICE_DATE,PLAN_EXPLAIN,BONUS_IT_RATIO,TRANSFER_IT_RATIO&filter=(SECURITY_CODE=\"600487\")&pageNumber=1&pageSize=3&sortTypes=-1&sortColumns=NOTICE_DATE",
    EM_HEADERS, timeout=15)
print(f"  分红送转: {r}")
results["em_dividend"] = r

print("\n" + "=" * 70)
print("【汇总】")
print("=" * 70)
ok_count = sum(1 for v in results.values() if v.get("status") == "OK")
fail_count = len(results) - ok_count
print(f"  总计: {len(results)} 个接口 | 成功: {ok_count} | 失败: {fail_count}")

for k, v in results.items():
    status_icon = "✓" if v["status"] == "OK" else "✗"
    detail = ""
    if v.get("status") == "OK":
        detail = f"{v['ms']}ms | size={v['size']}"
        if v.get("count"): detail += f" | count={v['count']}"
        if v.get("keys"): detail += f" | keys={v['keys']}"
    else:
        detail = v.get("error", "")
    print(f"  [{status_icon}] {k}: {detail}")
