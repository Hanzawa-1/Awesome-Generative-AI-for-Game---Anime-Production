"""Semantic Scholar paper search (keyless; the Papers-with-Code metadata substitute)."""

from __future__ import annotations

from ._common import clamp, http_get

SCHEMA = {
    "name": "semantic_scholar",
    "description": "Search Semantic Scholar for papers. Returns title, year, authors, arxiv_id/doi, url. "
                   "Authoritative for well-cited papers and resolving arXiv ids.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "description": "1-20 (default 10)."},
        },
        "required": ["query"],
    },
}


def search(query: str, limit: int = 10, **_) -> list[dict] | dict:
    n = clamp(limit, 1, 20, 10)
    try:
        r = http_get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={"query": query, "limit": n, "fields": "title,year,authors,externalIds,url"},
        )
        if r.status_code != 200:
            return {"error": f"semantic scholar status {r.status_code}"}
        out = []
        for p in r.json().get("data", []) or []:
            ext = p.get("externalIds") or {}
            out.append(
                {
                    "title": p.get("title"),
                    "year": p.get("year"),
                    "authors": [a.get("name") for a in (p.get("authors") or [])][:6],
                    "arxiv_id": ext.get("ArXiv"),
                    "doi": ext.get("DOI"),
                    "url": p.get("url"),
                }
            )
        return out
    except Exception as e:  # noqa: BLE001
        return {"error": f"semantic scholar failed: {e}"[:300]}
