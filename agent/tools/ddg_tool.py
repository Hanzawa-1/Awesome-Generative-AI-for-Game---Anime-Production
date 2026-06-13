"""Web search tool via the ddgs library (successor to duckduckgo-search; keyless)."""

from __future__ import annotations

from ._common import clamp

SCHEMA = {
    "name": "search_web",
    "description": "General web search (DuckDuckGo). Returns title, url, and a snippet. "
                   "Best-effort enrichment; prefer arXiv/HF/GitHub for primary discovery.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "description": "1-10 (default 8)."},
        },
        "required": ["query"],
    },
}


def search(query: str, max_results: int = 8, **_) -> list[dict] | dict:
    from ddgs import DDGS

    n = clamp(max_results, 1, 10, 8)
    try:
        with DDGS() as d:
            results = list(d.text(query, max_results=n))
        return [
            {
                "title": r.get("title"),
                "url": r.get("href") or r.get("url") or r.get("link"),
                "snippet": r.get("body") or r.get("snippet"),
            }
            for r in results
        ]
    except Exception as e:  # noqa: BLE001
        return {"error": f"web search failed: {e}"[:300]}
