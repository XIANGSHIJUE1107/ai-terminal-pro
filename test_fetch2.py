import sys, os
sys.path.insert(0, '.')

# Same setup as fetcher.py
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

import requests
orig = requests.Session.__init__
def patched(self, *a, **k):
    orig(self, *a, **k)
    self.trust_env = False
    self.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
requests.Session.__init__ = patched

import akshare as ak
print("AKShare imported, trying to fetch...")
df = ak.stock_zh_a_hist(symbol="600487", period="daily", start_date="20250101", end_date="20250616", adjust="qfq")
print("Result:", type(df), len(df) if df is not None else 0)
if df is not None:
    print(df.head())