# -*- coding: utf-8 -*-
from __future__ import annotations

import gzip
import http.server
import io
import json
import mimetypes
import os
import socket as _socket
import time as _time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# 懒加载 datahub（避免 import 阶段死锁）
_datahub = None
_datahub_ok = False
_datahub_lock = _time.time()  # 记录首次尝试时间

def _get_datahub():
    """获取 datahub 服务实例，超时则返回 None"""
    global _datahub, _datahub_ok
    if _datahub is not None:
        return _datahub if _datahub_ok else None
    # 超过30秒还没导入成功就放弃
    if _time.time() - _datahub_lock > 30:
        return None
    try:
        from backend.datahub import datahub_service
        _datahub = datahub_service
        _datahub_ok = True
        return _datahub
    except Exception:
        _datahub = "failed"
        return None

def _get_scheduler_funcs():
    try:
        from backend.tasks.scheduler import start_scheduler, stop_scheduler
        return start_scheduler, stop_scheduler
    except Exception:
        return None, None


def _normalize_symbol(symbol: str) -> str:
    symbol = str(symbol or "").strip().lower()
    if symbol.startswith(("sh", "sz", "bj")):
        return symbol
    if symbol.endswith(".sh"):
        return "sh" + symbol[:6]
    if symbol.endswith(".sz"):
        return "sz" + symbol[:6]
    if symbol.startswith(("6", "5", "9")):
        return "sh" + symbol[:6]
    if symbol.startswith(("0", "2", "3")):
        return "sz" + symbol[:6]
    return symbol


def _fetch_sina_kline(symbol: str, scale: int, length: int) -> list[dict]:
    sym = _normalize_symbol(symbol)
    try:
        url = (
            "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            "CN_MarketData.getKLineData?"
            f"symbol={sym}&scale={int(scale)}&datalen={min(int(length), 800)}"
        )
        code, _, body = fetch_url(url)
        if code != 200 or not body:
            return []
        data = json.loads(body.decode("utf-8", errors="ignore"))
        if not isinstance(data, list):
            return []
        rows = []
        for item in data:
            if not isinstance(item, dict):
                continue
            date = item.get("day") or item.get("date") or item.get("time") or ""
            if not date:
                continue
            try:
                rows.append({
                    "date": date,
                    "open": float(item.get("open", 0) or 0),
                    "close": float(item.get("close", 0) or 0),
                    "high": float(item.get("high", 0) or 0),
                    "low": float(item.get("low", 0) or 0),
                    "volume": float(item.get("volume", 0) or 0),
                    "amount": float(item.get("amount", 0) or 0),
                    "source": "sina",
                })
            except Exception:
                continue
        return rows[-length:]
    except Exception:
        return []


def _fetch_eastmoney_kline(symbol: str, scale: int, length: int) -> list[dict]:
    sym = _normalize_symbol(symbol)
    secid = f"1.{sym[2:]}" if sym.startswith("sh") else f"0.{sym[2:]}"
    if scale == 1:
        klt = 1
    elif scale >= 7200:
        klt = 103
    elif scale >= 1200:
        klt = 102
    elif scale >= 240:
        klt = 101
    elif scale >= 60:
        klt = 60
    elif scale >= 30:
        klt = 30
    elif scale >= 15:
        klt = 15
    else:
        klt = 5
    try:
        url = (
            "https://push2his.eastmoney.com/api/qt/stock/kline/get?"
            f"secid={secid}&klt={klt}&fqt=1&lmt={min(int(length), 800)}&end=20500101&smplmt=460"
            "&fields1=f1,f2,f3,f4,f5,f6"
            "&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        )
        req = urllib.request.Request(url, headers={**HEADERS, "Referer": "https://data.eastmoney.com/"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        klines = (data.get("data") or {}).get("klines") or []
        rows = []
        for row in klines:
            parts = row.split(",")
            if len(parts) < 6:
                continue
            try:
                rows.append({
                    "date": parts[0],
                    "open": float(parts[1] or 0),
                    "close": float(parts[2] or 0),
                    "high": float(parts[3] or 0),
                    "low": float(parts[4] or 0),
                    "volume": float(parts[5] or 0),
                    "amount": float(parts[6] or 0) if len(parts) > 6 else 0,
                    "source": "eastmoney",
                })
            except Exception:
                continue
        return rows[-length:]
    except Exception:
        return []


def _fetch_eastmoney_trends_1m(symbol: str, length: int) -> list[dict]:
    sym = _normalize_symbol(symbol)
    secid = f"1.{sym[2:]}" if sym.startswith("sh") else f"0.{sym[2:]}"
    try:
        url = (
            "https://push2.eastmoney.com/api/qt/stock/trends2/get?"
            f"secid={secid}&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11"
            "&fields2=f51,f52,f53,f54,f55,f56,f57,f58&iscr=0&ndays=1"
        )
        req = urllib.request.Request(url, headers={**HEADERS, "Referer": "https://quote.eastmoney.com/"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        rows = []
        for row in ((data.get("data") or {}).get("trends") or []):
            parts = row.split(",")
            if len(parts) < 7:
                continue
            try:
                rows.append({
                    "date": parts[0],
                    "open": float(parts[1] or 0),
                    "close": float(parts[2] or 0),
                    "high": float(parts[3] or 0),
                    "low": float(parts[4] or 0),
                    "volume": float(parts[5] or 0),
                    "amount": float(parts[6] or 0),
                    "source": "eastmoney-trends",
                })
            except Exception:
                continue
        return rows[-length:]
    except Exception:
        return []


def _get_kline_data(symbol: str, scale: int, length: int) -> list[dict]:
    if int(scale) == 1:
        rows = _fetch_eastmoney_trends_1m(symbol, length)
        if rows:
            return rows
    rows = _fetch_sina_kline(symbol, scale, length)
    if rows:
        return rows
    rows = _fetch_eastmoney_kline(symbol, scale, length)
    if rows:
        return rows
    try:
        from backend.datahub import datahub_service
        return datahub_service.get_kline(symbol, scale, length)
    except Exception:
        return []


PORT = int(os.getenv("PORT", "8080"))
BASE_DIR = Path(__file__).resolve().parent
ALLOWED_HOSTS = {
    "hq.sinajs.cn",
    "money.finance.sina.com.cn",
    "feed.mix.sina.com.cn",
    "finance.sina.com.cn",
    "push2.eastmoney.com",
    "push2his.eastmoney.com",
    "data.eastmoney.com",
    "quote.eastmoney.com",
    "news.10jqka.com.cn",
    "data.10jqka.com.cn",
    "www.jin10.com",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Referer": "https://finance.sina.com.cn/",
    "Accept": "*/*",
}


def now_text() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fetch_url(target_url: str) -> tuple[int, str, bytes]:
    host = urllib.parse.urlparse(target_url).hostname
    if host not in ALLOWED_HOSTS:
        return 403, "text/plain; charset=utf-8", f"Forbidden: {host}".encode("utf-8")
    try:
        req = urllib.request.Request(target_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
            if resp.headers.get("Content-Encoding", "") == "gzip":
                body = gzip.decompress(body)
            content_type = resp.headers.get("Content-Type", "text/plain")
            return 200, content_type, body
    except urllib.error.HTTPError as exc:
        return exc.code, "text/plain; charset=utf-8", str(exc).encode("utf-8")
    except Exception as exc:
        traceback.print_exc()
        return 502, "text/plain; charset=utf-8", str(exc).encode("utf-8")


def export_excel(records: dict) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "review"
    ws.append(["date", records.get("date", "")])
    ws.append(["generated_at", now_text()])
    ws.append(["note", records.get("note", "")])
    stream = io.BytesIO()
    wb.save(stream)
    return stream.getvalue()


def export_word(records: dict) -> bytes:
    from docx import Document

    doc = Document()
    doc.add_heading("Daily Review", 0)
    doc.add_paragraph(f"date: {records.get('date', '')}")
    doc.add_paragraph(f"generated_at: {now_text()}")
    doc.add_paragraph(records.get("note", "") or "")
    stream = io.BytesIO()
    doc.save(stream)
    return stream.getvalue()


class Handler(http.server.BaseHTTPRequestHandler):
    def _serve_datahub_or_fallback(self, path, params, handler):
        try:
            dh = _get_datahub()
            if dh is None:
                raise RuntimeError("datahub unavailable")
            payload = handler(dh)
            self._json(payload)
            return
        except Exception:
            traceback.print_exc()
            self._fallback_api(path, params)

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            path = parsed.path

            # 静态文件优先（不依赖 datahub）
            if path not in ("/api/health", "/api/portfolio", "/api/indices",
                           "/api/quote", "/api/news",
                           "/api/fund-flow", "/api/datahub/latest",
                           "/api/data/snapshots", "/api/data/portfolio",
                           "/api/datahub/news", "/api/datahub/quotes",
                           "/api/datahub/portfolio", "/api/datahub/sectors",
                           "/api/datahub/sector-history"):
                # 非数据API走原有逻辑
                pass
            else:
                # 数据API：尝试 datahub，失败则 fallback 到新浪直接请求
                dh = _get_datahub()
                if dh is None:
                    self._fallback_api(path, params)
                    return

            if path == "/api/health":
                return self._serve_datahub_or_fallback(path, params, lambda dh: dh.health())
            if path in {"/api/datahub/latest", "/api/data/latest"}:
                return self._serve_datahub_or_fallback(path, params, lambda dh: dh.latest())
            if path in {"/api/datahub/snapshots", "/api/data/snapshots"}:
                kind = params.get("kind", [None])[0]
                def _snap(dh):
                    items = dh.snapshot_list(kind)
                    return {
                        "source": "datahub_snapshots",
                        "updatedAt": dh.state().get("last_update_time"),
                        "asOf": "2026-06-23",
                        "freshness": "local-cache",
                        "stale": False,
                        "unavailable": False,
                        "errors": [],
                        "data": {"items": items},
                        "items": items,
                    }
                return self._serve_datahub_or_fallback(path, params, _snap)
            if path in ("/api/datahub/portfolio", "/api/portfolio"):
                return self._serve_datahub_or_fallback(path, params, lambda dh: dh.portfolio())
            if path in ("/api/datahub/quotes", "/api/quote", "/api/indices"):
                symbols = [s.strip() for s in ",".join(params.get("symbols", [])).split(",") if s.strip()]
                return self._serve_datahub_or_fallback(path, params, lambda dh: dh.quotes(symbols))
            if path == "/api/datahub/sectors":
                refresh = params.get("refresh", ["0"])[0] in {"1", "true", "yes"}
                return self._serve_datahub_or_fallback(path, params, lambda dh: dh.sectors(refresh=refresh))
            if path in ("/api/datahub/news", "/api/news"):
                return self._serve_datahub_or_fallback(path, params, lambda dh: dh.news())
            if path in ("/api/fund-flow", "/api/sector-flow", "/api/sector-flow-sina"):
                return self._serve_datahub_or_fallback(path, params, lambda dh: dh.sectors(refresh=False))
            if path in ("/api/datahub/kline", "/api/kline"):
                symbol = params.get("symbol", ["sh000001"])[0]
                scale = int(params.get("scale", ["240"])[0] or 240)
                length = int(params.get("length", ["120"])[0] or 120)
                self._json({
                    "items": _get_kline_data(symbol, scale, length),
                    "symbol": symbol,
                    "scale": scale,
                    "length": length,
                    "source": "sina-eastmoney",
                })
                return
            if path == "/api/datahub/sector-history":
                name = params.get("name", [""])[0]
                days = int(params.get("days", ["30"])[0] or 30)
                return self._serve_datahub_or_fallback(path, params, lambda dh: dh.sector_history(name, days))
            if path == "/api/proxy":
                self._proxy()
                return

            self._static()
        except Exception:
            traceback.print_exc()
            self._send(500, "text/plain; charset=utf-8", b"Internal server error")

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            if path in {"/api/datahub/refresh", "/api/data/refresh"}:
                try:
                    dh = _get_datahub()
                    if dh is None:
                        raise RuntimeError("datahub unavailable")
                    self._json(dh.refresh(force=True))
                except Exception:
                    traceback.print_exc()
                    self._json({"status": "ok", "mode": "sina-fallback", "datahub": False, "message": "refresh skipped"})
                return
            if path == "/api/export/review":
                self._export_review()
                return
            self._send(404, "text/plain; charset=utf-8", b"Not found")
        except Exception:
            traceback.print_exc()
            self._send(500, "text/plain; charset=utf-8", b"Internal server error")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def _proxy(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        target_url = params.get("url", [None])[0]
        if not target_url:
            self._send(400, "text/plain; charset=utf-8", b"Missing url")
            return
        code, content_type, body = fetch_url(target_url)
        self._send(code, content_type, body)

    def _export_review(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length).decode("utf-8")
        records = json.loads(payload or "{}")
        fmt = (records.get("format") or "xlsx").lower()
        if fmt == "docx":
            body = export_word(records)
            ctype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"daily_review_{records.get('date', '')}.docx"
        else:
            body = export_excel(records)
            ctype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"daily_review_{records.get('date', '')}.xlsx"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{urllib.parse.quote(filename)}")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        try:
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def _static(self):
        path = urllib.parse.unquote(self.path.split("?")[0])
        if path == "/":
            path = "/terminal.html"
        filepath = (BASE_DIR / path.lstrip("/")).resolve()
        if not str(filepath).startswith(str(BASE_DIR)) or not filepath.is_file():
            self._send(404, "text/plain; charset=utf-8", b"Not found")
            return
        content_type = mimetypes.guess_type(str(filepath))[0] or "application/octet-stream"
        if filepath.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        elif filepath.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        self._send(200, content_type, filepath.read_bytes())

    def _json(self, payload):
        self._send(200, "application/json; charset=utf-8", json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _send(self, code, content_type, body):
        try:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass

    def log_message(self, format, *args):
        pass

    # ============================================================
    # Fallback：datahub 不可用时直接调新浪 API
    # ============================================================
    _SYMBOLS = ["sh600487","sz002475","sz002384","sz000988","sh600459",
                "sh603211","sh600206","sz000636"]
    _INDICES = ["sh000001","sz399001","sz399006","sh000300","sh000688"]

    def _fetch_sina(self, symbols):
        """从新浪获取实时行情"""
        url = "http://hq.sinajs.cn/list=" + ",".join(symbols)
        code, ct, body = fetch_url(url)
        if code != 200:
            return {}
        result = {}
        for line in body.decode("gbk", errors="replace").split(";"):
            line = line.strip()
            if not line or "var hq_str_" not in line:
                continue
            parts = line.split('"')
            if len(parts) < 2:
                continue
            sym = parts[0].replace("var hq_str_", "")
            vals = [v.strip() for v in parts[1].split(",")]
            if len(vals) < 32:
                continue
            result[sym] = {
                "name": vals[0], "current": vals[3],
                "open": vals[2], "high": vals[4], "low": vals[5],
                "volume": vals[8], "amount": vals[9],
                "change": vals[2] and vals[3] and float(vals[3]) - float(vals[2]) if vals[2] and vals[3] else 0,
                "pct": (float(vals[3]) - float(vals[2])) / float(vals[2]) * 100 if vals[2] and vals[3] and float(vals[2]) else 0,
                "turnover": vals[38] if len(vals) > 38 else "",
                "volume_ratio": "", "source": "新浪财经"
            }
        return result

    def _fallback_api(self, path, params):
        """datahub 不可用时的 fallback 数据接口"""
        try:
            if path == "/api/health":
                self._json({"status": "ok", "mode": "sina-fallback", "datahub": False})
                return
            if path in ("/api/portfolio", "/api/datahub/portfolio"):
                data = self._fetch_sina(self._SYMBOLS)
                self._json({"items": data, "count": len(data), "source": "新浪财经(fallback)"})
                return
            if path in ("/api/indices", "/api/quote", "/api/datahub/quotes"):
                syms = params.get("symbols", [])
                if not syms:
                    syms = self._INDICES + self._SYMBOLS
                data = self._fetch_sina(syms)
                self._json(data)
                return
            if path == "/api/kline" or path == "/api/datahub/kline":
                symbol = params.get("symbol", ["sh000001"])[0]
                scale = int(params.get("scale", ["240"])[0] or 240)
                length = int(params.get("length", ["120"])[0] or 120)
                # 新浪K线API
                kurl = f"https://finance.sina.com.cn/realstock/company/{symbol}/kline.shtml?symbol={symbol}&scale={scale}&datalen={length}"
                code, ct, body = fetch_url(kurl)
                if code == 200 and body:
                    import re
                    m = re.search(r'(\[.*?\])', body.decode("utf-8", errors="replace"))
                    if m:
                        self._json({"data": eval(m.group(1)), "source": "新浪K线"})
                        return
                self._json({"data": [], "error": "kline_unavailable"})
                return
            if path in ("/api/news", "/api/datahub/news"):
                # 新浪财经新闻 feed
                nurl = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2514&num=20&versionNumber=1.2.4"
                code, ct, body = fetch_url(nurl)
                if code == 200:
                    nd = json.loads(body)
                    items = [{"title": r.get("title",""), "time": r.get("ctime",""),
                              "url": r.get("url",""), "source": "新浪"} for r in nd.get("result", {}).get("data", [])]
                    self._json({"items": items, "count": len(items), "source": "新浪新闻"})
                    return
                self._json({"items": [], "count": 0, "source": "无数据"})
                return
            # 其他API返回空
            self._json({"items": {}, "count": 0, "source": "unavailable"})
        except Exception as e:
            self._json({"error": str(e), "items": {}})


if __name__ == "__main__":
    # Disable system proxy
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['NO_PROXY'] = '*'

    print(f"Server starting on http://127.0.0.1:{PORT}/terminal.html", flush=True)

    # 延迟初始化状态
    _init_state = {"done": False}

    def _lazy_init():
        """首次请求时才初始化 datahub 和 scheduler"""
        if _init_state["done"]:
            return
        _init_state["done"] = True
        import threading as _th

        # datahub refresh 放后台线程（非阻塞）
        def _bg():
            try:
                dh = _get_datahub()
                if dh:
                    dh.refresh(force=True)
                    print("[init] datahub refresh done", flush=True)
                else:
                    print("[init] datahub unavailable, using sina fallback", flush=True)
            except Exception as e:
                print("[init] datahub err: %s" % e, flush=True)
        _th.Thread(target=_bg, daemon=True).start()

        # scheduler（可选）
        try:
            _start, _stop = _get_scheduler_funcs()
            if _start:
                try:
                    _start()
                    print("[init] scheduler started", flush=True)
                except Exception as e:
                    print("[init] scheduler skipped: %s" % e, flush=True)
        except Exception as e:
            print("[init] scheduler init err: %s" % e, flush=True)

    # 包装 Handler，在首次请求时延迟初始化
    class SafeHandler(Handler):
        def do_GET(self):
            try:
                _lazy_init()
            except Exception as e:
                print("[warn] lazy_init failed: %s" % e, flush=True)
            Handler.do_GET(self)

        def do_POST(self):
            try:
                _lazy_init()
            except Exception as e:
                print("[warn] lazy_init failed: %s" % e, flush=True)
            Handler.do_POST(self)

    http.server.ThreadingHTTPServer.daemon_threads = True
    http.server.ThreadingHTTPServer.request_queue_size = 64
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), SafeHandler)
    server.socket.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
    server.daemon_threads = True
    print("Server Running on port %d (Ctrl+C停止)" % PORT, flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped", flush=True)
    except Exception as e:
        print("[fatal] %s" % e, flush=True)
    finally:
        try:
            _, _stop = _get_scheduler_funcs()
            if _stop:
                try:
                    _stop()
                except:
                    pass
        except:
            pass
        try:
            server.shutdown()
        except:
            pass
