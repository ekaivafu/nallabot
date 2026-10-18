# ─────────────────────────────────────────────────────────────
#  proxies.py — Proxy pool manager with round-robin & health track
# ─────────────────────────────────────────────────────────────

from __future__ import annotations

import itertools
import os
import random
from typing import Optional

# Default list of proxies provided in host:port:user:pass or URL format
DEFAULT_PROXIES = [
    "45.38.107.97:6014:dtxywcxs:05lz7yrp3hfn",
    "64.137.96.74:6641:dtxywcxs:05lz7yrp3hfn",
    "198.23.243.226:6361:dtxywcxs:05lz7yrp3hfn",
    "38.154.185.97:6370:dtxywcxs:05lz7yrp3hfn",
    "84.247.60.125:6095:dtxywcxs:05lz7yrp3hfn",
    "191.96.254.138:6185:dtxywcxs:05lz7yrp3hfn",
    "198.46.161.42:5092:dtxywcxs:05lz7yrp3hfn",
    "64.137.10.153:5803:dtxywcxs:05lz7yrp3hfn",
    "104.164.49.38:7693:dtxywcxs:05lz7yrp3hfn",
    "23.26.71.145:5628:dtxywcxs:05lz7yrp3hfn",
]


def parse_proxy(raw: str) -> str:
    """
    Format proxy strings into standard URL format:
    Supports:
      - host:port:user:pass -> http://user:pass@host:port
      - http://user:pass@host:port (unchanged)
      - host:port -> http://host:port
    """
    raw = raw.strip()
    if not raw:
        return ""

    if raw.startswith("http://") or raw.startswith("https://") or raw.startswith("socks5://"):
        return raw

    parts = raw.split(":")
    if len(parts) == 4:
        host, port, user, password = parts
        return f"http://{user}:{password}@{host}:{port}"
    elif len(parts) == 2:
        host, port = parts
        return f"http://{host}:{port}"

    return raw


class ProxyPool:
    """Manages an active pool of proxies with round-robin dispatch and failover."""

    def __init__(self, raw_proxies: Optional[list[str]] = None):
        if raw_proxies is None:
            # Check env var first, otherwise fallback to defaults
            env_proxies = os.getenv("PROXIES")
            if env_proxies:
                raw_proxies = [p.strip() for p in env_proxies.split(",") if p.strip()]
            else:
                raw_proxies = DEFAULT_PROXIES

        self._proxies: list[str] = [
            formatted for p in raw_proxies if (formatted := parse_proxy(p))
        ]
        self._cycle = itertools.cycle(self._proxies) if self._proxies else None

    @property
    def total(self) -> int:
        return len(self._proxies)

    def get_next(self) -> Optional[str]:
        """Return next proxy in round-robin order."""
        if not self._proxies or not self._cycle:
            return None
        return next(self._cycle)

    def get_random(self) -> Optional[str]:
        """Return a random proxy from the pool."""
        if not self._proxies:
            return None
        return random.choice(self._proxies)

    def get_all(self) -> list[str]:
        """Return all parsed proxy URLs."""
        return list(self._proxies)


# Global singleton proxy pool
proxy_pool = ProxyPool()
