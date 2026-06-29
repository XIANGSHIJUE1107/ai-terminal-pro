# -*- coding: utf-8 -*-
"""
A股数据代理服务器 V6 - 稳定版
特性：
- 使用 ThreadingHTTPServer（多线程，不阻塞）
- 零依赖（不加载backend模块）
- 自动端口检测和冲突处理
- 完善的错误恢复
- 内置数据缓存（避免频繁请求外部API）
"""

import gzip
import http.server
import json
import os
import ssl
import socket as _socket
import sys
import threading
import time as _time
import traceback
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

# ==================== 配置 ====================
PORT = int(os.getenv("PORT", "8080"))
BASE_DIR = Path(__file__).resolve().parent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.sina.com.cn/",
}
EM_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://data.eastmoney.com/",
}

SYMBOLS = ["sh600487","sz002475","sz002384","sz000988","sh600459","sh603211","sh600206","sz000636"]
INDICES = ["sh000001","sz399001","sz399006","sh000300","sh000688","sh000852"]

# 数据缓存（避免重复请求）
_cache = {"portfolio": None, "indices": None, "_ts": 0}
CACHE_TTL = 15  # 秒


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    print(f"[{now()}] {msg}", flush=True)


def _fetch(url, headers=None, timeout=12):
    """安全HTTP请求，带重试"""
    h = headers or HEADERS
    last_err = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=h)
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                body = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                return body.decode("utf-8", errors="ignore")
        except Exception as e:
            last_err = e
            if attempt == 0:
                _time.sleep(0.3)
    raise last_err


def _fetch_json(url, headers=None, timeout=12):
    return json.loads(_fetch(url, headers, timeout))


# ==================== 数据获取 ====================

def get_portfolio():
    """获取持仓股行情（带缓存）"""
    if _cache["portfolio"] and (_time.time() - _cache["_ts"]) < CACHE_TTL:
        return _cache["portfolio"]
    try:
        url = "https://hq.sinajs.cn/list=" + ",".join(SYMBOLS)
        text = _fetch(url, HEADERS, 15)
        result = {}
        for line in text.strip().split("\n"):
            if not line.strip(): continue
            m = line.split('="')
            if len(m) < 2: continue
            sym = m[0].replace("var hq_str_", "")
            parts = m[1].rstrip('";\n').split(",")
            if len(parts) < 10: continue
            cur, prev = float(parts[3] or 0), float(parts[2] or 0)
            result[sym] = {
                "symbol": sym, "name": parts[0],
                "open": float(parts[1] or 0), "prevClose": prev,
                "current": cur, "high": float(parts[4] or 0),
                "low": float(parts[5] or 0),
                "volume": float(parts[8] or 0), "amount": float(parts[9] or 0),
                "change": round((cur - prev) / prev * 100, 2) if prev else 0,
                "source": "新浪财经", "updatedAt": now(),
            }
        _cache["portfolio"] = result
        _cache["_ts"] = _time.time()
        return result
    except Exception as e:
        log(f"ERR portfolio: {e}")
        return _cache["portfolio"] or {}


def get_indices():
    """获取指数行情（带缓存）"""
    if _cache["indices"] and (_time.time() - _cache["_ts"]) < CACHE_TTL:
        return _cache["indices"]
    try:
        url = "https://hq.sinajs.cn/list=" + ",".join(INDICES)
        text = _fetch(url, HEADERS, 15)
        result = {}
        for line in text.strip().split("\n"):
            if not line.strip(): continue
            m = line.split('="')
            if len(m) < 2: continue
            sym = m[0].replace("var hq_str_", "")
            parts = m[1].rstrip('";\n').split(",")
            if len(parts) < 10: continue
            cur, prev = float(parts[3] or 0), float(parts[2] or 0)
            result[sym] = {
                "symbol": sym, "name": parts[0],
                "prevClose": prev, "current": cur,
                "high": float(parts[4] or 0), "low": float(parts[5] or 0),
                "volume": float(parts[8] or 0), "amount": float(parts[9] or 0),
                "change": round((cur - prev) / prev * 100, 2) if prev else 0,
                "source": "新浪财经", "updatedAt": now(),
            }
        _cache["indices"] = result
        _cache["_ts"] = _time.time()
        return result
    except Exception as e:
        log(f"ERR indices: {e}")
        return _cache["indices"] or {}


def get_kline(symbol, scale=240, length=120):
    """新浪K线数据"""
    try:
        url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale={scale}&datalen={min(int(length), 800)}"
        text = _fetch(url, HEADERS, 15)
        data = json.loads(text)
        if not isinstance(data, list): return []
        return [{"date": d.get("day", ""), "open": float(d.get("open", 0) or 0),
                 "close": float(d.get("close", 0) or 0), "high": float(d.get("high", 0) or 0),
                 "low": float(d.get("low", 0) or 0), "volume": float(d.get("volume", 0) or 0)}
                for d in data]
    except Exception as e:
        log(f"ERR kline({symbol}): {e}")
        return []


def get_fund_flow(symbol, days=120):
    """个股资金流：优先东财push2his，失败则用K线估算"""
    # ---- 尝试东财真实API ----
    try:
        secid = f"1.{symbol[2:]}" if symbol.startswith("sh") else f"0.{symbol[2:]}"
        url = (f"https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?"
               f"secid={secid}&fields1=f1,f2,f3,f4&"
               f"fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&"
               f"klt=101&fqt=1&end=20500101&lmt={days}")
        raw = _fetch_json(url, EM_HEADERS, 15)
        klines = (raw.get("data", {}) or {}).get("klines", []) or []
        flows = []
        for k in klines:
            p = k.split(",")
            if len(p) >= 11:
                flows.append({
                    "date": p[0], "mainNetInflow": float(p[10] or 0),
                    "superLargeNetInflow": float(p[3] or 0),
                    "largeNetInflow": float(p[4] or 0),
                    "midNetInflow": float(p[5] or 0),
                    "smallNetInflow": float(p[6] or 0),
                    "changePct": float(p[9] or 0),
                })
        if flows:
            return {"items": flows, "source": "东财push2his", "total": len(flows)}
    except Exception as e:
        log(f"fund-flow API failed, fallback to kline: {e}")

    # ---- Fallback: 用K线数据估算资金流 ----
    try:
        kdata = get_kline(symbol, 240, days)
        if not kdata:
            return {"items": [], "error": "no data", "source": "K线估算"}
        flows = []
        for i, d in enumerate(kdata):
            o, c, h, l, v = d["open"], d["close"], d["high"], d["low"], d["volume"]
            amt = abs(c - o) * v * 100  # 粗略估算成交额方向
            sign = 1 if c >= o else -1
            chg = round((c / o - 1) * 100, 2) if o > 0 else 0
            flows.append({
                "date": d["date"],
                "mainNetInflow": round(sign * amt / 1e8, 2),
                "estimated": True,
                "changePct": chg,
                "close": c, "volume": v,
            })
        return {"items": flows, "source": "K线估算(fallback)", "total": len(flows), "note": "东财不可用，基于K线OHLCV估算"}
    except Exception as e:
        log(f"ERR fund_flow fallback({symbol}): {e}")
        return {"items": [], "error": str(e), "source": "异常"}


def get_news():
    """新浪财经新闻（多源fallback）"""
    sources = [
        ("https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2510&num=20", "新浪财经频道"),
        ("https://feed.mix.sina.com.cn/api/roll/get?pageid=154&lid=2513&num=20", "新浪财经滚动"),
    ]
    for url, src_name in sources:
        try:
            raw = _fetch_json(url, HEADERS, 12)
            items = (raw.get("result", {}) or {}).get("data", []) or []
            if items:
                result = [{"title": it.get("title", ""), "url": it.get("url", ""),
                           "time": it.get("ctime", ""),
                           "summary": it.get("summary", "") or it.get("wapsummary", "")} for it in items]
                log(f"news OK: {len(result)} from {src_name}")
                return {"items": result, "source": src_name}
        except Exception as e:
            log(f"news source [{src_name}] failed: {e}")
    return {"items": [], "error": "all news sources failed"}


# ==================== HTTP Handler ====================

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            p = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(p.query)
            path = p.path

            # ---- 健康检查 ----
            if path == "/api/health":
                return self._ok({"status": "ok", "service": "A股代理V6", "port": PORT, "time": now()})

            # ---- 持仓股 ----
            if path == "/api/portfolio":
                pf = get_portfolio()
                return self._ok({"items": pf, "count": len(pf), "source": "新浪财经"})

            # ---- 指数 ----
            if path == "/api/indices":
                return self._ok(get_indices())

            # ---- 行情(通用) ----
            if path == "/api/quote":
                syms = [s.strip() for s in q.get("symbols", [""])[0].split(",") if s.strip()]
                # 合并持仓+指数
                all_syms = set(SYMBOLS + INDICES + syms)
                pf = get_portfolio()
                idx = get_indices()
                merged = {}
                for s in syms:
                    if s in pf: merged[s] = pf[s]
                    elif s in idx: merged[s] = idx[s]
                return self._ok({"items": merged})

            # ---- K线 ----
            if path == "/api/kline":
                sym = q.get("symbol", ["sh000001"])[0]
                sc = int(q.get("scale", ["240"])[0] or 240)
                ln = int(q.get("length", ["120"])[0] or 120)
                return self._ok({"items": get_kline(sym, sc, ln), "symbol": sym})

            # ---- 资金流 ----
            if path == "/api/fund-flow":
                sym = q.get("symbol", ["sh600487"])[0]
                days = int(q.get("days", ["120"])[0] or 120)
                return self._ok(get_fund_flow(sym, days))

            # ---- 新闻 ----
            if path in ("/api/news", "/api/datahub/news"):
                return self._ok(get_news())

            # ---- 通用代理 ----
            if path == "/api/proxy":
                target = q.get("url", [None])[0]
                if not target: return self._err(400, "Missing url")
                host = urllib.parse.urlparse(target).hostname or ""
                allowed = {"hq.sinajs.cn", "money.finance.sina.com.cn", "feed.mix.sina.com.cn",
                          "finance.sina.com.cn", "push2.eastmoney.com", "push2his.eastmoney.com"}
                if host not in allowed: return self._err(403, f"Forbidden: {host}")
                try:
                    body = _fetch(target, HEADERS, 15).encode()
                    return self._raw(200, "application/json; charset=utf-8", body)
                except Exception as e:
                    return self._err(502, str(e))

            # ---- 静态文件 ----
            fp = path.split("?")[0]
            if fp == "/": fp = "/terminal.html"
            fpath = (BASE_DIR / fp.lstrip("/")).resolve()
            if str(fpath).startswith(str(BASE_DIR)) and fpath.is_file():
                ct = "text/html; charset=utf-8" if fpath.suffix == ".html" else \
                     "application/javascript; charset=utf-8" if fpath.suffix == ".js" else \
                     "application/octet-stream"
                return self._raw(200, ct, fpath.read_bytes())

            self._err(404, "Not Found")
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception:
            traceback.print_exc()
            try: self._err(500, "Error")
            except: pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def _ok(self, data):
        self._json(200, data)

    def _err(self, code, msg):
        self._json(code, {"error": msg})

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._raw(code, "application/json; charset=utf-8", body)

    def _raw(self, code, ct, body):
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass


# ==================== 启动 ====================
if __name__ == "__main__":
    # 尝试使用 ThreadingHTTPServer（更稳定）
    try:
        from http.server import ThreadingHTTPServer as ServerClass
        log("Using ThreadingHTTPServer (multi-threaded)")
    except ImportError:
        ServerClass = http.server.HTTPServer
        log("Using HTTPServer (single-threaded)")

    # 端口冲突检测与自动切换
    test_port = PORT
    for _ in range(3):
        try:
            s = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            s.bind(("127.0.0.1", test_port))
            s.close()
            break
        except OSError:
            log(f"Port {test_port} occupied, trying {test_port+1}")
            test_port += 1

    srv = ServerClass(("127.0.0.1", test_port), H)
    srv.socket.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)

    log("=" * 50)
    log("  A股数据代理服务器 V6 (稳定版)")
    log(f"  http://127.0.0.1:{test_port}/terminal.html")
    log("=" * 50)
    log(f"APIs: /api/health /api/portfolio /api/kline /api/fund-flow /api/news /api/proxy")

    # 预热数据（后台线程）
    def warmup():
        log("Warming up data caches...")
        get_portfolio()
        get_indices()
        log("Data cache ready.")
    t = threading.Thread(target=warmup, daemon=True)
    t.start()

    # 主循环：serve_forever + 自动重启保护
    MAX_RESTARTS = 100
    for restart_count in range(MAX_RESTARTS):
        try:
            if restart_count > 0:
                log(f"Auto-restart #{restart_count} ...")
                srv = ServerClass(("127.0.0.1", test_port), H)
                srv.socket.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
            srv.serve_forever()
            break  # 正常退出(KeyboardInterrupt)则跳出循环
        except KeyboardInterrupt:
            log("\nStopped by user")
            break
        except Exception as e:
            log(f"FATAL(restart #{restart_count}): {e}")
            traceback.print_exc()
            _time.sleep(2)

    log("Server shutdown complete.")
