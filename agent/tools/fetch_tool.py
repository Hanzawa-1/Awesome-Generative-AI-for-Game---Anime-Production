"""Generic URL fetch tool, SSRF-guarded and size-capped, for verifying/enriching a page."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ._common import http_get

MAX_HTML_CHARS = 500_000
MAX_EXCERPT = 4_000

SCHEMA = {
    "name": "fetch_url",
    "description": "Fetch a single http(s) page and return its final_url, status, title, og_image, and a "
                   "short text excerpt. Use to confirm a project/repo page is real and gather details.",
    "parameters": {
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    },
}


def _is_safe(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception:
        return False
    if p.scheme not in ("http", "https") or not p.hostname:
        return False
    try:
        for *_, sockaddr in socket.getaddrinfo(p.hostname, None):
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
    except Exception:
        return False
    return True


def fetch(url: str, **_) -> dict:
    if not _is_safe(url):
        return {"error": "blocked or unresolvable url"}
    try:
        r = http_get(url)
    except Exception as e:  # noqa: BLE001
        return {"error": f"fetch failed: {e}"[:200]}

    ctype = r.headers.get("Content-Type", "")
    result = {"final_url": r.url, "status": r.status_code}
    if "html" not in ctype:
        result["content_type"] = ctype
        return result
    try:
        soup = BeautifulSoup(r.text[:MAX_HTML_CHARS], "html.parser")
        if soup.title:
            result["title"] = soup.title.get_text(strip=True)
        og = soup.find("meta", attrs={"property": "og:image"})
        if og and og.get("content"):
            result["og_image"] = og["content"]
        result["text_excerpt"] = " ".join(soup.get_text(" ").split())[:MAX_EXCERPT]
    except Exception as e:  # noqa: BLE001
        result["parse_error"] = str(e)[:120]
    return result
