import sys, os
sys.path.insert(0, '.')
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

import requests
from requests.sessions import Session

# Patch Session.__init__ 
orig_init = Session.__init__
def patched_init(self, *a, **k):
    orig_init(self, *a, **k)
    self.trust_env = False
    self.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })
Session.__init__ = patched_init

# Verify patch works
s = Session()
print("trust_env:", s.trust_env)
print("UA:", s.headers.get("User-Agent"))

# Also patch the default adapter
import requests.adapters
orig_send = requests.adapters.HTTPAdapter.send
def patched_send(self, request, **kwargs):
    print(f"  [DEBUG] Sending to: {request.url}")
    print(f"  [DEBUG] Headers: {dict(request.headers)}")
    print(f"  [DEBUG] Proxy: {self.proxy_manager}")
    return orig_send(self, request, **kwargs)
requests.adapters.HTTPAdapter.send = patched_send

import akshare as ak
print("\nTrying to fetch...")
try:
    df = ak.stock_zh_a_hist(symbol="600487", period="daily", start_date="20250101", end_date="20250616", adjust="qfq")
    print("Success:", len(df))
except Exception as e:
    print(f"Error: {e}")