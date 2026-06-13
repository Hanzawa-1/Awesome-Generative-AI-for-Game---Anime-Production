"""Hugging Face tools: trending daily papers + model search (keyless; optional HF_TOKEN)."""

from __future__ import annotations

import os

from ._common import clamp, http_get

DAILY_SCHEMA = {
    "name": "hf_daily_papers",
    "description": "Hugging Face trending/daily papers. Returns title, arxiv_id, summary, upvotes, url. "
                   "Great for spotting recently hyped research.",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "Optional YYYY-MM-DD; omit for the latest."},
        },
    },
}

MODELS_SCHEMA = {
    "name": "hf_search_models",
    "description": "Search Hugging Face models by query, sorted by downloads. Returns model_id, url, "
                   "downloads, likes, tags. Good for finding released OSS model weights.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "description": "1-20 (default 15)."},
        },
        "required": ["query"],
    },
}


def daily_papers(date: str | None = None, **_) -> list[dict] | dict:
    try:
        params = {"date": date} if date else None
        r = http_get("https://huggingface.co/api/daily_papers", params=params)
        if r.status_code != 200:
            return {"error": f"hf daily_papers status {r.status_code}"}
        data = r.json()
        out = []
        for item in data[:30]:
            p = item.get("paper", item)
            pid = p.get("id")
            out.append(
                {
                    "title": p.get("title"),
                    "arxiv_id": pid,
                    "summary": (p.get("summary") or "").replace("\n", " ")[:400],
                    "upvotes": p.get("upvotes"),
                    "url": f"https://huggingface.co/papers/{pid}" if pid else None,
                }
            )
        return out
    except Exception as e:  # noqa: BLE001
        return {"error": f"hf daily_papers failed: {e}"[:300]}


def search_models(query: str, limit: int = 15, **_) -> list[dict] | dict:
    from huggingface_hub import list_models

    n = clamp(limit, 1, 20, 15)
    try:
        models = list_models(
            search=query,
            sort="downloads",
            direction=-1,
            limit=n,
            token=os.environ.get("HF_TOKEN") or None,
        )
        out = []
        for m in models:
            out.append(
                {
                    "model_id": m.id,
                    "url": f"https://huggingface.co/{m.id}",
                    "downloads": getattr(m, "downloads", None),
                    "likes": getattr(m, "likes", None),
                    "tags": (getattr(m, "tags", None) or [])[:10],
                }
            )
        return out
    except Exception as e:  # noqa: BLE001
        return {"error": f"hf model search failed: {e}"[:300]}
