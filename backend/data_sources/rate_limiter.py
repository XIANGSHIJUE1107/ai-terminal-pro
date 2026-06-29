# -*- coding: utf-8 -*-
"""东财限流防封 —— 内置请求间隔 + 随机延迟 + 熔断保护"""

from __future__ import annotations

import random
import threading
import time
from collections import defaultdict
from datetime import datetime


class RateLimiter:
    """多域名限流器，东财系域名内置最小间隔"""

    EASTMONEY_DOMAINS = {
        "push2.eastmoney.com": 0.35,
        "push2his.eastmoney.com": 0.35,
        "data.eastmoney.com": 0.5,
        "datacenter.eastmoney.com": 0.5,
        "reportapi.eastmoney.com": 0.6,
        "emweb.securities.eastmoney.com": 0.5,
        "searchadapter.eastmoney.com": 0.4,
        "quote.eastmoney.com": 0.35,
        "pdf.dfcfw.com": 0.6,
        "np-anotice-stock.eastmoney.com": 0.5,
    }

    CIRCUIT_BREAKER_THRESHOLD = 5  # 连续失败次数阈值
    CIRCUIT_BREAKER_COOLDOWN = 60  # 熔断冷却时间（秒）

    def __init__(self):
        self._lock = threading.Lock()
        self._last_request: dict[str, float] = {}
        self._failure_count: dict[str, int] = defaultdict(int)
        self._circuit_open_until: dict[str, float] = {}

    def _extract_domain(self, url: str) -> str:
        from urllib.parse import urlparse
        return urlparse(url).hostname or ""

    def _min_interval(self, domain: str) -> float:
        return self.EASTMONEY_DOMAINS.get(domain, 0.1)

    def is_circuit_open(self, url: str) -> bool:
        domain = self._extract_domain(url)
        with self._lock:
            until = self._circuit_open_until.get(domain, 0)
            if until and time.time() < until:
                return True
        return False

    def record_failure(self, url: str):
        domain = self._extract_domain(url)
        with self._lock:
            self._failure_count[domain] += 1
            if self._failure_count[domain] >= self.CIRCUIT_BREAKER_THRESHOLD:
                self._circuit_open_until[domain] = time.time() + self.CIRCUIT_BREAKER_COOLDOWN

    def record_success(self, url: str):
        domain = self._extract_domain(url)
        with self._lock:
            self._failure_count[domain] = 0

    def wait(self, url: str):
        domain = self._extract_domain(url)
        min_interval = self._min_interval(domain)
        jitter = random.uniform(0, min_interval * 0.5)
        wait_time = min_interval + jitter

        with self._lock:
            last = self._last_request.get(domain, 0)
            elapsed = time.time() - last
            if elapsed < wait_time:
                time.sleep(wait_time - elapsed)
            self._last_request[domain] = time.time()

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "failures": dict(self._failure_count),
                "circuits": {k: datetime.fromtimestamp(v).strftime("%H:%M:%S") for k, v in self._circuit_open_until.items() if v > time.time()},
            }


rate_limiter = RateLimiter()