"""Load/save the YAML entry database with stable ordering for minimal git diffs."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from agent.schema import Entry

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRIES_FILE = "entries.yml"      # kind == "oss"
SERVICES_FILE = "services.yml"    # kind == "proprietary"


def data_dir(override: str | os.PathLike | None = None) -> Path:
    return Path(override or os.environ.get("DATA_DIR") or (REPO_ROOT / "data"))


def _sort_key(e: Entry):
    # Deterministic; newest-first within a task. None year sorts last.
    return (e.area, e.task, e.kind, -(e.year or 0), e.id)


def load_file(path: Path) -> list[Entry]:
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [Entry.model_validate(r) for r in (raw.get("entries") or [])]


def load_all(override: str | os.PathLike | None = None) -> list[Entry]:
    d = data_dir(override)
    return load_file(d / ENTRIES_FILE) + load_file(d / SERVICES_FILE)


def _record(e: Entry) -> dict:
    d = e.model_dump(mode="json", exclude_none=True)
    # Drop empty lists (authors/tags) for tidier diffs.
    return {k: v for k, v in d.items() if not (isinstance(v, list) and not v)}


def _dump(entries: list[Entry], path: Path) -> None:
    ordered = sorted(entries, key=_sort_key)
    payload = {"entries": [_record(e) for e in ordered]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=1000),
        encoding="utf-8",
    )


def save_split(entries: list[Entry], override: str | os.PathLike | None = None) -> None:
    """Partition by kind and write entries.yml (oss) + services.yml (proprietary)."""
    d = data_dir(override)
    _dump([e for e in entries if e.kind == "oss"], d / ENTRIES_FILE)
    _dump([e for e in entries if e.kind == "proprietary"], d / SERVICES_FILE)
