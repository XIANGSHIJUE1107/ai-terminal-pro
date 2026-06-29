import sys, os
sys.path.insert(0, '.')
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

import requests
orig = requests.Session.__init__
def patched(self, *a, **k):
    orig(self, *a, **k)
    self.trust_env = False
requests.Session.__init__ = patched

from stock_platform.data.database import init_db
init_db()
from stock_platform.data.fetcher import fetch_stock_daily
df = fetch_stock_daily('600487', start_date='20250101')
print('Rows:', len(df) if df is not None else 0)
if df is not None:
    print(df.head())