"""paperswithcode.co search (community successor; OFF by default — anti-bot/403 prone)."""

from __future__ import annotations

from ._common import clamp, http_get

SCHEMA = {
    "name": "pwc_co",
    "description": "Search paperswithcode.co (community successor to Papers with Code) for papers "
                   "with code. Best-effort and often rate-limited; may return an error.",
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
        r = http_get("https://paperswithcode.co/api/v1/search", params={"q": query, "items_per_page": n})
        if r.status_code != 200:
            return {"error": f"paperswithcode.co status {r.status_code} (likely anti-bot)"}
        data = r.json()
        results = data.get("results", data if isinstance(data, list) else [])
        out = []
        for it in results[:n]:
            paper = it.get("paper", it)
            out.append(
                {
                    "title": paper.get("title"),
                    "arxiv_id": paper.get("arxiv_id"),
                    "url": paper.get("url_abs") or paper.get("url"),
                    "repo": (it.get("repository") or {}).get("url"),
                }
            )
        return out
    except Exception as e:  # noqa: BLE001
        return {"error": f"paperswithcode.co failed: {e}"[:300]}
