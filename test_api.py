import urllib.request, json, sys

try:
    url = 'http://127.0.0.1:8080/api/fundamental/comprehensive?symbol=002475'
    r = urllib.request.urlopen(url, timeout=15)
    data = json.loads(r.read())
    print('STATUS OK')
    print('sources:', data.get('sources', []))
    print('forecast keys:', list(data.get('forecast', {}).keys()))
    print('ths_forecast keys:', list(data.get('ths_forecast', {}).keys()))
    print('eastmoney_detail count:', data.get('eastmoney_detail', {}).get('count', 0))
except Exception as e:
    print('ERROR:', e)
