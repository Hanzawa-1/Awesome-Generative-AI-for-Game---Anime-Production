"""GitHub repository search (uses GITHUB_TOKEN when present for higher rate limits)."""

from __future__ import annotations

import os

from ._common import clamp, http_get

SCHEMA = {
    "name": "search_github",
    "description": "Search GitHub repositories. Use query qualifiers like 'topic:text-to-3d "
                   "stars:>200 pushed:>2025-06-01'. Returns repo (owner/name), url, stars, "
                   "description, topics, pushed_at.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "GitHub search query with qualifiers."},
            "sort": {"type": "string", "enum": ["stars", "updated", "forks"], "description": "default stars"},
            "limit": {"type": "integer", "description": "1-20 (default 15)."},
        },
        "required": ["query"],
    },
}


def search(query: str, sort: str = "stars", limit: int = 15, **_) -> list[dict] | dict:
    n = clamp(limit, 1, 20, 15)
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if sort not in ("stars", "updated", "forks"):
        sort = "stars"
    try:
        r = http_get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": sort, "order": "desc", "per_page": n},
            headers=headers,
        )
        if r.status_code != 200:
            return {"error": f"github search status {r.status_code}: {r.json().get('message', '')[:120]}"}
        items = r.json().get("items", [])
        return [
            {
                "repo": it["full_name"],
                "url": it["html_url"],
                "stars": it.get("stargazers_count"),
                "description": it.get("description"),
                "topics": (it.get("topics") or [])[:8],
                "pushed_at": it.get("pushed_at"),
            }
            for it in items
        ]
    except Exception as e:  # noqa: BLE001
        return {"error": f"github search failed: {e}"[:300]}
