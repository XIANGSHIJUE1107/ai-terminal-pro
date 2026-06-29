# -*- coding: utf-8 -*-
"""Simple HTTP server for terminal.html"""
import http.server
import os
import json
import urllib.request
import urllib.parse
import mimetypes
import gzip
import socket
import traceback
from pathlib import Path

# Disable proxy
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

BASE_DIR = Path(__file__).resolve().parent
PORT = 8080

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.sina.com.cn/',
    'Accept': '*/*',
}

ALLOWED_HOSTS = {
    'hq.sinajs.cn', 'money.finance.sina.com.cn', 'feed.mix.sina.com.cn',
    'finance.sina.com.cn', 'push2.eastmoney.com', 'push2his.eastmoney.com',
    'data.eastmoney.com', 'quote.eastmoney.com',
}


def fetch_url(url):
    host = urllib.parse.urlparse(url).hostname
    if host not in ALLOWED_HOSTS:
        return 403, 'text/plain', b'Forbidden'
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
            if resp.headers.get('Content-Encoding', '') == 'gzip':
                body = gzip.decompress(body)
            return 200, resp.headers.get('Content-Type', 'text/plain'), body
    except Exception as e:
        return 502, 'text/plain', str(e).encode()


def fetch_sina_kline(symbol, scale, length):
    sym = symbol.strip().lower()
    url = f'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sym}&scale={scale}&datalen={min(length, 800)}'
    code, ct, body = fetch_url(url)
    if code != 200 or not body:
        return []
    data = json.loads(body.decode('utf-8', 'ignore'))
    if not isinstance(data, list):
        return []
    rows = []
    for item in data:
        if not isinstance(item, dict):
            continue
        d = item.get('day') or item.get('date') or ''
        if not d:
            continue
        try:
            rows.append({
                'date': d,
                'open': float(item.get('open', 0) or 0),
                'close': float(item.get('close', 0) or 0),
                'high': float(item.get('high', 0) or 0),
                'low': float(item.get('low', 0) or 0),
                'volume': float(item.get('volume', 0) or 0),
                'amount': float(item.get('amount', 0) or 0),
                'source': 'sina',
            })
        except Exception:
            continue
    return rows[-length:]


def fetch_sina_quotes(symbols):
    url = 'http://hq.sinajs.cn/list=' + ','.join(symbols)
    code, ct, body = fetch_url(url)
    if code != 200 or not body:
        return {}
    text = body.decode('gbk', 'replace')
    result = {}
    for line in text.split(';'):
        line = line.strip()
        if not line or 'var hq_str_' not in line:
            continue
        parts = line.split('"')
        if len(parts) < 2:
            continue
        sym = parts[0].replace('var hq_str_', '')
        vals = [v.strip() for v in parts[1].split(',')]
        if len(vals) < 10:
            continue
        try:
            cur = float(vals[3] or 0)
            prev = float(vals[2] or 0)
            result[sym] = {
                'symbol': sym, 'name': vals[0],
                'open': float(vals[1] or 0), 'prevClose': prev,
                'current': cur, 'high': float(vals[4] or 0),
                'low': float(vals[5] or 0), 'volume': float(vals[8] or 0),
                'amount': float(vals[9] or 0),
                'change': (cur - prev) / prev * 100 if prev else 0,
                'changePct': (cur - prev) / prev * 100 if prev else 0,
                'source': 'sina-realtime', '_live': True,
            }
        except Exception:
            continue
    return result


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            path = parsed.path

            # API: proxy
            if path == '/api/proxy':
                url = params.get('url', [None])[0]
                if not url:
                    self._send(400, 'text/plain', b'Missing url')
                    return
                code, ct, body = fetch_url(url)
                self._send(code, ct, body)
                return

            # API: kline
            if path == '/api/kline':
                symbol = params.get('symbol', ['sh000001'])[0]
                scale = int(params.get('scale', ['240'])[0] or 240)
                length = int(params.get('length', ['120'])[0] or 120)
                rows = fetch_sina_kline(symbol, scale, length)
                self._json({'items': rows, 'symbol': symbol, 'scale': scale, 'source': 'sina'})
                return

            # API: quote / portfolio / indices
            if path in ('/api/quote', '/api/portfolio', '/api/indices'):
                syms_str = params.get('symbols', [''])[0]
                if syms_str:
                    syms = [s.strip() for s in syms_str.split(',') if s.strip()]
                else:
                    syms = ['sh000001', 'sz399001', 'sz399006', 'sh000300', 'sh000688',
                            'sh600487', 'sz002475', 'sz002384', 'sz000988',
                            'sh600459', 'sh603211', 'sh600206', 'sz000636']
                result = fetch_sina_quotes(syms)
                self._json({'items': result, 'count': len(result)})
                return

            # API: news
            if path in ('/api/news', '/api/datahub/news'):
                try:
                    url = 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2514&num=20&versionNumber=1.2.4'
                    code, ct, body = fetch_url(url)
                    if code == 200:
                        nd = json.loads(body)
                        items = [{'title': r.get('title', ''), 'time': r.get('ctime', ''),
                                  'url': r.get('url', ''), 'source': '新浪'}
                                 for r in nd.get('result', {}).get('data', [])]
                        self._json({'items': items, 'count': len(items), 'source': '新浪新闻'})
                        return
                except Exception:
                    pass
                self._json({'items': [], 'count': 0, 'source': '无数据'})
                return

            # API: health
            if path == '/api/health':
                self._json({'status': 'ok', 'mode': 'simple-server'})
                return

            # API: fund-flow / margin etc (return empty)
            if path in ('/api/fund-flow', '/api/margin', '/api/block-trade',
                        '/api/holder-num', '/api/dividend', '/api/datahub/latest',
                        '/api/data/snapshots', '/api/data/portfolio',
                        '/api/datahub/quotes', '/api/datahub/portfolio',
                        '/api/datahub/sectors', '/api/datahub/sector-history',
                        '/api/sector-flow', '/api/sector-flow-sina', '/api/datahub/kline'):
                self._json({'items': [], 'count': 0, 'source': 'unavailable'})
                return

            # Static file serving
            file_path = path.split('?')[0]
            if file_path == '/':
                file_path = '/terminal.html'
            fp = (BASE_DIR / file_path.lstrip('/')).resolve()
            if not str(fp).startswith(str(BASE_DIR)) or not fp.is_file():
                self._send(404, 'text/plain', b'Not found')
                return
            ct = mimetypes.guess_type(str(fp))[0] or 'application/octet-stream'
            if fp.suffix == '.js':
                ct = 'application/javascript; charset=utf-8'
            elif fp.suffix == '.html':
                ct = 'text/html; charset=utf-8'
            self._send(200, ct, fp.read_bytes())
        except Exception:
            traceback.print_exc()
            self._send(500, 'text/plain', b'Internal error')

    def _send(self, code, ct, body):
        self.send_response(code)
        self.send_header('Content-Type', ct)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _json(self, payload):
        self._send(200, 'application/json; charset=utf-8',
                   json.dumps(payload, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    print(f'Starting server on http://127.0.0.1:{PORT}/terminal.html')
    server = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.daemon_threads = True
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Stopped')
        server.shutdown()