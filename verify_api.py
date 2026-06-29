import urllib.request, json

# 1. Portfolio
r = urllib.request.urlopen('http://127.0.0.1:5000/api/portfolio', timeout=30)
d = json.loads(r.read())
print('=== PORTFOLIO ===')
print('Source:', d['source'])
print('Items:', len(d['items']), 'stocks')
for k, v in list(d['items'].items())[:3]:
    print(f'  {k}: {v["name"]} current={v["current"]} change={v["change"]}% live={v["_live"]}')

# 2. Indices
r2 = urllib.request.urlopen('http://127.0.0.1:5000/api/quote?symbols=sh000001,sz399001,sh000300', timeout=30)
d2 = json.loads(r2.read())
print()
print('=== INDICES ===')
for k, v in d2['items'].items():
    print(f'  {k}: {v["name"]} current={v["current"]} change={v["change"]}%')

# 3. Static
r3 = urllib.request.urlopen('http://127.0.0.1:5000/stock_data.js', timeout=10)
print()
print('stock_data.js:', len(r3.read()), 'bytes')
print('=== ALL OK ===')