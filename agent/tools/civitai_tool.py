"""Civitai model search (best-effort; great for anime/image OSS checkpoints & LoRAs)."""

from __future__ import annotations

from ._common import clamp, http_get

SCHEMA = {
    "name": "civitai",
    "description": "Search Civitai for open community models (checkpoints, LoRAs) — useful for "
                   "anime/image generation assets. Returns name, url, type, tags. Best-effort.",
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
        r = http_get("https://civitai.com/api/v1/models", params={"query": query, "limit": n})
        if r.status_code != 200:
            return {"error": f"civitai status {r.status_code}"}
        items = r.json().get("items", []) or []
        return [
            {
                "name": it.get("name"),
                "url": f"https://civitai.com/models/{it.get('id')}",
                "type": it.get("type"),
                "tags": (it.get("tags") or [])[:8],
                "nsfw": it.get("nsfw"),
            }
            for it in items
        ]
    except Exception as e:  # noqa: BLE001
        return {"error": f"civitai failed: {e}"[:300]}
