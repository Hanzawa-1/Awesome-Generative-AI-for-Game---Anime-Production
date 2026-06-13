"""Validate the data files against the schema + taxonomy. Exit non-zero on any error.

Used in CI (deploy + update workflows) and locally via ``make validate``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a plain script (python scripts/validate.py) from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.taxonomy import load_taxonomy  # noqa: E402
from pipeline import db  # noqa: E402


def main() -> int:
    errors: list[str] = []

    try:
        tax = load_taxonomy()
    except Exception as e:
        print(f"VALIDATION FAILED loading taxonomy: {e}")
        return 1

    try:
        entries = db.load_all()
    except Exception as e:
        print(f"VALIDATION FAILED loading/validating entries: {e}")
        return 1

    seen_ids: dict[str, str] = {}
    seen_keys: dict[str, str] = {}
    for e in entries:
        if e.id in seen_ids:
            errors.append(f"duplicate id '{e.id}' (titles: {seen_ids[e.id]!r} and {e.title!r})")
        seen_ids[e.id] = e.title
        if e.key in seen_keys:
            errors.append(f"duplicate dedup_key '{e.key}' ({seen_keys[e.key]} and {e.id})")
        seen_keys[e.key] = e.id

    if errors:
        print("VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"OK: {len(entries)} entries valid across {len(tax)} tasks in {len(tax.areas)} areas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
