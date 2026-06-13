"""Shared helpers for discovery tools."""

from __future__ import annotations

import requests

UA = "Mozilla/5.0 (compatible; awesome-genai-bot/1.0; +https://github.com/)"
DEFAULT_TIMEOUT = 20


def http_get(url: str, *, params=None, headers=None, timeout: int = DEFAULT_TIMEOUT, **kw):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    return requests.get(url, params=params, headers=h, timeout=timeout, **kw)


def clamp(value, lo: int, hi: int, default: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))
