import urllib.request, json

# 1. Health
r = urllib.request.urlopen('http://127.0.0.1:5000/api/health', timeout=10)
print('HEALTH:', json.loads(r.read())['status'])

# 2. Sector Flow
try:
    r = urllib.request.urlopen('http://127.0.0.1:5000/api/sector-flow?pz=10', timeout=30)
    d = json.loads(r.read())
    print('SECTOR-FLOW:', len(d.get('items', [])), 'sectors')
    for it in d.get('items', [])[:3]:
        print(f'  {it["name"]}: 主力净流入={it["mainNetInflow"]} 涨跌={it["changePct"]}%')
except Exception as e:
    print('SECTOR-FLOW ERROR:', e)

# 3. Fund Flow
try:
    r = urllib.request.urlopen('http://127.0.0.1:5000/api/fund-flow?symbol=sh600487&type=daily&days=5', timeout=30)
    d = json.loads(r.read())
    print('FUND-FLOW:', len(d.get('items', [])), 'days')
except Exception as e:
    print('FUND-FLOW ERROR:', e)

# 4. Sector History
try:
    r = urllib.request.urlopen('http://127.0.0.1:5000/api/sector-history?code=BK0477&days=5', timeout=30)
    d = json.loads(r.read())
    print('SECTOR-HISTORY:', len(d.get('history', [])), 'bars')
except Exception as e:
    print('SECTOR-HISTORY ERROR:', e)

# 5. Margin
try:
    r = urllib.request.urlopen('http://127.0.0.1:5000/api/margin?symbol=sh600487', timeout=30)
    d = json.loads(r.read())
    print('MARGIN:', len(d.get('items', [])), 'records')
except Exception as e:
    print('MARGIN ERROR:', e)

# 6. Block Trade
try:
    r = urllib.request.urlopen('http://127.0.0.1:5000/api/block-trade?symbol=sh600487', timeout=30)
    d = json.loads(r.read())
    print('BLOCK-TRADE:', len(d.get('items', [])), 'records')
except Exception as e:
    print('BLOCK-TRADE ERROR:', e)

print('=== ALL DONE ===')